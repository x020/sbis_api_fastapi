"""
Saby CRM API client for integration with SBIS services.
Handles all API interactions with Saby CRM.
"""
import json
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel

from config.config import get_settings
from app.services.auth import auth_service, SabyAuthError
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class SabyApiError(Exception):
    """Exception raised for Saby API errors."""

    def __init__(self, message: str, code: Optional[int] = None, details: Optional[str] = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)


class ContactPerson(BaseModel):
    """Contact person data model."""

    name: str
    phone: Optional[str] = None
    email: Optional[str] = None


class Client(BaseModel):
    """Client data model."""

    face_id: Optional[str] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    name: str
    client_type: List[int] = [0]  # 0 - legal entity, 1 - individual entrepreneur, 2 - natural person


class DealNomenclature(BaseModel):
    """Deal nomenclature item model."""

    code: str
    price: float
    count: int


class CreateDealRequest(BaseModel):
    """Request model for creating a deal."""

    regulation: int
    responsible: Optional[str] = None
    client: Optional[Client] = None
    contact_person: Optional[ContactPerson] = None
    note: Optional[str] = None
    source: Optional[int] = None
    notify: bool = False
    use_rules: bool = True
    user_conditions: Optional[Dict[str, str]] = None
    nomenclatures: Optional[List[DealNomenclature]] = None
    additional_fields: Optional[Dict[str, Any]] = None


class DealResponse(BaseModel):
    """Response model for deal operations."""

    document_id: int
    uuid: str
    regulation: int
    client: Optional[Dict[str, Any]] = None
    contact_person: Optional[Dict[str, Any]] = None
    note: Optional[str] = None
    state: Optional[str] = None
    source: Optional[int] = None


