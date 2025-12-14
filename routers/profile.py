from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Any, Dict
from database import save_profile, update_user_profile_complete, get_user_by_id, get_profile as db_get_profile

router = APIRouter(prefix="/profile", tags=["profile"])


def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    if not height_cm or not weight_kg:
        return None
    height_m = height_cm / 100
    bmi = weight_kg / (height_m * height_m)
    return round(bmi, 2)


class ProfileUpdate(BaseModel):
    # accept the full set of fields your frontend sends
    age: Optional[int] = None
    gender: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    diet_type: Optional[str] = None
    activity_level: Optional[str] = None
    sleep_hours: Optional[float] = None
    health_conditions: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


@router.post("/setup")
def setup_profile(
    request: Request,
    user_id: Optional[str] = None,  # Accept string user_id (objectId string)
    profile_data: ProfileUpdate = None,
):
    """
    Setup user profile.
    Usage: POST /profile/setup?user_id=<user_id>
    Body: JSON with profile fields (age, gender, weight_kg, height_cm, diet_type, activity_level, sleep_hours, health_conditions, etc.)
    If user_id is not provided as query param, you may pass it in the body using the /setup-body endpoint.
    """

    # Validate presence of user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id (query param) is required")

    # Ensure user exists (optional safety)
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Save profile data (exclude None fields)
    pdata: Dict[str, Any] = profile_data.dict(exclude_none=True) if profile_data else {}

    # Accept alternative key names if frontend sends 'height'/'weight' instead of height_cm/weight_kg
    # Normalize to height_cm and weight_kg
    if "height" in pdata and "height_cm" not in pdata:
        try:
            pdata["height_cm"] = float(pdata.pop("height"))
        except Exception:
            pass
    if "weight" in pdata and "weight_kg" not in pdata:
        try:
            pdata["weight_kg"] = float(pdata.pop("weight"))
        except Exception:
            pass

    # Calculate BMI if we have height & weight
    height_val = pdata.get("height_cm")
    weight_val = pdata.get("weight_kg")
    try:
        if height_val is not None and weight_val is not None:
            bmi_val = calculate_bmi(float(height_val), float(weight_val))
            if bmi_val is not None:
                pdata["bmi"] = bmi_val
    except Exception:
        # if conversion fails, ignore BMI calculation and let validation happen elsewhere
        pass

    if pdata:
        save_profile(user_id, pdata)

    # Mark profile as complete
    success = update_user_profile_complete(user_id, True)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or could not update profile")

    return {
        "success": True,
        "message": "Profile setup complete!",
        "profile_complete": True,
        "profile": pdata,
    }


@router.post("/setup-body")
def setup_profile_body(data: Dict):
    """
    Alternative: Accept user_id in body
    Usage: POST /profile/setup-body
    Body: {"user_id": "<id>", "age": 25, ...}
    """
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    # Extract profile data (excluding user_id)
    profile_data = {k: v for k, v in data.items() if k != "user_id" and v is not None}

    # Normalize keys if needed
    if "height" in profile_data and "height_cm" not in profile_data:
        try:
            profile_data["height_cm"] = float(profile_data.pop("height"))
        except Exception:
            pass
    if "weight" in profile_data and "weight_kg" not in profile_data:
        try:
            profile_data["weight_kg"] = float(profile_data.pop("weight"))
        except Exception:
            pass

    # Calculate BMI if possible
    height_val = profile_data.get("height_cm")
    weight_val = profile_data.get("weight_kg")
    try:
        if height_val is not None and weight_val is not None:
            bmi_val = calculate_bmi(float(height_val), float(weight_val))
            if bmi_val is not None:
                profile_data["bmi"] = bmi_val
    except Exception:
        pass

    if profile_data:
        save_profile(user_id, profile_data)

    # Mark profile as complete
    success = update_user_profile_complete(user_id, True)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "success": True,
        "message": "Profile setup complete!",
        "profile_complete": True,
        "profile": profile_data,
    }

@router.get("/get")
def get_profile(user_id: str):
    """
    Fetch user profile from MongoDB
    Usage: GET /profile/get?user_id=<id>
    """
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = db_get_profile(user_id)
    if not profile:
        return {"profile": None}

    return {"profile": {k: str(v) if k == "_id" else v for k, v in profile.items()}}
