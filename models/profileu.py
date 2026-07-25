# backend/models/profileu.py
"""
Pydantic schemas for user profile operations.

Used by the /profile routes to validate profile creation and updates.
"""
from pydantic import BaseModel
from typing import Optional, Literal

class ProfileSetupRequest(BaseModel):
    """Schema for creating or updating a user's health profile, used by POST /profile/{user_id}."""
    user_id: int
    age: int
    gender: Literal["male", "female", "other"]
    weight_kg: float
    height_cm: float
    diet_type: Literal["veg", "non-veg", "eggetarian", "vegan"]
    activity_level: Literal["low", "moderate", "high"]
    sleep_hours: float
    # Free-text field detailing any chronic conditions or injuries to be considered by the agents
    health_conditions: Optional[str] = None
    # Free-text field describing the user's main objective (e.g., 'lose weight', 'build muscle')
    fitness_goal: Optional[str] = None
