from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from database.models import Patient, CTGSession, Report
from api.schemas import PatientCreate, PatientUpdate, CTGSessionCreate


def serialize_session(session: CTGSession) -> Dict[str, Any]:
    """Сериализация сессии с преобразованием JSON строк в словари"""
    session_dict = {
        "id": session.id,
        "patient_id": session.patient_id,
        "session_date": session.session_date,
        "fhr_file_path": session.fhr_file_path,
        "uc_file_path": session.uc_file_path,
        "baseline_fhr": session.baseline_fhr,
        "variability": session.variability,
        "accelerations_count": session.accelerations_count,
        "decelerations_count": session.decelerations_count,
        "status": session.status,
        "created_at": session.created_at
    }
    
    # Преобразуем JSON строки в словари
    if session.figo_result:
        try:
            session_dict["figo_result"] = json.loads(session.figo_result)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error parsing figo_result: {e}")
            session_dict["figo_result"] = None
    
    if session.nichd_result:
        try:
            session_dict["nichd_result"] = json.loads(session.nichd_result)
        except (json.JSONDecodeError, TypeError):
            session_dict["nichd_result"] = None
    
    if session.ai_result:
        try:
            session_dict["ai_result"] = json.loads(session.ai_result)
        except (json.JSONDecodeError, TypeError):
            session_dict["ai_result"] = None
    
    if session.forecast_15min:
        try:
            session_dict["forecast_15min"] = json.loads(session.forecast_15min)
        except (json.JSONDecodeError, TypeError):
            session_dict["forecast_15min"] = None
    
    if session.forecast_30min:
        try:
            session_dict["forecast_30min"] = json.loads(session.forecast_30min)
        except (json.JSONDecodeError, TypeError):
            session_dict["forecast_30min"] = None
    
    if session.forecast_60min:
        try:
            session_dict["forecast_60min"] = json.loads(session.forecast_60min)
        except (json.JSONDecodeError, TypeError):
            session_dict["forecast_60min"] = None
    
    if session.hypoxia_risk:
        try:
            session_dict["hypoxia_risk"] = json.loads(session.hypoxia_risk)
        except (json.JSONDecodeError, TypeError):
            session_dict["hypoxia_risk"] = None
    
    return session_dict


def serialize_patient(patient: Patient) -> Dict[str, Any]:
    """Сериализация пациентки с сериализацией сессий"""
    try:
        patient_dict = {
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
            "created_at": patient.created_at,
            "updated_at": patient.updated_at,
            "sessions": [serialize_session(session) for session in patient.sessions] if patient.sessions else []
        }
        
        # Устанавливаем дату последней сессии
        if patient.sessions:
            patient_dict["last_session"] = patient.sessions[0].session_date.strftime("%d.%m.%Y %H:%M")
        else:
            patient_dict["last_session"] = None
        
        return patient_dict
    except Exception as e:
        print(f"Error serializing patient {patient.id}: {e}")
        # Возвращаем минимальную информацию в случае ошибки
        return {
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
            "created_at": patient.created_at,
            "updated_at": patient.updated_at,
            "sessions": [],
            "last_session": None
        }


