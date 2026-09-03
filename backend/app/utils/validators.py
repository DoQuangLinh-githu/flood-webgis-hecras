# backend/app/utils/validators.py

from typing import Any, Dict
from datetime import datetime


def validate_simulation_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate simulation parameters"""
    required_fields = ["rainfall", "rainfall_unit", "duration", "duration_unit"]
    
    for field in required_fields:
        if field not in params:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate rainfall
    rainfall = params["rainfall"]
    if not isinstance(rainfall, (int, float)):
        raise ValueError("Rainfall must be a number")
    if rainfall <= 0 or rainfall > 500:
        raise ValueError("Rainfall must be between 0 and 500")
    
    # Validate duration
    duration = params["duration"]
    if not isinstance(duration, (int, float)):
        raise ValueError("Duration must be a number")
    if duration <= 0 or duration > 72:
        raise ValueError("Duration must be between 0 and 72 hours")
    
    # Validate units
    valid_rainfall_units = ["mm", "cm", "inch"]
    if params["rainfall_unit"].lower() not in valid_rainfall_units:
        raise ValueError(f"Rainfall unit must be one of: {valid_rainfall_units}")
    
    valid_duration_units = ["minute", "hour", "day"]
    if params["duration_unit"].lower() not in valid_duration_units:
        raise ValueError(f"Duration unit must be one of: {valid_duration_units}")
    
    return params


def validate_job_id(job_id: str) -> bool:
    """Validate job ID format"""
    import re
    pattern = r"^JOB-\d{3}$"
    return bool(re.match(pattern, job_id))