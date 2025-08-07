from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: Optional[int] = None
    employee_id: str = Field(..., description="Employee badge ID")
    first_name: str = Field(..., min_length=1, description="First name")
    last_name: str = Field(..., min_length=1, description="Last name")
    table_number: int = Field(..., gt=0, description="Table number")
    last_checkin: Optional[str] = None
    is_checked_in: bool = False

class UserCreate(BaseModel):
    employee_id: str = Field(..., description="Employee badge ID")
    first_name: str = Field(..., min_length=1, description="First name")
    last_name: str = Field(..., min_length=1, description="Last name")
    table_number: int = Field(..., gt=0, description="Table number")

class Checkin(BaseModel):
    id: Optional[int] = None
    employee_id: str
    checkin_time: Optional[datetime] = None

class CheckinRecord(BaseModel):
    first_name: str
    last_name: str
    employee_id: str
    table_number: int
    checkin_time: str

class CheckinResponse(BaseModel):
    success: bool
    name: Optional[str] = None
    table_number: Optional[int] = None
    time: Optional[str] = None
    message: Optional[str] = None

class ImportResponse(BaseModel):
    success: bool
    imported: int = 0
    errors: list[str] = []
    message: Optional[str] = None

class DeleteResponse(BaseModel):
    success: bool
    deleted: int = 0
    message: Optional[str] = None

class CreateUserResponse(BaseModel):
    success: bool
    message: str
    user: Optional[User] = None

class Settings(BaseModel):
    welcome_banner: str
    secondary_banner: str
    text_color: str
    foreground_color: str
    background_color: str
    background_image: str

class SettingsUpdate(BaseModel):
    welcome_banner: Optional[str] = None
    secondary_banner: Optional[str] = None
    text_color: Optional[str] = None
    foreground_color: Optional[str] = None
    background_color: Optional[str] = None
    background_image: Optional[str] = None

class SettingsResponse(BaseModel):
    success: bool
    message: str
    settings: Optional[Settings] = None