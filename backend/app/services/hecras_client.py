# backend/app/services/hecras_client.py

import os
import requests
import logging
from typing import Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class HECRASClient:
    """Client để gọi HEC-RAS API Service"""

    @staticmethod
    def _get_api_url() -> str:
        """Lấy URL từ biến môi trường hoặc config"""
        return os.getenv("HECRAS_API_URL", "http://localhost:8000")

    @staticmethod
    def health_check() -> bool:
        """Kiểm tra HEC-RAS API Service"""
        try:
            response = requests.get(f"{HECRASClient._get_api_url()}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"HEC-RAS API health check failed: {e}")
            return False

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """Lấy thông tin HEC-RAS model"""
        try:
            response = requests.get(f"{HECRASClient._get_api_url()}/info", timeout=10)
            if response.status_code == 200:
                return response.json()
            return {"error": f"API error: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def run_simulation(
        scenario_name: str,
        rainfall: float,
        rainfall_unit: str,
        duration: float,
        duration_unit: str,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Gửi yêu cầu chạy simulation đến HEC-RAS API"""
        try:
            data = {
                "scenario_name": scenario_name,
                "rainfall": rainfall,
                "rainfall_unit": rainfall_unit,
                "duration": duration,
                "duration_unit": duration_unit,
                "job_id": job_id
            }

            logger.info(f"Sending to HEC-RAS API: {data}")

            response = requests.post(
                f"{HECRASClient._get_api_url()}/run",
                json=data,
                timeout=3600  # 1 giờ timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "failed",
                    "error": f"API error: {response.status_code} - {response.text}"
                }

        except requests.exceptions.Timeout:
            logger.error("HEC-RAS API timeout")
            return {"status": "failed", "error": "HEC-RAS execution timeout"}
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to HEC-RAS API")
            return {"status": "failed", "error": "Cannot connect to HEC-RAS service"}
        except Exception as e:
            logger.error(f"HEC-RAS API error: {e}")
            return {"status": "failed", "error": str(e)}

    @staticmethod
    def get_results(job_id: str) -> Dict[str, Any]:
        """Lấy kết quả từ HEC-RAS API"""
        try:
            response = requests.get(
                f"{HECRASClient._get_api_url()}/results/{job_id}",
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return {"status": "failed", "error": f"API error: {response.status_code}"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    @staticmethod
    def download_result(job_id: str, filename: str) -> Optional[bytes]:
        """Tải file kết quả"""
        try:
            response = requests.get(
                f"{HECRASClient._get_api_url()}/results/{job_id}/download/{filename}",
                timeout=60
            )
            if response.status_code == 200:
                return response.content
            return None
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None