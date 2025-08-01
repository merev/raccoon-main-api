from fastapi import FastAPI
from app.reservation import router as reservation_router
from app.contact import router as contact_router
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from raccoon_common import database, models

app = FastAPI(title="Raccoon Public API", root_path="/api")

app.include_router(reservation_router)
app.include_router(contact_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    for i in range(10):
        try:
            async with database.engine.begin() as conn:
                await conn.run_sync(models.Base.metadata.create_all)
            break
        except Exception as e:
            print(f"DB not ready yet, retrying... ({i + 1}/10)")
            await asyncio.sleep(2)