class SabyCRMClient:
    """Client for Saby CRM API interactions."""

    def __init__(self):
        """Initialize the Saby CRM client."""
        self.base_url = settings.saby.api_url
        self.timeout = settings.saby.request_timeout

    async def _make_request(
        self,
        method: str,
        params: Dict[str, Any],
        request_id: int = 0
    ) -> Dict[str, Any]:
        """
        Make a JSON-RPC request to Saby API.

        Args:
            method: API method name
            params: Request parameters
            request_id: Request ID for JSON-RPC

        Returns:
            API response

        Raises:
            SabyApiError: If API request fails
        """
        # Ensure we have a valid token
        token = await auth_service.ensure_valid_token()

        # Prepare JSON-RPC request
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "protocol": 6,
            "id": request_id
        }

        headers = auth_service.get_auth_headers(token)

        logger.info(f"Making API request: {method}", extra={"method": method, "params": params})

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=headers
                )

                if response.status_code != 200:
                    logger.error(f"API request failed with status {response.status_code}: {response.text}")
                    raise SabyApiError(f"API request failed: {response.status_code}", code=response.status_code)

                result = response.json()

                # Check for JSON-RPC error
                if "error" in result:
                    error = result["error"]
                    logger.error(f"API returned error: {error}")
                    raise SabyApiError(
                        error.get("message", "Unknown API error"),
                        code=error.get("code"),
                        details=str(error.get("data"))
                    )

                logger.info(f"API request successful: {method}")
                return result.get("result", {})

        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise SabyApiError(f"Request error: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise SabyApiError(f"Invalid JSON response: {e}")

    async def get_crm_theme_by_name(self, theme_name: str) -> Dict[str, Any]:
        """
        Get CRM theme by name.

        Args:
            theme_name: Name of the CRM theme

        Returns:
            Theme information including regulation ID
        """
        logger.info(f"Getting CRM theme: {theme_name}")

        result = await self._make_request(
            "CRMLead.getCRMThemeByName",
            {"НаименованиеТемы": theme_name}
        )

        return {
            "theme_id": result.get("d", [None, None, None, None])[0],
            "theme_name": result.get("d", [None, None, None, None])[1],
            "error": result.get("d", [None, None, None, None])[2],
            "regulation": result.get("d", [None, None, None, None])[3]
        }

    async def find_or_create_client(self, client_data: Dict[str, Any]) -> str:
        """
        Find existing client or create new one.

        Args:
            client_data: Client information

        Returns:
            Client ID
        """
        logger.info("Finding or creating client", extra={"client_data": client_data})

        # Try to find existing client first
        if "inn" in client_data and "kpp" in client_data:
            try:
                result = await self._make_request(
                    "Контрагент.ПоИННКППКФ",
                    {
                        "params": {
                            "d": [
                                client_data["inn"],
                                client_data["kpp"],
                                client_data.get("name", "")
                            ],
                            "s": [
                                {"n": "ИНН", "t": "Строка"},
                                {"n": "КПП", "t": "Строка"},
                                {"n": "Название", "t": "Строка"}
                            ],
                            "_type": "record",
                            "f": 0
                        }
                    }
                )
                logger.info(f"Found existing client: {result}")
                return str(result)

            except SabyApiError as e:
                logger.warning(f"Client not found, will create new: {e}")

        # Create new client if not found or no INN/KPP provided
        return await self._create_client(client_data)

    async def _create_client(self, client_data: Dict[str, Any]) -> str:
        """Create a new client."""
        logger.info("Creating new client", extra={"client_data": client_data})

        # This is a simplified client creation - adjust based on actual API requirements
        params = {
            "params": {
                "d": {
                    "ИНН": client_data.get("inn", ""),
                    "КПП": client_data.get("kpp", ""),
                    "Название": client_data.get("name", ""),
                },
                "s": {
                    "ИНН": "Строка",
                    "КПП": "Строка",
                    "Название": "Строка"
                }
            }
        }

        result = await self._make_request("Контрагент.ПоИННКППКФ", params)
        logger.info(f"Created new client: {result}")
        return str(result)

    async def create_deal(self, deal_request: CreateDealRequest) -> DealResponse:
        """
        Create a new deal in Saby CRM.

        Args:
            deal_request: Deal creation parameters

        Returns:
            Created deal information
        """
        logger.info("Creating deal", extra={"regulation": deal_request.regulation})

        # Prepare request parameters
        params = {
            "Лид": {
                "d": {
                    "Регламент": deal_request.regulation,
                },
                "s": {
                    "Регламент": "Число целое"
                }
            }
        }

        # Add optional fields
        deal_data = params["Лид"]["d"]
        deal_schema = params["Лид"]["s"]

        if deal_request.responsible:
            deal_data["Ответственный"] = deal_request.responsible
            deal_schema["Ответственный"] = "Строка"

        if deal_request.contact_person:
            contact_data = {
                "ФИО": deal_request.contact_person.name,
            }
            contact_schema = {
                "ФИО": "Строка",
            }

            if deal_request.contact_person.phone:
                contact_data["Телефон"] = deal_request.contact_person.phone
                contact_schema["Телефон"] = "Строка"

            if deal_request.contact_person.email:
                contact_data["email"] = deal_request.contact_person.email
                contact_schema["email"] = "Строка"

            deal_data["КонтактноеЛицо"] = {"d": contact_data, "s": contact_schema}
            deal_schema["КонтактноеЛицо"] = "Запись"

        if deal_request.client:
            client_data = {}
            client_schema = {}

            if deal_request.client.face_id:
                client_data["@Лицо"] = deal_request.client.face_id
                client_schema["@Лицо"] = "Строка"

            if deal_request.client.inn:
                client_data["ИНН"] = deal_request.client.inn
                client_schema["ИНН"] = "Строка"

            if deal_request.client.kpp:
                client_data["КПП"] = deal_request.client.kpp
                client_schema["КПП"] = "Строка"

            client_data["Наименование"] = deal_request.client.name
            client_schema["Наименование"] = "Строка"

            client_data["Type"] = deal_request.client.client_type
            client_schema["Type"] = {"Массив": "Число целое"}

            deal_data["Клиент"] = {"d": client_data, "s": client_schema}
            deal_schema["Клиент"] = "Запись"

        if deal_request.note:
            deal_data["Примечание"] = deal_request.note
            deal_schema["Примечание"] = "Строка"

        if deal_request.user_conditions:
            deal_data["UserConds"] = deal_request.user_conditions
            deal_schema["UserConds"] = "JSON-объект"

        if deal_request.nomenclatures:
            nomenclatures_data = []
            for nom in deal_request.nomenclatures:
                nomenclatures_data.append({
                    "code": nom.code,
                    "price": nom.price,
                    "count": nom.count
                })

            deal_data["Nomenclatures"] = nomenclatures_data
            deal_schema["Nomenclatures"] = "JSON-объект"

        # Make API request
        result = await self._make_request("CRMLead.insertRecord", params)

        # Parse response
        response_data = result.get("d", {})

        return DealResponse(
            document_id=response_data.get("@Документ", 0),
            uuid=response_data.get("ИдентификаторДокумента", ""),
            regulation=response_data.get("Регламент", deal_request.regulation),
            client=response_data.get("Клиент"),
            contact_person=response_data.get("КонтактноеЛицо"),
            note=response_data.get("Примечание"),
            state=response_data.get("Состояние"),
            source=response_data.get("Источник")
        )

    async def get_deal_status(self, deal_id: int) -> Dict[str, Any]:
        """
        Get current status of a deal.

        Args:
            deal_id: Deal document ID

        Returns:
            Deal status information
        """
        logger.info(f"Getting deal status for deal ID: {deal_id}")

        result = await self._make_request(
            "CRMLead.getStatus",
            {"ИдентификаторДокумента": deal_id}
        )

        return result


# Global Saby CRM client instance
saby_client = SabyCRMClient()