from fastapi import FastAPI
from app.api.v1 import xray
from app.api.v1.log_watcher import tailer
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Xray FastAPI Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(xray.router, prefix="/api/v1", tags=["Xray"])

@app.on_event("startup")
async def startup_event():
    await tailer.start()
