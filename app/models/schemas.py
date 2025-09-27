"""
Pydantic models for API request/response validation.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, EmailStr, Field, validator


class ContactPersonBase(BaseModel):
    """Base contact person model."""

    name: str = Field(..., min_length=1, max_length=255, description="Full name of contact person")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")

    @validator("phone")
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v and not v.replace("+", "").replace("-", "").replace("(", "").replace(")", "").replace(" ", "").isdigit():
            raise ValueError("Invalid phone number format")
        return v


class ContactPersonCreate(ContactPersonBase):
    """Model for creating contact person."""

    @validator("phone", "email")
    def validate_contact_info(cls, v, values):
        """Ensure either phone or email is provided."""
        if not v and not values.get("email") and not values.get("phone"):
            raise ValueError("Either phone or email must be provided")
        return v


class ClientBase(BaseModel):
    """Base client model."""

    name: str = Field(..., min_length=1, max_length=255, description="Client name")
    inn: Optional[str] = Field(None, regex=r"^\d{10,12}$", description="INN (10-12 digits)")
    kpp: Optional[str] = Field(None, regex=r"^\d{9}$", description="KPP (9 digits)")
    client_type: List[int] = Field(default=[0], description="Client types: 0-legal, 1-individual entrepreneur, 2-natural person")


class ClientCreate(ClientBase):
    """Model for creating client."""

    face_id: Optional[str] = Field(None, description="Existing client ID in Saby")


class DealNomenclatureBase(BaseModel):
    """Base nomenclature item model."""

    code: str = Field(..., min_length=1, max_length=50, description="Product code")
    price: float = Field(..., gt=0, description="Unit price")
    count: int = Field(..., gt=0, description="Quantity")


class CreateDealRequest(BaseModel):
    """Request model for creating a deal."""

    regulation: int = Field(..., gt=0, description="CRM regulation/theme ID")
    responsible: Optional[str] = Field(None, description="Responsible person ID")
    client: Optional[ClientCreate] = Field(None, description="Client information")
    contact_person: Optional[ContactPersonCreate] = Field(None, description="Contact person information")
    note: Optional[str] = Field(None, max_length=1000, description="Deal note")
    source: Optional[int] = Field(None, description="Deal source ID")
    notify: bool = Field(False, description="Send notifications")
    use_rules: bool = Field(True, description="Use registration rules")
    user_conditions: Optional[Dict[str, str]] = Field(None, description="User-defined conditions")
    nomenclatures: Optional[List[DealNomenclatureBase]] = Field(None, description="Deal products")
    additional_fields: Optional[Dict[str, Any]] = Field(None, description="Additional custom fields")

    @validator("client", "contact_person")
    def validate_client_or_contact(cls, v, values, field):
        """Ensure either client or contact_person is provided."""
        if field.name == "client" and not v and not values.get("contact_person"):
            raise ValueError("Either client or contact_person must be provided")
        return v


class DealResponse(BaseModel):
    """Response model for deal operations."""

    document_id: int = Field(..., description="Deal document ID")
    uuid: str = Field(..., description="Deal UUID")
    regulation: int = Field(..., description="Regulation ID")
    client: Optional[Dict[str, Any]] = Field(None, description="Client information")
    contact_person: Optional[Dict[str, Any]] = Field(None, description="Contact person information")
    note: Optional[str] = Field(None, description="Deal note")
    state: Optional[str] = Field(None, description="Deal state")
    source: Optional[int] = Field(None, description="Deal source")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    code: Optional[int] = Field(None, description="Error code")
    details: Optional[str] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field(..., description="API version")
    saby_connected: bool = Field(..., description="Saby CRM connection status")


class DealListResponse(BaseModel):
    """Response model for deal list operations."""

    deals: List[DealResponse] = Field(..., description="List of deals")
    total: int = Field(..., description="Total number of deals")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")


# API Documentation models
class APIMessage(BaseModel):
    """Generic API message model."""

    message: str = Field(..., description="Message text")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")


# Webhook models (for future extensions)
class WebhookPayload(BaseModel):
    """Webhook payload model."""

    event_type: str = Field(..., description="Type of event")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")


class WebhookResponse(BaseModel):
    """Webhook response model."""

    status: str = Field(..., description="Response status")
    message: Optional[str] = Field(None, description="Response message")