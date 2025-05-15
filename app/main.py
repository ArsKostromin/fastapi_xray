from fastapi import FastAPI
from app.api.v1 import xray
import threading
import time

app = FastAPI(title="Xray FastAPI Service")
app.include_router(xray.router, prefix="/api/v1", tags=["Xray"])

def background_log_sender():
    while True:
        time.sleep(60)
        try:
            xray.send_logs()
        except Exception as e:
            print("Log sender error:", e)

threading.Thread(target=background_log_sender, daemon=True).start()
