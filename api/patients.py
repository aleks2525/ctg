from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import json

from database.models import get_db, Patient, CTGSession
from api.schemas import PatientCreate, PatientUpdate, PatientResponse
from services.database_service import PatientService

# Создаем роутер без валидации ответов
router = APIRouter()


@router.post("/", status_code=201)
async def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """Создание новой пациентки"""
    new_patient = PatientService.create_patient(db, patient)
    return JSONResponse(content=new_patient, status_code=201)


@router.get("/")
async def get_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получение списка всех пациенток"""
    try:
        # Получаем только базовую информацию без сессий
        patients = db.query(Patient).offset(skip).limit(limit).all()
        
        result = []
        for patient in patients:
            # Получаем сессии для каждой пациентки
            sessions = db.query(CTGSession).filter(
                CTGSession.patient_id == patient.id
            ).order_by(CTGSession.session_date.desc()).all()
            
            # Сериализуем сессии
            sessions_data = []
            for session in sessions:
                session_data = {
                    "id": session.id,
                    "patient_id": session.patient_id,
                    "session_date": session.session_date.isoformat() if session.session_date else None,
                    "fhr_file_path": session.fhr_file_path,
                    "uc_file_path": session.uc_file_path,
                    "baseline_fhr": session.baseline_fhr,
                    "variability": session.variability,
                    "accelerations_count": session.accelerations_count,
                    "decelerations_count": session.decelerations_count,
                    "status": session.status,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "figo_result": None,
                    "nichd_result": None,
                    "ai_result": None,
                    "forecast_15min": None,
                    "forecast_30min": None,
                    "forecast_60min": None,
                    "hypoxia_risk": None
                }
                
                # Парсим JSON поля
                import json
                if session.figo_result:
                    try:
                        session_data["figo_result"] = json.loads(session.figo_result)
                    except:
                        pass
                if session.nichd_result:
                    try:
                        session_data["nichd_result"] = json.loads(session.nichd_result)
                    except:
                        pass
                if session.ai_result:
                    try:
                        session_data["ai_result"] = json.loads(session.ai_result)
                    except:
                        pass
                if session.forecast_15min:
                    try:
                        session_data["forecast_15min"] = json.loads(session.forecast_15min)
                    except:
                        pass
                if session.forecast_30min:
                    try:
                        session_data["forecast_30min"] = json.loads(session.forecast_30min)
                    except:
                        pass
                if session.forecast_60min:
                    try:
                        session_data["forecast_60min"] = json.loads(session.forecast_60min)
                    except:
                        pass
                if session.hypoxia_risk:
                    try:
                        session_data["hypoxia_risk"] = json.loads(session.hypoxia_risk)
                    except:
                        pass
                
                sessions_data.append(session_data)
            
            last_session_date = None
            if sessions:
                last_session_date = sessions[0].session_date.strftime("%d.%m.%Y %H:%M")
            
            patient_data = {
                "id": patient.id,
                "full_name": patient.full_name,
                "diagnosis": patient.diagnosis,
                "diabetes": patient.diabetes,
                "anemia": patient.anemia,
                "hypertension": patient.hypertension,
                "preeclampsia": patient.preeclampsia,
                "infections": patient.infections,
                "multiple": patient.multiple,
                "placenta": patient.placenta,
                "term": patient.term,
                "created_at": patient.created_at.isoformat() if patient.created_at else None,
                "updated_at": patient.updated_at.isoformat() if patient.updated_at else None,
                "sessions": sessions_data,
                "last_session": last_session_date,
                "sessions_count": len(sessions)
            }
            result.append(patient_data)
        
        return JSONResponse(content=result)
    except Exception as e:
        print(f"Error in get_patients: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


@router.get("/{patient_id}")
async def get_patient(patient_id: int, db: Session = Depends(get_db)):
    """Получение пациентки по ID"""
    patient = PatientService.get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Пациентка не найдена")
    return JSONResponse(content=patient)


@router.put("/{patient_id}")
async def update_patient(patient_id: int, patient: PatientUpdate, db: Session = Depends(get_db)):
    """Обновление данных пациентки"""
    updated_patient = PatientService.update_patient(db, patient_id, patient)
    if not updated_patient:
        raise HTTPException(status_code=404, detail="Пациентка не найдена")
    return JSONResponse(content=updated_patient)


@router.delete("/{patient_id}")
async def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    """Удаление пациентки"""
    success = PatientService.delete_patient(db, patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Пациентка не найдена")
    return {"message": "Пациентка успешно удалена"}


@router.get("/search/{query}")
async def search_patients(query: str, db: Session = Depends(get_db)):
    """Поиск пациенток по ФИО"""
    patients = PatientService.search_patients(db, query)
    return JSONResponse(content=patients)

