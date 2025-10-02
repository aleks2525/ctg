"""
Общие функции для анализа КТГ
"""
import numpy as np
from typing import List


def calc_baseline(fhr_series: List[float], window_size: int = 10) -> float:
    """
    Расчет базового ритма (baseline FHR)
    
    Используется скользящее окно для сглаживания и вычисления медианы
    """
    if not fhr_series:
        return 0.0
    
    # Фильтрация выбросов (значения вне диапазона 50-200)
    filtered = [fhr for fhr in fhr_series if 50 <= fhr <= 200]
    
    if not filtered:
        return 0.0
    
    # Расчет медианы с использованием скользящего окна
    if len(filtered) < window_size:
        return np.median(filtered)
    
    windowed_medians = []
    for i in range(len(filtered) - window_size + 1):
        window = filtered[i:i + window_size]
        windowed_medians.append(np.median(window))
    
    return np.median(windowed_medians)


def detect_accelerations(fhr_series: List[float], baseline: float, ga_weeks: int = 37) -> int:
    """
    Обнаружение акселераций
    
    Критерии:
    - Повышение ЧСС на ≥15 уд/мин от baseline (≥10 для < 32 недель)
    - Продолжительность ≥15 секунд
    """
    if not fhr_series or baseline == 0:
        return 0
    
    # Порог для акселерации
    threshold = 10 if ga_weeks < 32 else 15
    
    accelerations_count = 0
    in_acceleration = False
    acceleration_length = 0
    
    for fhr in fhr_series:
        if fhr >= baseline + threshold:
            if not in_acceleration:
                in_acceleration = True
                acceleration_length = 1
            else:
                acceleration_length += 1
        else:
            if in_acceleration and acceleration_length >= 15:  # минимум 15 точек
                accelerations_count += 1
            in_acceleration = False
            acceleration_length = 0
    
    # Проверка последней акселерации
    if in_acceleration and acceleration_length >= 15:
        accelerations_count += 1
    
    return accelerations_count


def detect_decelerations(fhr_series: List[float], baseline: float, threshold: int = 15) -> int:
    """
    Обнаружение децелераций
    
    Критерии:
    - Снижение ЧСС на ≥15 уд/мин от baseline
    - Продолжительность ≥15 секунд
    """
    if not fhr_series or baseline == 0:
        return 0
    
    decelerations_count = 0
    in_deceleration = False
    deceleration_length = 0
    
    for fhr in fhr_series:
        if fhr <= baseline - threshold:
            if not in_deceleration:
                in_deceleration = True
                deceleration_length = 1
            else:
                deceleration_length += 1
        else:
            if in_deceleration and deceleration_length >= 15:
                decelerations_count += 1
            in_deceleration = False
            deceleration_length = 0
    
    # Проверка последней децелерации
    if in_deceleration and deceleration_length >= 15:
        decelerations_count += 1
    
    return decelerations_count


def smooth_signal(signal: List[float], window_size: int = 5) -> List[float]:
    """Сглаживание сигнала скользящим средним"""
    if len(signal) < window_size:
        return signal
    
    smoothed = []
    for i in range(len(signal)):
        start = max(0, i - window_size // 2)
        end = min(len(signal), i + window_size // 2 + 1)
        window = signal[start:end]
        smoothed.append(np.mean(window))
    
    return smoothed

