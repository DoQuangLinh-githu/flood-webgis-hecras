# agent/src/agent.py

import os
import sys
import time
import json
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

import requests

from agent.src.config import settings
from agent.src.logger import get_logger
from agent.src.auth import AgentAuthenticator, TokenValidator
from agent.src.job_manager import JobManager, WorkingDirectory

logger = get_logger()


class HECRASAgent:
    """Main HEC-RAS Agent"""

    def __init__(self):
        self.running = False
        self.job_manager = JobManager()
        self.current_job = None
        self.job_polling = True

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.job_polling = False

    def _get_auth_headers(self) -> dict:
        """Get authentication headers for API requests"""
        return AgentAuthenticator.get_headers()

    def _send_heartbeat(self) -> bool:
        """Send heartbeat to backend"""
        try:
            headers = self._get_auth_headers()
            headers["Content-Type"] = "application/json"

            data = {
                "agent_name": settings.AGENT_NAME,
                "machine_name": settings.AGENT_MACHINE_NAME,
                "status": "ONLINE" if self.running else "OFFLINE",
                "version": settings.AGENT_VERSION,
                "current_job": self.current_job,
                "timestamp": datetime.now().isoformat()
            }

            response = requests.post(
                f"{settings.BACKEND_URL}/api/agents/heartbeat",
                json=data,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                logger.debug("Heartbeat sent successfully")
                return True
            else:
                logger.warning(f"Heartbeat failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            return False

    def _get_pending_job(self) -> Optional[Dict[str, Any]]:
        """Get a pending job from backend"""
        try:
            headers = self._get_auth_headers()
            headers["Content-Type"] = "application/json"

            response = requests.get(
                f"{settings.BACKEND_URL}/api/jobs/pending",
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                job = response.json()
                if job:
                    logger.info(f"Received job: {job.get('job_id')}")
                    return job
                else:
                    logger.debug("No pending jobs")
                    return None
            elif response.status_code == 204:
                logger.debug("No pending jobs")
                return None
            else:
                logger.warning(f"Failed to get pending job: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting pending job: {e}")
            return None

    def _update_job_status(self, job_id: str, status: str, error: Optional[str] = None) -> bool:
        """Update job status in backend"""
        try:
            headers = self._get_auth_headers()
            headers["Content-Type"] = "application/json"

            data = {
                "status": status,
                "error_message": error,
                "agent_name": settings.AGENT_NAME,
                "timestamp": datetime.now().isoformat()
            }

            response = requests.put(
                f"{settings.BACKEND_URL}/api/jobs/{job_id}/status",
                json=data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                logger.info(f"Job {job_id} status updated to {status}")
                return True
            else:
                logger.error(f"Failed to update job status: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
            return False

    def _complete_job(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Mark job as completed with results"""
        try:
            headers = self._get_auth_headers()
            headers["Content-Type"] = "application/json"

            data = {
                "status": "COMPLETED",
                "result": result,
                "agent_name": settings.AGENT_NAME,
                "timestamp": datetime.now().isoformat()
            }

            response = requests.put(
                f"{settings.BACKEND_URL}/api/jobs/{job_id}/complete",
                json=data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                logger.info(f"Job {job_id} completed successfully")
                return True
            else:
                logger.error(f"Failed to complete job: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error completing job: {e}")
            return False

    def _process_job(self, job: Dict[str, Any]) -> bool:
        """Process a single job"""
        job_id = job.get("job_id")
        parameters = job.get("parameters", {})

        if not job_id:
            logger.error("Job missing job_id")
            return False

        logger.info(f"Processing job: {job_id}")
        self.current_job = job_id

        try:
            # 1. Update status to RUNNING
            if not self._update_job_status(job_id, "RUNNING"):
                logger.error(f"Failed to update job {job_id} to RUNNING")
                return False

            # 2. Create working directory
            working_dir = WorkingDirectory(job_id)
            job_dir = working_dir.create()
            logger.info(f"Created working directory: {job_dir}")

            # 3. Copy model template
            if not self.job_manager.copy_model_template(job_dir):
                raise Exception("Failed to copy model template")

            # 4. Update inputs
            job_params = {
                "job_id": job_id,
                **parameters
            }
            if not self.job_manager.update_inputs(job_dir, job_params):
                raise Exception("Failed to update inputs")

            # 5. Update status to PROCESSING (simulation running)
            if not self._update_job_status(job_id, "PROCESSING"):
                logger.error(f"Failed to update job {job_id} to PROCESSING")
                return False

            # 6. Run simulation
            if not self.job_manager.run_simulation(job_dir, job_id):
                raise Exception("Simulation failed")

            # 7. Process results
            result = self.job_manager.process_results(job_dir, job_id)

            # 8. Complete job
            if not self._complete_job(job_id, result):
                raise Exception("Failed to complete job")

            logger.info(f"Job {job_id} processed successfully")
            return True

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Job {job_id} failed: {error_msg}")

            # Update status to FAILED
            self._update_job_status(job_id, "FAILED", error_msg)
            return False

        finally:
            self.current_job = None

    def _run_polling_cycle(self):
        """Run one polling cycle"""
        try:
            # Get pending job
            job = self._get_pending_job()

            if job:
                # Process job
                self._process_job(job)
            else:
                # No job, wait
                time.sleep(settings.POLL_INTERVAL)

        except Exception as e:
            logger.error(f"Polling cycle error: {e}")
            time.sleep(settings.POLL_INTERVAL)

    def run(self):
        """Main agent loop"""
        logger.info(f"Starting HEC-RAS Agent v{settings.AGENT_VERSION}")
        logger.info(f"Agent Name: {settings.AGENT_NAME}")
        logger.info(f"Machine: {settings.AGENT_MACHINE_NAME}")
        logger.info(f"Backend URL: {settings.BACKEND_URL}")
        logger.info(f"Working Directory: {settings.WORKING_DIR}")
        logger.info(f"Mock Mode: {settings.MOCK_MODE}")

        self.running = True

        # Send initial heartbeat
        self._send_heartbeat()

        while self.running:
            try:
                # Send heartbeat periodically
                if self._send_heartbeat():
                    # Heartbeat successful, poll for jobs
                    self._run_polling_cycle()
                else:
                    # Heartbeat failed, wait and retry
                    logger.warning("Heartbeat failed, waiting...")
                    time.sleep(settings.HEARTBEAT_INTERVAL)

            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                time.sleep(settings.POLL_INTERVAL)

        logger.info("Agent stopped")

    def stop(self):
        """Stop the agent"""
        self.running = False
        logger.info("Agent stopping...")


def main():
    """Entry point for the agent"""
    agent = HECRASAgent()
    agent.run()


if __name__ == "__main__":
    main()