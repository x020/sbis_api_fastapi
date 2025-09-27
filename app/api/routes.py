"""
API routes for SBIS integration service.
"""
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.models.schemas import (
    APIMessage,
    CreateDealRequest,
    DealResponse,
    HealthResponse,
    WebhookPayload,
    WebhookResponse
)
from app.services.saby_client import saby_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse: Service health status
    """
    logger.info("Health check requested")

    # Check Saby CRM connection
    saby_connected = True
    try:
        # Try to get a test theme to verify connection
        await saby_client.get_crm_theme_by_name("Test")
    except Exception as e:
        logger.warning(f"Saby CRM connection check failed: {e}")
        saby_connected = False

    return HealthResponse(
        status="healthy" if saby_connected else "degraded",
        version="1.0.0",
        saby_connected=saby_connected
    )


@router.post("/deals", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(deal_request: CreateDealRequest) -> DealResponse:
    """
    Create a new deal in Saby CRM.

    Args:
        deal_request: Deal creation parameters

    Returns:
        DealResponse: Created deal information
    """
    logger.info(
        "Creating deal",
        extra={
            "regulation": deal_request.regulation,
            "has_client": deal_request.client is not None,
            "has_contact": deal_request.contact_person is not None
        }
    )

    try:
        # Create deal using Saby client
        deal_response = await saby_client.create_deal(deal_request)

        logger.info(
            "Deal created successfully",
            extra={
                "document_id": deal_response.document_id,
                "uuid": deal_response.uuid
            }
        )

        return deal_response

    except Exception as e:
        logger.error(f"Failed to create deal: {e}")
        raise


@router.get("/deals/{deal_id}", response_model=Dict)
async def get_deal_status(deal_id: int) -> Dict:
    """
    Get deal status from Saby CRM.

    Args:
        deal_id: Deal document ID

    Returns:
        Dict: Deal status information
    """
    logger.info(f"Getting deal status for ID: {deal_id}")

    try:
        status_info = await saby_client.get_deal_status(deal_id)

        logger.info(f"Deal status retrieved: {status_info}")
        return status_info

    except Exception as e:
        logger.error(f"Failed to get deal status: {e}")
        raise


@router.get("/themes/{theme_name}", response_model=Dict)
async def get_crm_theme(theme_name: str) -> Dict:
    """
    Get CRM theme information by name.

    Args:
        theme_name: Name of the CRM theme

    Returns:
        Dict: Theme information including regulation ID
    """
    logger.info(f"Getting CRM theme: {theme_name}")

    try:
        theme_info = await saby_client.get_crm_theme_by_name(theme_name)

        logger.info(f"CRM theme retrieved: {theme_info}")
        return theme_info

    except Exception as e:
        logger.error(f"Failed to get CRM theme: {e}")
        raise


@router.post("/clients/find-or-create", response_model=Dict)
async def find_or_create_client(client_data: Dict) -> Dict:
    """
    Find existing client or create new one in Saby CRM.

    Args:
        client_data: Client information

    Returns:
        Dict: Client information with ID
    """
    logger.info("Finding or creating client", extra={"client_data": client_data})

    try:
        client_id = await saby_client.find_or_create_client(client_data)

        result = {"client_id": client_id, **client_data}
        logger.info(f"Client processed: {result}")

        return result

    except Exception as e:
        logger.error(f"Failed to process client: {e}")
        raise


@router.post("/webhook/deal-created")
async def webhook_deal_created(payload: WebhookPayload) -> WebhookResponse:
    """
    Webhook endpoint for deal creation events.

    Args:
        payload: Webhook payload

    Returns:
        WebhookResponse: Processing result
    """
    logger.info(
        "Webhook deal created",
        extra={
            "event_type": payload.event_type,
            "data": payload.data
        }
    )

    try:
        # Process webhook payload
        # Add your webhook processing logic here

        return WebhookResponse(
            status="processed",
            message="Deal creation webhook processed successfully"
        )

    except Exception as e:
        logger.error(f"Failed to process webhook: {e}")
        return WebhookResponse(
            status="error",
            message=f"Failed to process webhook: {e}"
        )


@router.get("/", response_model=APIMessage)
async def root() -> APIMessage:
    """
    Root endpoint with API information.

    Returns:
        APIMessage: Welcome message
    """
    return APIMessage(
        message="SBIS API FastAPI Service - Integration with Saby CRM"
    )


@router.get("/info", response_model=Dict)
async def api_info() -> Dict:
    """
    Get API information and capabilities.

    Returns:
        Dict: API information
    """
    return {
        "name": "SBIS API FastAPI",
        "version": "1.0.0",
        "description": "Integration service for Saby CRM",
        "endpoints": {
            "health": "GET /health",
            "create_deal": "POST /deals",
            "get_deal": "GET /deals/{deal_id}",
            "get_theme": "GET /themes/{theme_name}",
            "find_client": "POST /clients/find-or-create",
            "webhook": "POST /webhook/deal-created"
        },
        "features": {
            "saby_auth": True,
            "deal_creation": True,
            "client_management": True,
            "webhooks": True
        }
    }