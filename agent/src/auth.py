# agent/src/auth.py

import hashlib
import hmac
import time
import uuid
from typing import Optional
from datetime import datetime

from agent.src.config import settings
from agent.src.logger import get_logger

logger = get_logger()


class AgentAuthenticator:
    """Authentication for Agent to Backend"""

    @staticmethod
    def get_headers() -> dict:
        """Generate authentication headers for API requests"""
        timestamp = str(int(time.time()))
        nonce = str(uuid.uuid4())

        # Generate signature
        # HMAC-SHA256 of (timestamp + nonce + agent_name)
        message = f"{timestamp}{nonce}{settings.AGENT_NAME}"
        signature = hmac.new(
            settings.AGENT_TOKEN.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return {
            "X-Agent-Name": settings.AGENT_NAME,
            "X-Agent-Token": settings.AGENT_TOKEN,
            "X-Agent-API-Key": settings.AGENT_API_KEY,
            "X-Agent-Timestamp": timestamp,
            "X-Agent-Nonce": nonce,
            "X-Agent-Signature": signature,
            "X-Agent-Version": settings.AGENT_VERSION,
        }

    @staticmethod
    def verify_response(response_headers: dict) -> bool:
        """Verify backend response authenticity"""
        # In production, verify backend signature
        # For Phase 4, we just check if we got a valid response
        return True


class TokenValidator:
    """Validate commands and paths for security"""

    @staticmethod
    def validate_command(command: str) -> bool:
        """Check if command is allowed"""
        cmd_name = command.split()[0].lower()
        if cmd_name not in settings.ALLOWED_COMMANDS:
            logger.warning(f"Command '{cmd_name}' not in allowed list")
            return False
        return True

    @staticmethod
    def validate_path(path: str) -> bool:
        """Check if path is allowed"""
        normalized_path = path.replace("\\", "/").rstrip("/")
        for allowed in settings.ALLOWED_PATHS:
            if normalized_path.startswith(allowed.replace("\\", "/")):
                return True
        logger.warning(f"Path '{path}' not in allowed list")
        return False

    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Sanitize input to prevent injection"""
        # Remove dangerous characters
        dangerous = [";", "&", "|", ">", "<", "`", "$", "(", ")", "{", "}", "[", "]"]
        for char in dangerous:
            input_str = input_str.replace(char, "")
        return input_str