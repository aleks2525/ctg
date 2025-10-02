from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.models import get_db
from api.schemas import AnalysisParams, AnalysisResult
from services.analysis_service import AnalysisService
from services.database_service import SessionService, PatientService

router = APIRouter()


@router.post("/{session_id}/analyze", response_model=AnalysisResult)
async def analyze_session(
    session_id: int,
    params: AnalysisParams,
    db: Session = Depends(get_db)
):
    """
    Анализ КТГ сессии с использованием выбранных модулей
    
    - **figo_nice**: Использовать эвристический модуль FIGO/NICE
    - **nichd_acog**: Использовать эвристический модуль NICHD/ACOG
    - **ai**: Использовать ИИ модуль для прогнозирования
    """
    try:
        # Получение сессии
        session = SessionService.get_session_by_id(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Сессия не найдена")
        
        # Проверка наличия файлов
        if not session.fhr_file_path or not session.uc_file_path:
            raise HTTPException(
                status_code=400,
                detail="Для анализа необходимо загрузить оба файла (FHR и UC)"
            )
        
        # Получение данных пациентки для учета факторов риска
        patient = PatientService.get_patient_by_id(db, session.patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Пациентка не найдена")
        
        # Выполнение анализа
        analysis_result = AnalysisService.analyze_ctg_session(
            db=db,
            session=session,
            patient=patient,
            use_figo=params.figo_nice,
            use_nichd=params.nichd_acog,
            use_ai=params.ai
        )
        
        # Сохраняем результаты анализа в базу данных
        analysis_data = {
            "fhr_base": analysis_result["fhr_base"],
            "variability": analysis_result["variability"],
            "accelerations": analysis_result["accelerations"],
            "decelerations": analysis_result["decelerations"],
            "status": analysis_result["status"],
            "figo_result": analysis_result["figo_result"],
            "nichd_result": analysis_result["nichd_result"],
            "ai_result": analysis_result["ai_result"],
            "forecast_15min": analysis_result["forecast_15min"],
            "forecast_30min": analysis_result["forecast_30min"],
            "forecast_60min": analysis_result["forecast_60min"],
            "hypoxia_risk": analysis_result["hypoxia_risk"]
        }
        
        # Обновляем сессию с результатами анализа
        SessionService.update_session_analysis(db, session_id, analysis_data)
        
        return analysis_result
        
    except HTTPException:
        # Перебрасываем HTTP исключения как есть
        raise
    except Exception as e:
        # Логируем ошибку для отладки (только в режиме разработки)
        import traceback
        import logging
        logging.error(f"Ошибка анализа сессии {session_id}: {str(e)}")
        logging.debug(f"Полная трассировка: {traceback.format_exc()}")
        
        # Возвращаем понятную ошибку клиенту
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка выполнения анализа: {str(e)}"
        )


@router.get("/{session_id}/statistics")
async def get_session_statistics(session_id: int, db: Session = Depends(get_db)):
    """Получение подробной статистики КТГ для модального окна"""
    session = SessionService.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    statistics = AnalysisService.get_detailed_statistics(db, session)
    
    return statistics

