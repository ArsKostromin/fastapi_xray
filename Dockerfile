FROM python:3.13

RUN apt-get update && apt-get install -y docker.io

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ✅ Даем права на выполнение скрипта перезапуска aeee
RUN chmod +x /app/restart_xray.sh

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
