from pydantic import BaseModel
from typing import Optional, Literal

class ProfileSetupRequest(BaseModel):
    user_id: int
    age: int
    gender: Literal["male", "female", "other"]
    weight_kg: float
    height_cm: float
    diet_type: Literal["veg", "non-veg", "eggetarian", "vegan"]
    activity_level: Literal["low", "moderate", "high"]
    sleep_hours: float
    health_conditions: Optional[str] = None
    fitness_goal: Optional[str] = None
