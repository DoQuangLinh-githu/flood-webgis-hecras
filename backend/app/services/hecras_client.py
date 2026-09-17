# backend/app/services/hecras_client.py

import logging
from typing import Dict, Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class HECRASClient:
    """
    Client gọi HEC-RAS API Service (v3.0.2 trên Máy 1).

    HEC-RAS API endpoints:
      - GET  /health
      - GET  /
      - POST /run                -> trả về ngay {status: queued, job_id}
      - GET  /jobs/{id}          -> trạng thái job
      - GET  /results/{id}       -> danh sách file kết quả
      - GET  /results/{id}/download/{filename}
      - POST /extract/{id}       -> extract HDF -> GeoJSON
      - GET  /geojson/{file}     -> serve file GeoJSON (static)
    """

    TIMEOUT_SHORT = 10.0
    TIMEOUT_MEDIUM = 30.0
    TIMEOUT_LONG = 60.0
    TIMEOUT_EXTRACT = 180.0

    @staticmethod
    def _base_url() -> str:
        return settings.HECRAS_API_URL.rstrip("/")

    # --------------------------------------------------------
    # HEALTH
    # --------------------------------------------------------

    @staticmethod
    def health_check() -> bool:
        """Kiểm tra HEC-RAS API Service có sống không."""
        try:
            with httpx.Client(timeout=HECRASClient.TIMEOUT_SHORT) as client:
                r = client.get(f"{HECRASClient._base_url()}/health")
                return r.status_code == 200
        except Exception as e:
            logger.error(f"HEC-RAS health check failed: {e}")
            return False

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """Lấy thông tin HEC-RAS service (dùng GET /)."""
        try:
            with httpx.Client(timeout=HECRASClient.TIMEOUT_SHORT) as client:
                r = client.get(f"{HECRASClient._base_url()}/")
                if r.status_code == 200:
                    return r.json()
                return {"error": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    # --------------------------------------------------------
    # RUN SIMULATION
    # --------------------------------------------------------

    @staticmethod
    def run_simulation(
        scenario_name: str,
        rainfall: float,
        rainfall_unit: str,
        duration: float,
        duration_unit: str,
        job_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Gửi yêu cầu chạy simulation.

        HEC-RAS API v3.0.2 trả về NGAY (không chờ job xong):
          {"status": "queued", "job_id": "JOB-...", "queue_position": N}

        Do đó timeout chỉ cần 30s.
        """
        payload = {
            "scenario_name": scenario_name,
            "rainfall": rainfall,
            "rainfall_unit": rainfall_unit,
            "duration": duration,
            "duration_unit": duration_unit,
        }
        if job_id:
            payload["job_id"] = job_id

        try:
            with httpx.Client(timeout=HECRASClient.TIMEOUT_MEDIUM) as client:
                r = client.post(
                    f"{HECRASClient._base_url()}/run",
                    json=payload,
                )
                if r.status_code == 200:
                    return r.json()
                return {
                    "status": "failed",
                    "error": f"HTTP {r.status_code}: {r.text[:500]}",
                }
        except httpx.TimeoutException:
            return {"status": "failed", "error": "HEC-RAS API timeout"}
        except httpx.ConnectError:
            return {"status": "failed", "error": "Cannot connect to HEC-RAS API"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    # --------------------------------------------------------
    # JOB STATUS
    # --------------------------------------------------------

    @staticmethod
    def get_job_status(hecras_job_id: str) -> Dict[str, Any]:
        """
        Lấy trạng thái job từ HEC-RAS API.

        Trả về ví dụ:
          {
            "job_id": "JOB-xxx",
            "status": "running" | "completed" | "failed" | "queued",
            "message": "...",
            "result_files": [...],
            "result_directory": "...",
            ...
          }
        """
        try:
            with httpx.Client(timeout=HECRASClient.TIMEOUT_SHORT) as client:
                r = client.get(
                    f"{HECRASClient._base_url()}/jobs/{hecras_job_id}"
                )
                if r.status_code == 200:
                    return r.json()
                if r.status_code == 404:
                    return {"status": "not_found"}
                return {
                    "status": "error",
                    "error": f"HTTP {r.status_code}",
                }
        except Exception as e:
            logger.error(f"get_job_status error: {e}")
            return {"status": "error", "error": str(e)}

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    @staticmethod
    def get_results(hecras_job_id: str) -> Dict[str, Any]:
        """Lấy danh sách file kết quả."""
        try:
            with httpx.Client(timeout=HECRASClient.TIMEOUT_MEDIUM) as client:
                r = client.get(
                    f"{HECRASClient._base_url()}/results/{hecras_job_id}"
                )
                if r.status_code == 200:
                    return r.json()
                return {
                    "status": "failed",
                    "error": f"HTTP {r.status_code}",
                }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    @staticmethod
    def download_result(
        hecras_job_id: str, filename: str
    ) -> Optional[bytes]:
        """Tải nội dung một file kết quả."""
        try:
            with httpx.Client(timeout=HECRASClient.TIMEOUT_LONG) as client:
                r = client.get(
                    f"{HECRASClient._base_url()}/results/{hecras_job_id}/download/{filename}"
                )
                if r.status_code == 200:
                    return r.content
                return None
        except Exception as e:
            logger.error(f"download_result error: {e}")
            return None

    # --------------------------------------------------------
    # EXTRACT HDF -> GEOJSON
    # --------------------------------------------------------

    @staticmethod
    def extract_geojson(hecras_job_id: str) -> Dict[str, Any]:
        """
        Gọi HEC-RAS API để extract HDF -> GeoJSON.

        Returns:
            {
              "status": "completed",
              "geojson_path": "...",
              "size_bytes": ...,
              "elapsed_seconds": ...
            }
        """
        try:
            with httpx.Client(timeout=HECRASClient.TIMEOUT_EXTRACT) as client:
                r = client.post(
                    f"{HECRASClient._base_url()}/extract/{hecras_job_id}"
                )
                if r.status_code == 200:
                    return r.json()
                return {
                    "status": "failed",
                    "error": f"HTTP {r.status_code}: {r.text[:500]}",
                }
        except httpx.TimeoutException:
            return {"status": "failed", "error": "Extract timeout"}
        except Exception as e:
            logger.error(f"extract_geojson error: {e}")
            return {"status": "failed", "error": str(e)}

    # --------------------------------------------------------
    # DOWNLOAD GEOJSON
    # --------------------------------------------------------

    @staticmethod
    def download_geojson(hecras_job_id: str) -> Optional[bytes]:
        """
        Tải file GeoJSON từ HEC-RAS API qua static mount.

        URL: {HECRAS_API_URL}/geojson/{job_id}.geojson

        Yêu cầu HEC-RAS API phải mount thư mục geojson:
            app.mount("/geojson", StaticFiles(directory=CONFIG["geojson_dir"]))
        """
        try:
            url = f"{HECRASClient._base_url()}/geojson/{hecras_job_id}.geojson"
            with httpx.Client(timeout=HECRASClient.TIMEOUT_LONG) as client:
                r = client.get(url)
                if r.status_code == 200:
                    return r.content
                logger.warning(f"download_geojson: HTTP {r.status_code} for {url}")
                return None
        except Exception as e:
            logger.error(f"download_geojson error: {e}")
            return None