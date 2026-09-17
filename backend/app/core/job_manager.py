# backend/app/core/job_manager.py

import uuid
from datetime import datetime


class JobManager:
    """Quản lý job ID và trạng thái."""

    @staticmethod
    def generate_job_id() -> str:
        """Tạo job ID dạng JOB-YYYYMMDD-HHMMSS-XXXXXX."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        suffix = uuid.uuid4().hex[:6].upper()
        return f"JOB-{timestamp}-{suffix}"

    @staticmethod
    def is_terminal_status(status: str) -> bool:
        """Kiểm tra status đã kết thúc chưa."""
        return status in ("COMPLETED", "FAILED", "CANCELLED")