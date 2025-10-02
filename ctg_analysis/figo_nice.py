"""
Классификация по FIGO/NICE с учетом факторов риска пациентки
"""
from typing import Dict, List
from ctg_analysis.common import calc_baseline, detect_accelerations, detect_decelerations
from ctg_analysis.variability import calculate_variability, classify_variability
from ctg_analysis.risk_adjustment import calculate_risk_score, adjust_figo_classification


def evaluate_baseline(baseline: float) -> str:
    """
    Оценка базового ритма
    
    - reassuring: 110-160 уд/мин
    - non-reassuring: 100-109 или 161-180 уд/мин
    - abnormal: < 100 или > 180 уд/мин
    """
    if 110 <= baseline <= 160:
        return "reassuring"
    elif 100 <= baseline < 110 or 161 <= baseline <= 180:
        return "non-reassuring"
    else:
        return "abnormal"


def evaluate_variability(variability: float, var_class: str) -> str:
    """
    Оценка вариабельности
    
    - reassuring: moderate (5-25)
    - non-reassuring: minimal (< 5) или marked (> 25)
    - abnormal: absent (0)
    """
    if var_class == "moderate":
        return "reassuring"
    elif var_class in ["minimal", "marked"]:
        return "non-reassuring"
    else:  # absent
        return "abnormal"


def evaluate_accelerations(accels: int, duration_minutes: int = 20) -> str:
    """
    Оценка акселераций
    
    NICE: ≥2 акселерации за 20 минут - reassuring
    """
    if accels >= 2:
        return "reassuring"
    else:
        return "non-reassuring"


def evaluate_decelerations(decels_count: int) -> str:
    """
    Оценка децелераций
    
    - reassuring: нет децелераций
    - non-reassuring: редкие децелерации (< 3)
    - abnormal: частые децелерации (≥ 3)
    """
    if decels_count == 0:
        return "reassuring"
    elif decels_count < 3:
        return "non-reassuring"
    else:
        return "abnormal"


def classify_figo(fhr_series: List[float], risk_factors: Dict[str, bool], ga_weeks: int = 37) -> Dict:
    """
    Полная классификация по FIGO/NICE с учетом факторов риска
    
    Параметры:
    - fhr_series: временной ряд ЧСС плода
    - risk_factors: словарь факторов риска пациентки
    - ga_weeks: гестационный возраст в неделях
    
    Возвращает:
    - словарь с результатами классификации
    """
    
    # 1. Расчет базовых метрик
    baseline = calc_baseline(fhr_series)
    variability_value = calculate_variability(fhr_series)
    var_class = classify_variability(variability_value)
    accels = detect_accelerations(fhr_series, baseline, ga_weeks)
    decels_count = detect_decelerations(fhr_series, baseline)
    
    # 2. Оценка каждого параметра
    baseline_eval = evaluate_baseline(baseline)
    variability_eval = evaluate_variability(variability_value, var_class)
    accels_eval = evaluate_accelerations(accels)
    decels_eval = evaluate_decelerations(decels_count)
    
    evaluations = [baseline_eval, variability_eval, accels_eval, decels_eval]
    
    # 3. Базовая классификация
    if all(ev == "reassuring" for ev in evaluations):
        base_label = "Normal"
        base_code = 0
    elif "abnormal" in evaluations:
        base_label = "Pathological"
        base_code = 2
    else:
        base_label = "Suspicious"
        base_code = 1
    
    # 4. Расчет балла риска и корректировка
    risk_score = calculate_risk_score(risk_factors)
    adjustment = adjust_figo_classification(base_label, risk_score)
    
    # 5. Формирование результата
    result = {
        "source": "FIGO/NICE",
        "baseline": round(baseline, 1),
        "variability": round(variability_value, 1),
        "variability_class": var_class,
        "accelerations": accels,
        "decelerations": decels_count,
        "evaluations": {
            "baseline": baseline_eval,
            "variability": variability_eval,
            "accelerations": accels_eval,
            "decelerations": decels_eval
        },
        "base_classification": {
            "label": base_label,
            "code": base_code
        },
        "final_classification": {
            "label": adjustment["adjusted_label"],
            "code": adjustment["code"]
        },
        "risk_adjustment": {
            "applied": adjustment["adjustment_applied"],
            "risk_score": risk_score,
            "reason": adjustment["adjustment_reason"]
        },
        "label": adjustment["adjusted_label"],
        "code": adjustment["code"]
    }
    
    return result

