from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pypdf import PdfReader
from io import BytesIO
from database import save_profile, get_profile

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/report")
async def upload_medical_report(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload a PDF medical report, extract text, and save it to the user's profile.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # Read file content
        content = await file.read()
        pdf_file = BytesIO(content)
        
        # Extract text using pypdf
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")

        # Save to profile
        # We append/update the 'medical_report_text' field in the profile
        current_profile = get_profile(user_id)
        current_profile["medical_report_text"] = text.strip()
        current_profile["medical_report_uploaded_at"] = str(file.filename)
        
        save_profile(user_id, current_profile)
        
        return {
            "status": "success",
            "message": "Report uploaded and analyzed",
            "extracted_length": len(text)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
