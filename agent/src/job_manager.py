# agent/src/job_manager.py

import os
import json
import shutil
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from src.config import settings
from src.logger import get_logger
from src.auth import TokenValidator

logger = get_logger()


class JobManager:
    """Manage HEC-RAS simulation jobs"""

    def __init__(self):
        self.current_job = None
        self.working_dir = Path(settings.WORKING_DIR)
        self.template_dir = Path(settings.MODEL_TEMPLATE_DIR)
        self.mock_mode = settings.MOCK_MODE

    def create_working_directory(self, job_id: str) -> Path:
        """Create working directory for a job"""
        job_dir = self.working_dir / job_id
        try:
            job_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created working directory: {job_dir}")
            return job_dir
        except Exception as e:
            logger.error(f"Failed to create working directory: {e}")
            raise

    def copy_model_template(self, job_dir: Path) -> bool:
        """Copy HEC-RAS model template to working directory"""
        try:
            if not self.template_dir.exists():
                logger.warning(f"Template directory not found: {self.template_dir}")
                self._create_dummy_template(job_dir)
                return True

            for item in self.template_dir.iterdir():
                dest = job_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)

            logger.info(f"Copied template to: {job_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy template: {e}")
            return False

    def _create_dummy_template(self, job_dir: Path):
        """Create dummy template files"""
        dummy_files = ["project.prj", "plan.p01", "geometry.g01", "flow.f01"]
        for filename in dummy_files:
            file_path = job_dir / filename
            file_path.write_text(f"# Dummy HEC-RAS file: {filename}\n")
        logger.info(f"Created dummy template in: {job_dir}")

    def update_inputs(self, job_dir: Path, parameters: Dict[str, Any]) -> bool:
        """Update input files with simulation parameters"""
        try:
            params_file = job_dir / "simulation_params.json"
            params_data = {
                "job_id": parameters.get("job_id", "UNKNOWN"),
                "rainfall": parameters.get("rainfall", 0),
                "rainfall_unit": parameters.get("rainfall_unit", "mm"),
                "duration": parameters.get("duration", 0),
                "duration_unit": parameters.get("duration_unit", "hour"),
                "created_at": datetime.now().isoformat(),
                "simulation_type": "flood_depth"
            }
            params_file.write_text(json.dumps(params_data, indent=2))
            logger.info(f"Updated inputs for job: {job_dir.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to update inputs: {e}")
            return False

    def run_simulation(self, job_dir: Path, job_id: str) -> bool:
        """Run HEC-RAS simulation"""
        try:
            if self.mock_mode:
                logger.info(f"Running MOCK simulation for job: {job_id}")
                delay = settings.MOCK_SIMULATION_DELAY
                for i in range(delay):
                    time.sleep(1)
                    if i % 5 == 0:
                        logger.info(f"Simulation progress: {i+1}/{delay} seconds")

                output_file = job_dir / "output.hdf"
                output_file.write_text(
                    f"# Mock HEC-RAS output for job: {job_id}\n"
                    f"# Simulation completed at: {datetime.now()}\n"
                )
                logger.info(f"Mock simulation completed for job: {job_id}")
                return True
            else:
                logger.info(f"Running REAL HEC-RAS for job: {job_id}")
                # Real HEC-RAS execution (Phase 6)
                return self._run_real_hecras(job_dir, job_id)
        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            return False

    def _run_real_hecras(self, job_dir: Path, job_id: str) -> bool:
        """Run real HEC-RAS (Phase 6)"""
        # Placeholder - sẽ được implement ở Phase 6
        logger.warning("Real HEC-RAS execution not implemented yet")
        return False

    def process_results(self, job_dir: Path, job_id: str) -> Dict[str, Any]:
        """Process simulation results"""
        try:
            logger.info(f"Processing results for job: {job_id}")

            result = {
                "job_id": job_id,
                "result_type": "flood_depth",
                "crs": "EPSG:4326",
                "min_value": 0.0,
                "max_value": 2.83,
                "mock_result": self.mock_mode,
                "result_url": f"/results/{job_id}",
                "storage_key": f"results/{job_id}/flood.tif",
                "metadata": {
                    "resolution": 10,
                    "units": "m",
                    "simulation_type": "rainfall",
                    "processed_at": datetime.now().isoformat()
                }
            }

            result_file = job_dir / "result_metadata.json"
            result_file.write_text(json.dumps(result, indent=2))
            logger.info(f"Results processed for job: {job_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to process results: {e}")
            raise

    def cleanup(self, job_dir: Path):
        """Clean up job directory"""
        try:
            logger.info(f"Cleanup skipped for: {job_dir}")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


class WorkingDirectory:
    """Manage working directory lifecycle"""

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.path = Path(settings.WORKING_DIR) / job_id

    def create(self) -> Path:
        self.path.mkdir(parents=True, exist_ok=True)
        return self.path

    def exists(self) -> bool:
        return self.path.exists()

    def delete(self):
        if self.path.exists():
            shutil.rmtree(self.path)
            logger.info(f"Deleted working directory: {self.path}")