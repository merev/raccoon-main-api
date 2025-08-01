from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from raccoon_common import models, schemas, database
from app.config import NOTIFICATION_API_URL
import httpx
import os

router = APIRouter()

@router.post("/reservations")
async def create_reservation(reservation: schemas.ReservationIn, db: AsyncSession = Depends(database.get_db)):
    try:
        new_res = models.Reservation(**reservation.model_dump())
        db.add(new_res)
        await db.commit()
        await db.refresh(new_res)

        # Notify Telegram
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{NOTIFICATION_API_URL}/send-telegram", json={
                    "reservation": schemas.ReservationOut.model_validate(new_res).model_dump()
                })
        except Exception as e:
            print(f"Telegram failed: {e}")

        # Notify Email
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{NOTIFICATION_API_URL}/send-email", json={
                    "email": reservation.email,
                    "reservation": schemas.ReservationOut.model_validate(new_res).model_dump()
                })
        except Exception as e:
            print(f"Email failed: {e}")

        return {"status": "success", "reservation_id": str(new_res.id)}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reservations/decline")
async def decline_reservation(token: str, db: AsyncSession = Depends(database.get_db)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{NOTIFICATION_API_URL}/verify-decline-token", json={"token": token})
            response.raise_for_status()
            data = response.json()
            reservation_id = data["reservation_id"]

        stmt = update(models.Reservation).where(models.Reservation.id == reservation_id).values(status="declined")
        await db.execute(stmt)
        await db.commit()
        return {"status": "declined", "reservation_id": reservation_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
