from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.interface.routes import router

app = FastAPI(title="TaxDesk AI - Attachment Triage Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/api/health")
def health():
    return {"ok": True, "data": {"status": "up"}}
