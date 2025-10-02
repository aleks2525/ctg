from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database.models import get_db
from api.schemas import ReportCreate, ReportResponse
from services.report_service import ReportService
from services.database_service import SessionService

router = APIRouter()


@router.post("/", response_model=ReportResponse, status_code=201)
async def create_report(report: ReportCreate, db: Session = Depends(get_db)):
    """Создание отчета по сессии КТГ"""
    session = SessionService.get_session_by_id(db, report.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    return ReportService.generate_report(db, session)


@router.get("/session/{session_id}", response_model=ReportResponse)
async def get_session_report(session_id: int, db: Session = Depends(get_db)):
    """Получение отчета по сессии"""
    report = ReportService.get_report_by_session(db, session_id)
    if not report:
        raise HTTPException(status_code=404, detail="Отчет не найден")
    return report


@router.get("/patient/{patient_id}", response_model=List[ReportResponse])
async def get_patient_reports(patient_id: int, db: Session = Depends(get_db)):
    """Получение всех отчетов пациентки"""
    return ReportService.get_reports_by_patient(db, patient_id)


@router.get("/{report_id}/download")
async def download_report(report_id: int, db: Session = Depends(get_db)):
    """Скачивание отчета в формате HTML"""
    report = ReportService.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Отчет не найден")
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=report.report_html, media_type="text/html")

