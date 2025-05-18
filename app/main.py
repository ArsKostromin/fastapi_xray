from fastapi import FastAPI
from app.api.v1 import xray
from api.v1.log_watcher import tailer  # используем общий экземпляр
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Xray FastAPI Service")

# Если надо, добавь CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # настрой по вкусу
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(xray.router, prefix="/api/v1", tags=["Xray"])

# СТАРТУЕМ ЛОГГЕР ПРИ СТАРТЕ
@app.on_event("startup")
async def startup_event():
    tailer.start()
