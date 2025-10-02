"""
API endpoints для генерации тестовых данных в реальном времени
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import asyncio
import json

from services.test_data_generator import test_data_generator
from services.analysis_service import AnalysisService
from database.models import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/start")
async def start_test_data():
    """Запуск генерации тестовых данных"""
    try:
        # Сбрасываем генератор
        test_data_generator.reset()
        
        return JSONResponse(content={
            "status": "started",
            "message": "Генерация тестовых данных запущена",
            "sample_rate": test_data_generator.sample_rate
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запуска: {str(e)}")


@router.post("/stop")
async def stop_test_data():
    """Остановка генерации тестовых данных"""
    try:
        return JSONResponse(content={
            "status": "stopped",
            "message": "Генерация тестовых данных остановлена"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка остановки: {str(e)}")


@router.get("/generate")
async def generate_test_data(duration: float = 1.0):
    """
    Генерация тестовых данных на указанный период
    
    Args:
        duration: Длительность в секундах (по умолчанию 1 секунда)
    """
    try:
        # Генерируем данные
        fhr_data = test_data_generator.generate_fhr_data(duration)
        uc_data = test_data_generator.generate_uc_data(duration)
        
        # Рассчитываем базовые метрики
        baseline_fhr = test_data_generator.calculate_baseline_fhr(fhr_data)
        variability = test_data_generator.calculate_variability(fhr_data)
        accelerations = test_data_generator.detect_accelerations(fhr_data, baseline_fhr)
        decelerations = test_data_generator.detect_decelerations(fhr_data, baseline_fhr)
        
        # Рассчитываем риск гипоксии
        hypoxia_risk = test_data_generator.calculate_hypoxia_risk(fhr_data, uc_data)
        
        # Получаем статистику
        statistics = test_data_generator.get_statistics()
        
        return JSONResponse(content={
            "fhr_data": fhr_data,
            "uc_data": uc_data,
            "baseline_fhr": baseline_fhr,
            "variability": variability,
            "accelerations": accelerations,
            "decelerations": decelerations,
            "hypoxia_risk": hypoxia_risk,
            "statistics": statistics,
            "duration": duration,
            "timestamp": fhr_data[-1]['time'] if fhr_data else 0
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")


@router.get("/analyze")
async def analyze_test_data(db: Session = Depends(get_db)):
    """
    Анализ последних сгенерированных данных
    """
    try:
        # Генерируем данные для анализа (последние 5 минут)
        fhr_data = test_data_generator.generate_fhr_data(300)  # 5 минут
        uc_data = test_data_generator.generate_uc_data(300)
        
        # Рассчитываем метрики
        baseline_fhr = test_data_generator.calculate_baseline_fhr(fhr_data)
        variability = test_data_generator.calculate_variability(fhr_data)
        accelerations = test_data_generator.detect_accelerations(fhr_data, baseline_fhr)
        decelerations = test_data_generator.detect_decelerations(fhr_data, baseline_fhr)
        
        # Определяем статус
        if baseline_fhr < 110:
            status = "bradycardia"
        elif baseline_fhr > 160:
            status = "tachycardia"
        else:
            status = "normal"
        
        # Рассчитываем риск гипоксии
        hypoxia_risk = test_data_generator.calculate_hypoxia_risk(fhr_data, uc_data)
        
        # Генерируем прогнозы (упрощенные)
        forecast_15min = {
            "status": "normal" if status == "normal" else "warning",
            "text": f"Прогноз на 15 минут: {status}"
        }
        
        forecast_30min = {
            "status": "normal" if status == "normal" else "warning", 
            "text": f"Прогноз на 30 минут: {status}"
        }
        
        forecast_60min = {
            "status": "normal" if status == "normal" else "warning",
            "text": f"Прогноз на 60+ минут: {status}"
        }
        
        # Получаем статистику
        statistics = test_data_generator.get_statistics()
        
        return JSONResponse(content={
            "fhr_data": fhr_data,
            "uc_data": uc_data,
            "analysis": {
                "fhr_base": baseline_fhr,
                "variability": variability,
                "status": status,
                "accelerations": accelerations,
                "decelerations": decelerations,
                "forecast_15min": forecast_15min,
                "forecast_30min": forecast_30min,
                "forecast_60min": forecast_60min,
                "hypoxia_risk": hypoxia_risk,
                "statistics": statistics
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")


@router.get("/status")
async def get_test_data_status():
    """Получение статуса генератора тестовых данных"""
    try:
        statistics = test_data_generator.get_statistics()
        
        return JSONResponse(content={
            "is_running": True,  # Всегда true, так как генератор работает по запросу
            "sample_rate": test_data_generator.sample_rate,
            "time_offset": test_data_generator.time_offset,
            "statistics": statistics
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса: {str(e)}")
