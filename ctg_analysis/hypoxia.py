"""
Модуль для расчета риска гипоксии
Основан на эвристическом анализе FHR, UC и вариабельности
"""
import numpy as np
from typing import List, Dict


def calculate_hypoxia_risk(
    fhr_series: List[float],
    uc_series: List[float],
    variability_value: float,
    time_series: List[float],
    window_minutes: int = 2,
    step_minutes: int = 1
) -> List[Dict[str, float]]:
    """
    Расчет риска гипоксии по скользящему окну
    
    Параметры:
    - fhr_series: временной ряд ЧСС плода
    - uc_series: временной ряд сокращений матки
    - variability_value: значение вариабельности
    - time_series: временные метки
    - window_minutes: размер окна в минутах
    - step_minutes: шаг окна в минутах
    
    Возвращает:
    - список словарей {time, risk} для построения графика
    """
    
    # Параметры для детекции
    THRESH_ACCEL = 15  # порог для акселерации
    THRESH_DECEL = 15  # порог для децелерации
    
    # Преобразуем минуты в количество точек (предполагаем 1 Гц)
    window_size = window_minutes * 60
    step_size = step_minutes * 60
    
    results = []
    
    # Скользящее окно по данным
    for i in range(0, len(fhr_series) - window_size + 1, step_size):
        window_fhr = fhr_series[i:i + window_size]
        window_uc = uc_series[i:i + window_size] if i + window_size <= len(uc_series) else []
        
        # Расчет базового ритма в окне
        baseline = np.median(window_fhr) if window_fhr else 0
        
        # Детекция акселераций и децелераций
        accel_present, accel_count = detect_accelerations_in_window(window_fhr, baseline, THRESH_ACCEL)
        decel_present, decel_count = detect_decelerations_in_window(window_fhr, baseline, THRESH_DECEL)
        
        # Подсчет сокращений матки
        uc_count = count_contractions(window_uc) if window_uc else 0
        
        # Расчет риска
        risk = calculate_window_risk(
            baseline=baseline,
            variability=variability_value,
            uc_count=uc_count,
            accel_present=accel_present,
            decel_present=decel_present,
            accel_count=accel_count,
            decel_count=decel_count
        )
        
        # Временная метка центра окна
        time_center = time_series[i + window_size // 2] if i + window_size // 2 < len(time_series) else time_series[i]
        
        results.append({
            "time": time_center,
            "risk": risk
        })
    
    return results


def detect_accelerations_in_window(window_fhr: List[float], baseline: float, threshold: int) -> tuple:
    """
    Детекция акселераций в окне
    
    Возвращает: (accel_present, accel_count)
    """
    accel_present = any(fhr >= baseline + threshold for fhr in window_fhr)
    accel_count = sum(1 for fhr in window_fhr if fhr >= baseline + threshold)
    return accel_present, accel_count


def detect_decelerations_in_window(window_fhr: List[float], baseline: float, threshold: int) -> tuple:
    """
    Детекция децелераций в окне
    
    Возвращает: (decel_present, decel_count)
    """
    decel_present = any(fhr <= baseline - threshold for fhr in window_fhr)
    decel_count = sum(1 for fhr in window_fhr if baseline is not None and fhr <= baseline - threshold)
    return decel_present, decel_count


def count_contractions(uc_series: List[float], threshold: float = 15.0) -> int:
    """
    Подсчет количества сокращений матки
    
    Сокращение определяется как превышение порога
    """
    if not uc_series:
        return 0
    
    contractions = 0
    in_contraction = False
    
    for uc in uc_series:
        if uc > threshold:
            if not in_contraction:
                contractions += 1
                in_contraction = True
        else:
            in_contraction = False
    
    return contractions


def calculate_window_risk(
    baseline: float,
    variability: float,
    uc_count: int,
    accel_present: bool,
    decel_present: bool,
    accel_count: int,
    decel_count: int
) -> float:
    """
    Расчет риска гипоксии для окна
    
    Использует эвристическую оценку на основе:
    - Базового ритма (110-160 - норма)
    - Вариабельности (5-25 - норма)
    - Наличия децелераций (риск)
    - Отсутствия акселераций (риск)
    
    Возвращает значение риска от 0.0 до 1.0
    """
    
    # Оценка базового ритма
    if baseline == 0:
        baseline_score = 2
    elif 110 <= baseline <= 160:
        baseline_score = 0
    elif 105 <= baseline < 110 or 160 < baseline <= 165:
        baseline_score = 1
    else:
        baseline_score = 2
    
    # Оценка вариабельности
    if variability is None or variability == 0:
        var_score = 2
    elif variability >= 5:
        var_score = 0
    elif 3 <= variability < 5:
        var_score = 1
    else:
        var_score = 2
    
    # Оценка децелераций
    dec_score = 2 if decel_present else 0
    
    # Оценка акселераций
    acc_score = 0 if accel_present else 1
    
    # Количественная оценка
    acc_count_score = max(0, min(1, 2 - accel_count))
    dec_count_score = min(2, decel_count // 5)
    
    # Суммарный балл
    total_score = baseline_score + var_score + dec_score + acc_score + acc_count_score + dec_count_score
    
    # Нормализация к диапазону [0, 1]
    # Максимальный возможный балл: 2 + 2 + 2 + 1 + 1 + 2 = 10
    risk = max(0.0, min(1.0, total_score / 10.0))
    
    return risk


def classify_hypoxia_risk(risk: float) -> str:
    """
    Классификация уровня риска гипоксии
    
    - low: риск < 0.3
    - moderate: риск 0.3-0.6
    - high: риск > 0.6
    """
    if risk < 0.3:
        return "low"
    elif risk <= 0.6:
        return "moderate"
    else:
        return "high"

