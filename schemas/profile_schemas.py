# backend/schemas/profile_schemas.py
from pydantic import BaseModel
from typing import Optional, Literal

class ProfileSchema(BaseModel):
    """Merged definitive schema for a user's health profile."""
    # (Note: Usually user_id is a string in MongoDB, but we'll preserve the type from the old files)
    user_id: int
    age: int
    gender: Literal["male", "female", "other"]
    weight_kg: float
    height_cm: float
    diet_type: Optional[Literal["veg", "non-veg", "eggetarian", "vegan"]] = None
    activity_level: Literal["low", "moderate", "high"]
    sleep_hours: Optional[float] = None
    health_conditions: Optional[str] = None
    fitness_goal: Optional[str] = None
