"""
Классификация по NICHD/ACOG с учетом факторов риска пациентки
"""
from typing import Dict, List
from ctg_analysis.common import calc_baseline, detect_accelerations, detect_decelerations
from ctg_analysis.variability import calculate_variability, classify_variability
from ctg_analysis.risk_adjustment import calculate_risk_score, adjust_nichd_classification


def classify_nichd(fhr_series: List[float], risk_factors: Dict[str, bool], ga_weeks: int = 37) -> Dict:
    """
    Полная классификация по NICHD/ACOG с учетом факторов риска
    
    Категории NICHD:
    - Category I: Нормальная КТГ
    - Category II: Неопределенная КТГ (требует наблюдения)
    - Category III: Патологическая КТГ (требует вмешательства)
    
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
    
    # Определение паттерна децелераций (упрощенная логика)
    if decels_count == 0:
        dec_pattern = "none"
    elif decels_count <= 2:
        dec_pattern = "early"
    elif decels_count <= 5:
        dec_pattern = "variable"
    else:
        dec_pattern = "late"
    
    # 2. Базовая классификация по критериям NICHD
    base_label, base_code = classify_nichd_category(
        baseline, var_class, accels, decels_count, dec_pattern
    )
    
    # 3. Расчет балла риска и корректировка
    risk_score = calculate_risk_score(risk_factors)
    adjustment = adjust_nichd_classification(base_label, risk_score)
    
    # 4. Формирование результата
    result = {
        "source": "NICHD/ACOG",
        "baseline": round(baseline, 1),
        "variability": round(variability_value, 1),
        "variability_class": var_class,
        "accelerations": accels,
        "decelerations": {
            "count": decels_count,
            "pattern": dec_pattern
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


def classify_nichd_category(
    baseline: float,
    var_class: str,
    accels: int,
    decels_count: int,
    dec_pattern: str
) -> tuple:
    """
    Определение категории NICHD/ACOG
    
    Возвращает: (label, code)
    """
    
    # Category I (Нормальная)
    # Критерии:
    # - Baseline 110-160
    # - Moderate variability
    # - Accelerations present (если GA ≥ 32 недель)
    # - No decelerations или early decelerations
    
    if (110 <= baseline <= 160 and 
        var_class == "moderate" and 
        dec_pattern in ["none", "early"]):
        return "Category I", 0
    
    # Category III (Патологическая)
    # Критерии:
    # - Absent variability AND:
    #   - Recurrent late decelerations OR
    #   - Recurrent variable decelerations OR
    #   - Bradycardia
    # ИЛИ
    # - Sinusoidal pattern (не реализовано в этой версии)
    
    if var_class == "absent" and (
        dec_pattern in ["late", "variable"] or 
        baseline < 110 or
        decels_count > 3
    ):
        return "Category III", 2
    
    # Category II (Неопределенная)
    # Все остальные случаи, не попадающие в I или III
    
    return "Category II", 1

