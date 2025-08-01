from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import httpx
from app.config import NOTIFICATION_API_URL

router = APIRouter()

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    message: str

@router.post("/contact")
async def contact_form(message: ContactMessage):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{NOTIFICATION_API_URL}/send-contact", json=message.model_dump())
            response.raise_for_status()
        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send contact message: {str(e)}")
