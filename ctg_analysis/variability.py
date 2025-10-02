"""
Модуль для оценки вариабельности ЧСС плода
"""
import numpy as np
from typing import List


def calculate_variability(fhr_series: List[float], method: str = "short_term") -> float:
    """
    Расчет вариабельности ЧСС плода
    
    Параметры:
    - fhr_series: временной ряд ЧСС
    - method: метод расчета ("short_term" или "long_term")
    
    Возвращает:
    - вариабельность в мс
    """
    if not fhr_series or len(fhr_series) < 2:
        return 0.0
    
    if method == "short_term":
        return calculate_short_term_variability(fhr_series)
    elif method == "long_term":
        return calculate_long_term_variability(fhr_series)
    else:
        return calculate_short_term_variability(fhr_series)


def calculate_short_term_variability(fhr_series: List[float]) -> float:
    """
    Краткосрочная вариабельность (STV - Short Term Variability)
    
    Рассчитывается как среднее абсолютное отклонение между
    последовательными ударами
    """
    if len(fhr_series) < 2:
        return 0.0
    
    # Вычисляем разности между последовательными значениями
    differences = []
    for i in range(len(fhr_series) - 1):
        diff = abs(fhr_series[i + 1] - fhr_series[i])
        differences.append(diff)
    
    # Среднее абсолютное отклонение
    stv = np.mean(differences)
    
    return stv


def calculate_long_term_variability(fhr_series: List[float], window_minutes: int = 1) -> float:
    """
    Долгосрочная вариабельность (LTV - Long Term Variability)
    
    Рассчитывается как разница между максимальным и минимальным
    значением ЧСС в окне времени (обычно 1 минута)
    """
    if len(fhr_series) < window_minutes * 60:
        # Если данных меньше, чем размер окна, используем все данные
        return np.max(fhr_series) - np.min(fhr_series)
    
    # Разбиваем на окна
    window_size = window_minutes * 60  # предполагаем, что данные идут с частотой 1 Гц
    
    variabilities = []
    for i in range(0, len(fhr_series) - window_size + 1, window_size):
        window = fhr_series[i:i + window_size]
        ltv = np.max(window) - np.min(window)
        variabilities.append(ltv)
    
    # Среднее значение LTV по всем окнам
    return np.mean(variabilities)


def classify_variability(variability: float) -> str:
    """
    Классификация вариабельности согласно клиническим критериям
    
    Категории:
    - absent: 0 мс (отсутствует)
    - minimal: < 5 мс (минимальная)
    - moderate: 5-25 мс (умеренная, норма)
    - marked: > 25 мс (выраженная)
    """
    if variability == 0:
        return "absent"
    elif variability < 5:
        return "minimal"
    elif 5 <= variability <= 25:
        return "moderate"
    else:
        return "marked"


def calculate_variability_index(fhr_series: List[float]) -> dict:
    """
    Комплексный индекс вариабельности
    
    Возвращает словарь с различными метриками вариабельности
    """
    stv = calculate_short_term_variability(fhr_series)
    ltv = calculate_long_term_variability(fhr_series)
    
    return {
        "short_term_variability": stv,
        "long_term_variability": ltv,
        "stv_classification": classify_variability(stv),
        "ltv_classification": classify_variability(ltv),
        "overall_variability": (stv + ltv) / 2
    }

