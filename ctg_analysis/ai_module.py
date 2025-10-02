"""
Модуль ИИ для прогнозирования состояния плода

Примечание: В текущей версии используется эвристическая модель.
В будущем может быть заменен на LSTM/Transformer или другую ML модель.
"""
import numpy as np
from typing import Dict, List


def predict_outcomes(
    fhr_series: List[float],
    uc_series: List[float],
    risk_factors: Dict[str, bool]
) -> Dict:
    """
    Прогнозирование состояния плода на различные временные горизонты
    
    Параметры:
    - fhr_series: временной ряд ЧСС плода
    - uc_series: временной ряд сокращений матки
    - risk_factors: факторы риска пациентки
    
    Возвращает:
    - словарь с прогнозами на 15, 30 и 60+ минут
    """
    
    # Извлечение признаков
    features = extract_features(fhr_series, uc_series, risk_factors)
    
    # Прогнозирование (упрощенная эвристическая модель)
    # В реальном приложении здесь будет вызов обученной ML модели
    
    prediction_15min = predict_timeframe(features, "15min")
    prediction_30min = predict_timeframe(features, "30min")
    prediction_60min = predict_timeframe(features, "60min")
    
    return {
        "source": "ИИ модуль",
        "model_version": "v1.0_heuristic",
        "15min": prediction_15min,
        "30min": prediction_30min,
        "60min": prediction_60min,
        "features": features
    }


def extract_features(
    fhr_series: List[float],
    uc_series: List[float],
    risk_factors: Dict[str, bool]
) -> Dict:
    """
    Извлечение признаков для модели ИИ
    """
    
    # Статистические признаки FHR
    fhr_mean = np.mean(fhr_series) if fhr_series else 0
    fhr_std = np.std(fhr_series) if fhr_series else 0
    fhr_min = np.min(fhr_series) if fhr_series else 0
    fhr_max = np.max(fhr_series) if fhr_series else 0
    
    # Тренд FHR (простая линейная регрессия)
    fhr_trend = calculate_trend(fhr_series)
    
    # Статистические признаки UC
    uc_mean = np.mean(uc_series) if uc_series else 0
    uc_max = np.max(uc_series) if uc_series else 0
    
    # Количество сокращений
    uc_contractions = count_peaks(uc_series, threshold=15.0)
    
    # Факторы риска (векторизация)
    risk_score = sum([
        risk_factors.get("diabetes", 0) * 2,
        risk_factors.get("anemia", 0) * 1,
        risk_factors.get("hypertension", 0) * 2,
        risk_factors.get("preeclampsia", 0) * 3,
        risk_factors.get("infections", 0) * 2,
        risk_factors.get("multiple", 0) * 2,
        risk_factors.get("placenta", 0) * 3,
        risk_factors.get("term", 0) * 2
    ])
    
    return {
        "fhr_mean": fhr_mean,
        "fhr_std": fhr_std,
        "fhr_min": fhr_min,
        "fhr_max": fhr_max,
        "fhr_trend": fhr_trend,
        "uc_mean": uc_mean,
        "uc_max": uc_max,
        "uc_contractions": uc_contractions,
        "risk_score": risk_score
    }


def calculate_trend(series: List[float]) -> float:
    """
    Расчет тренда временного ряда (наклон линейной регрессии)
    
    Положительный тренд - рост, отрицательный - снижение
    """
    if not series or len(series) < 2:
        return 0.0
    
    x = np.arange(len(series))
    y = np.array(series)
    
    # Линейная регрессия
    coeffs = np.polyfit(x, y, 1)
    trend = coeffs[0]  # Наклон
    
    return float(trend)


def count_peaks(series: List[float], threshold: float) -> int:
    """
    Подсчет пиков в временном ряду
    """
    if not series:
        return 0
    
    peaks = 0
    in_peak = False
    
    for value in series:
        if value > threshold:
            if not in_peak:
                peaks += 1
                in_peak = True
        else:
            in_peak = False
    
    return peaks


def predict_timeframe(features: Dict, timeframe: str) -> Dict:
    """
    Прогнозирование для определенного временного горизонта
    
    Эвристическая модель на основе правил
    В реальном приложении - вызов ML модели
    """
    
    # Базовый риск на основе признаков
    risk_level = 0.0
    
    # Анализ базового ритма
    if features["fhr_mean"] < 110 or features["fhr_mean"] > 160:
        risk_level += 0.3
    
    # Анализ вариабельности
    if features["fhr_std"] < 5:
        risk_level += 0.3
    elif features["fhr_std"] > 25:
        risk_level += 0.2
    
    # Анализ тренда
    if features["fhr_trend"] < -0.5:  # Снижение ЧСС
        risk_level += 0.2
    elif features["fhr_trend"] > 0.5:  # Рост ЧСС
        risk_level += 0.1
    
    # Учет факторов риска
    risk_score_norm = min(features["risk_score"] / 10.0, 0.3)
    risk_level += risk_score_norm
    
    # Корректировка по временному горизонту
    if timeframe == "15min":
        adjustment = 1.0
    elif timeframe == "30min":
        adjustment = 1.2  # Больше неопределенности
        risk_level *= adjustment
    else:  # 60min
        adjustment = 1.5
        risk_level *= adjustment
    
    # Ограничение диапазона [0, 1]
    risk_level = min(max(risk_level, 0.0), 1.0)
    
    # Определение статуса и текста прогноза
    if risk_level < 0.3:
        status = "normal"
        prediction = "Стабильное состояние"
        confidence = 0.85
    elif risk_level < 0.6:
        status = "warning"
        prediction = "Возможны отклонения, рекомендуется наблюдение"
        confidence = 0.70
    else:
        status = "danger"
        prediction = "Высокий риск осложнений, требуется внимание"
        confidence = 0.60
    
    return {
        "status": status,
        "prediction": prediction,
        "risk_level": round(risk_level, 2),
        "confidence": confidence,
        "timeframe": timeframe
    }


# Заглушка для будущей интеграции реальной ML модели
def load_ml_model(model_path: str):
    """
    Загрузка обученной ML модели
    
    TODO: Реализовать загрузку модели (LSTM/Transformer)
    """
    pass


def predict_with_ml_model(model, features: np.ndarray):
    """
    Прогнозирование с использованием ML модели
    
    TODO: Реализовать прогнозирование
    """
    pass

