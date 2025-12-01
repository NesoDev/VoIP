FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn qrcode

COPY main.py .
COPY add_extension.sh .

RUN chmod +x add_extension.sh

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
