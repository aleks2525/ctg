from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from api import patients, sessions, reports, analysis, test_data
from database.models import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    print("Database initialized")
    print("Server running on http://localhost:8000")
    yield
    # Shutdown
    print("Server stopped")


app = FastAPI(title="CTG Analysis System - ITELMA", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров API
app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(test_data.router, prefix="/api/test-data", tags=["Test Data"])

# Статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Главная страница
@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

