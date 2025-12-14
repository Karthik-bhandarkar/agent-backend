from pydantic import BaseModel

class UserProfile(BaseModel):
    user_id: int
    weight: float
    height: float
    age: int
    gender: str
    activity_level: str
    health_conditions: str
    fitness_goal: str
