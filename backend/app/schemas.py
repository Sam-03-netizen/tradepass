from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class CompanyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    country: str = Field(default="IN", min_length=2, max_length=2)
    company_type: str = Field(default="exporter", max_length=40)
    @field_validator("country")
    @classmethod
    def country_upper(cls, v): return v.strip().upper()

class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=10, max_length=72)
    @field_validator("password")
    @classmethod
    def bcrypt_byte_limit(cls, v):
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        return v

class RegisterRequest(BaseModel):
    company: CompanyCreate
    user: UserCreate

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; name: str; email: EmailStr; company_id: int; role: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ShipmentCreate(BaseModel):
    reference_number: str = Field(min_length=2, max_length=80)
    product: str = Field(min_length=2, max_length=250)
    origin_country: str = Field(min_length=2, max_length=2)
    destination_country: str = Field(min_length=2, max_length=2)
    buyer_name: str | None = Field(default=None, max_length=200)
    @field_validator("reference_number", "product", "origin_country", "destination_country")
    @classmethod
    def strip_text(cls, v): return v.strip().upper() if v and len(v.strip()) == 2 and v.isalpha() else v.strip()
    @field_validator("origin_country", "destination_country")
    @classmethod
    def country_code(cls, v):
        if not v.isalpha() or len(v) != 2: raise ValueError("Use a two-letter country code, e.g. IN or DE")
        return v.upper()

class ShipmentUpdate(BaseModel):
    product: str | None = Field(default=None, min_length=2, max_length=250)
    buyer_name: str | None = Field(default=None, max_length=200)
    status: Literal["draft", "in_progress", "ready_for_review", "completed", "on_hold"] | None = None

class ShipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; company_id: int; created_by: int; reference_number: str; product: str; origin_country: str; destination_country: str; buyer_name: str | None; status: str; created_at: datetime; updated_at: datetime

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; shipment_id: int; original_filename: str; category: str; content_type: str; size_bytes: int; processing_status: str; review_status: str; extracted_fields: dict; reviewed_fields: dict; expiry_date: str | None; created_at: datetime

class ReviewFields(BaseModel):
    fields: dict = Field(default_factory=dict)
    expiry_date: str | None = None

class ShareCreate(BaseModel):
    document_ids: list[int] = Field(default_factory=list)
    expires_in_hours: int = Field(default=72, ge=1, le=720)

class ResolveIssue(BaseModel):
    resolved: bool = True
