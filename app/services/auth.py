"""
Authentication service for Saby CRM API.
Handles token acquisition, validation, and refresh.
"""
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import httpx
from pydantic import BaseModel

from config.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class SabyToken(BaseModel):
    """Saby CRM access token model."""

    access_token: str
    sid: str
    expires_at: Optional[datetime] = None
    token_type: str = "Bearer"

    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class AuthCredentials(BaseModel):
    """Saby CRM authentication credentials."""

    app_client_id: str
    app_secret: str
    secret_key: str


class SabyAuthService:
    """Service for handling Saby CRM authentication."""

    def __init__(self):
        """Initialize the auth service."""
        self.credentials = AuthCredentials(
            app_client_id=settings.saby.app_client_id,
            app_secret=settings.saby.app_secret,
            secret_key=settings.saby.secret_key
        )
        self.base_url = settings.saby.auth_url
        self._token: Optional[SabyToken] = None

    async def get_access_token(self) -> SabyToken:
        """
        Get access token from Saby CRM.

        Returns:
            SabyToken: Access token with metadata

        Raises:
            SabyAuthError: If authentication fails
        """
        logger.info("Requesting access token from Saby CRM")

        try:
            async with httpx.AsyncClient(timeout=settings.saby.request_timeout) as client:
                response = await client.post(
                    self.base_url,
                    json={
                        "app_client_id": self.credentials.app_client_id,
                        "app_secret": self.credentials.app_secret,
                        "secret_key": self.credentials.secret_key
                    },
                    headers={
                        "Content-Type": "application/json; charset=utf-8",
                        "User-Agent": "SBIS-API-FastAPI/1.0.0"
                    }
                )

                if response.status_code != 200:
                    logger.error(f"Authentication failed with status {response.status_code}: {response.text}")
                    raise SabyAuthError(f"Authentication failed: {response.status_code}")

                data = response.json()

                if "token" not in data:
                    logger.error(f"Invalid response format: {data}")
                    raise SabyAuthError("Invalid response format from Saby CRM")

                # Create token with expiration (tokens are typically valid for 24 hours)
                expires_at = datetime.utcnow() + timedelta(hours=24)

                token = SabyToken(
                    access_token=data["token"],
                    sid=data.get("sid", ""),
                    expires_at=expires_at
                )

                self._token = token
                logger.info("Successfully obtained access token")

                return token

        except httpx.RequestError as e:
            logger.error(f"Request error during authentication: {e}")
            raise SabyAuthError(f"Request error: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise SabyAuthError(f"Invalid JSON response: {e}")

    async def ensure_valid_token(self) -> SabyToken:
        """
        Ensure we have a valid access token.

        Returns:
            SabyToken: Valid access token
        """
        if not self._token or self._token.is_expired():
            logger.info("Token expired or missing, requesting new token")
            return await self.get_access_token()

        return self._token

    def get_auth_headers(self, token: Optional[SabyToken] = None) -> Dict[str, str]:
        """
        Get authentication headers for API requests.

        Args:
            token: Token to use (if None, uses cached token)

        Returns:
            Dict with authentication headers
        """
        if token is None:
            token = self._token

        if not token:
            raise SabyAuthError("No valid token available")

        return {
            "X-SBISAccessToken": token.access_token,
            "Content-Type": "application/json-rpc; charset=utf-8",
            "User-Agent": "SBIS-API-FastAPI/1.0.0"
        }

    async def logout(self) -> bool:
        """
        Logout from Saby CRM (invalidate token).

        Returns:
            bool: True if logout successful
        """
        if not self._token:
            logger.warning("No active token to logout")
            return True

        try:
            async with httpx.AsyncClient(timeout=settings.saby.request_timeout) as client:
                response = await client.post(
                    self.base_url,
                    json={
                        "event": "exit",
                        "token": self._token.access_token
                    },
                    headers={
                        "Content-Type": "application/json; charset=utf-8",
                        "User-Agent": "SBIS-API-FastAPI/1.0.0"
                    }
                )

                if response.status_code == 200:
                    logger.info("Successfully logged out from Saby CRM")
                    self._token = None
                    return True
                else:
                    logger.warning(f"Logout request failed with status {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return False


class SabyAuthError(Exception):
    """Exception raised for Saby CRM authentication errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


# Global auth service instance
auth_service = SabyAuthService()