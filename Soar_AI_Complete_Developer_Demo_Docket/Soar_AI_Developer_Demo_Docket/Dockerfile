FROM python:3.13-slim
WORKDIR /demo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m demo && mkdir -p /demo/runtime && chown -R demo:demo /demo
USER demo
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