class PatientService:
    """Сервис для управления пациентками"""
    
    @staticmethod
    def create_patient(db: Session, patient: PatientCreate) -> Dict[str, Any]:
        """Создание новой пациентки"""
        db_patient = Patient(**patient.dict())
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        return serialize_patient(db_patient)
    
    @staticmethod
    def get_patient_by_id(db: Session, patient_id: int) -> Optional[Dict[str, Any]]:
        """Получение пациентки по ID"""
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if patient:
            return serialize_patient(patient)
        return None
    
    @staticmethod
    def get_all_patients(db: Session, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение всех пациенток с их сессиями"""
        patients = db.query(Patient).options(
            joinedload(Patient.sessions)
        ).offset(skip).limit(limit).all()
        
        return [serialize_patient(patient) for patient in patients]
    
    @staticmethod
    def update_patient(db: Session, patient_id: int, patient: PatientUpdate) -> Optional[Dict[str, Any]]:
        """Обновление данных пациентки"""
        db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not db_patient:
            return None
        
        update_data = patient.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_patient, key, value)
        
        db_patient.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_patient)
        return serialize_patient(db_patient)
    
    @staticmethod
    def delete_patient(db: Session, patient_id: int) -> bool:
        """Удаление пациентки"""
        db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not db_patient:
            return False
        
        db.delete(db_patient)
        db.commit()
        return True
    
    @staticmethod
    def search_patients(db: Session, query: str) -> List[Dict[str, Any]]:
        """Поиск пациенток по ФИО"""
        patients = db.query(Patient).options(
            joinedload(Patient.sessions)
        ).filter(
            Patient.full_name.ilike(f"%{query}%")
        ).all()
        
        return [serialize_patient(patient) for patient in patients]


class SessionService:
    """Сервис для управления сессиями КТГ"""
    
    @staticmethod
    def create_session(db: Session, session: CTGSessionCreate) -> CTGSession:
        """Создание новой сессии"""
        db_session = CTGSession(**session.dict())
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session
    
    @staticmethod
    def get_session_by_id(db: Session, session_id: int) -> Optional[CTGSession]:
        """Получение сессии по ID"""
        return db.query(CTGSession).filter(CTGSession.id == session_id).first()
    
    @staticmethod
    def get_sessions_by_patient(db: Session, patient_id: int) -> List[CTGSession]:
        """Получение всех сессий пациентки"""
        return db.query(CTGSession).filter(
            CTGSession.patient_id == patient_id
        ).order_by(CTGSession.session_date.desc()).all()
    
    @staticmethod
    def update_session_file(db: Session, session_id: int, file_type: str, file_path: str):
        """Обновление пути к файлу в сессии"""
        db_session = db.query(CTGSession).filter(CTGSession.id == session_id).first()
        if not db_session:
            return None
        
        if file_type == "fhr":
            db_session.fhr_file_path = file_path
        elif file_type == "uc":
            db_session.uc_file_path = file_path
        
        db.commit()
        db.refresh(db_session)
        return db_session
    
    @staticmethod
    def update_session_analysis(db: Session, session_id: int, analysis_data: dict):
        """Обновление результатов анализа в сессии"""
        db_session = db.query(CTGSession).filter(CTGSession.id == session_id).first()
        if not db_session:
            return None
        
        # Обновляем базовые метрики
        db_session.baseline_fhr = analysis_data.get("fhr_base")
        db_session.variability = analysis_data.get("variability")
        db_session.accelerations_count = analysis_data.get("accelerations", 0)
        db_session.decelerations_count = analysis_data.get("decelerations", 0)
        db_session.status = analysis_data.get("status")
        
        # Сохраняем результаты классификаций
        if analysis_data.get("figo_result"):
            db_session.figo_result = json.dumps(analysis_data["figo_result"], ensure_ascii=False)
        
        if analysis_data.get("nichd_result"):
            db_session.nichd_result = json.dumps(analysis_data["nichd_result"], ensure_ascii=False)
        
        if analysis_data.get("ai_result"):
            db_session.ai_result = json.dumps(analysis_data["ai_result"], ensure_ascii=False)
        
        # Сохраняем прогнозы
        if analysis_data.get("forecast_15min"):
            db_session.forecast_15min = json.dumps(analysis_data["forecast_15min"], ensure_ascii=False)
        
        if analysis_data.get("forecast_30min"):
            db_session.forecast_30min = json.dumps(analysis_data["forecast_30min"], ensure_ascii=False)
        
        if analysis_data.get("forecast_60min"):
            db_session.forecast_60min = json.dumps(analysis_data["forecast_60min"], ensure_ascii=False)
        
        # Сохраняем риск гипоксии
        if analysis_data.get("hypoxia_risk"):
            db_session.hypoxia_risk = json.dumps(analysis_data["hypoxia_risk"], ensure_ascii=False)
        
        db.commit()
        db.refresh(db_session)
        return db_session
    
    @staticmethod
    def delete_session(db: Session, session_id: int) -> bool:
        """Удаление сессии"""
        db_session = db.query(CTGSession).filter(CTGSession.id == session_id).first()
        if not db_session:
            return False
        
        db.delete(db_session)
        db.commit()
        return True

