FROM python:3.10-slim

WORKDIR /app

COPY backend/ ./backend/

RUN pip install uv && cd backend && uv sync

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
