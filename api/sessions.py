from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from database.models import get_db
from api.schemas import CTGSessionCreate, CTGSessionResponse, FileUploadResponse
from services.database_service import SessionService
from services.file_service import FileService

router = APIRouter()

# Папка для хранения загруженных файлов
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/", response_model=CTGSessionResponse, status_code=201)
async def create_session(session: CTGSessionCreate, db: Session = Depends(get_db)):
    """Создание новой сессии КТГ"""
    return SessionService.create_session(db, session)


@router.get("/patient/{patient_id}", response_model=List[CTGSessionResponse])
async def get_patient_sessions(patient_id: int, db: Session = Depends(get_db)):
    """Получение всех сессий пациентки"""
    return SessionService.get_sessions_by_patient(db, patient_id)


@router.get("/{session_id}", response_model=CTGSessionResponse)
async def get_session(session_id: int, db: Session = Depends(get_db)):
    """Получение сессии по ID"""
    session = SessionService.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return session


@router.delete("/{session_id}")
async def delete_session(session_id: int, db: Session = Depends(get_db)):
    """Удаление сессии"""
    success = SessionService.delete_session(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return {"message": "Сессия успешно удалена"}


@router.post("/{session_id}/upload-fhr", response_model=FileUploadResponse)
async def upload_fhr_file(
    session_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Загрузка FHR файла для сессии"""
    session = SessionService.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    # Проверка формата файла
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Допустимы только CSV файлы")
    
    # Сохранение файла
    file_path = os.path.join(UPLOAD_DIR, f"session_{session_id}_fhr.csv")
    file_info = await FileService.save_upload_file(file, file_path)
    
    # Обновление сессии
    SessionService.update_session_file(db, session_id, "fhr", file_path)
    
    return FileUploadResponse(
        filename=file.filename,
        file_path=file_path,
        file_type="fhr",
        points_count=file_info["points_count"],
        duration_seconds=file_info["duration"],
        upload_status="success"
    )


@router.post("/{session_id}/upload-uc", response_model=FileUploadResponse)
async def upload_uc_file(
    session_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Загрузка UC файла для сессии"""
    session = SessionService.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    # Проверка формата файла
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Допустимы только CSV файлы")
    
    # Сохранение файла
    file_path = os.path.join(UPLOAD_DIR, f"session_{session_id}_uc.csv")
    file_info = await FileService.save_upload_file(file, file_path)
    
    # Обновление сессии
    SessionService.update_session_file(db, session_id, "uc", file_path)
    
    return FileUploadResponse(
        filename=file.filename,
        file_path=file_path,
        file_type="uc",
        points_count=file_info["points_count"],
        duration_seconds=file_info["duration"],
        upload_status="success"
    )


@router.get("/{session_id}/data")
async def get_session_data(session_id: int, db: Session = Depends(get_db)):
    """Получение данных КТГ для графиков"""
    session = SessionService.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    fhr_data = None
    uc_data = None
    
    if session.fhr_file_path and os.path.exists(session.fhr_file_path):
        fhr_data = FileService.read_csv_data(session.fhr_file_path)
    
    if session.uc_file_path and os.path.exists(session.uc_file_path):
        uc_data = FileService.read_csv_data(session.uc_file_path)
    
    return {
        "session_id": session_id,
        "fhr_data": fhr_data,
        "uc_data": uc_data
    }

