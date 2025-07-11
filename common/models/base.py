from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel as PydanticBaseModel, Field

try:
    from bson import ObjectId
    HAS_BSON = True
except ImportError:
    HAS_BSON = False
    ObjectId = str


class ObjectIdStr(str):
    """Custom type for MongoDB ObjectId that serializes to string"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if HAS_BSON and isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            return v
        raise ValueError("Invalid ObjectId")


class BaseModel(PydanticBaseModel):
    """Base model with common fields for all entities"""
    
    id: Optional[ObjectIdStr] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for MongoDB storage"""
        return self.dict(by_alias=True, exclude_none=True)