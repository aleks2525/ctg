"""
Модуль учета факторов риска анамнеза пациентки
Корректирует классификацию КТГ на основе векторизации факторов
"""
from typing import Dict


# Весовые коэффициенты факторов риска
RISK_SCORES = {
    "diabetes": 2,          # Сахарный диабет
    "anemia": 1,            # Анемия
    "hypertension": 2,      # Хроническая гипертония
    "preeclampsia": 3,      # Преэклампсия
    "infections": 2,        # Инфекционные заболевания
    "multiple": 2,          # Многоплодная беременность
    "placenta": 3,          # Патологии плаценты и пуповины
    "term": 2               # Срок беременности < 37 или > 41 недель
}


def calculate_risk_score(risk_factors: Dict[str, bool]) -> int:
    """
    Расчет общего балла риска на основе факторов анамнеза
    
    Параметры:
    - risk_factors: словарь {фактор: наличие (True/False)}
    
    Возвращает:
    - суммарный балл риска
    """
    score = 0
    for key, value in risk_factors.items():
        if value and key in RISK_SCORES:
            score += RISK_SCORES[key]
    return score


def adjust_figo_classification(base_label: str, risk_score: int) -> Dict[str, any]:
    """
    Корректировка FIGO/NICE классификации с учетом факторов риска
    
    Параметры:
    - base_label: базовая классификация ("Normal", "Suspicious", "Pathological")
    - risk_score: балл риска из анамнеза
    
    Возвращает:
    - словарь с скорректированной классификацией
    """
    adjusted_label = base_label
    adjustment_applied = False
    
    # Если балл риска >= 4, повышаем категорию
    if risk_score >= 4:
        if base_label == "Normal":
            adjusted_label = "Suspicious"
            adjustment_applied = True
        elif base_label == "Suspicious":
            adjusted_label = "Pathological"
            adjustment_applied = True
    
    # Код для категории
    code_map = {
        "Normal": 0,
        "Suspicious": 1,
        "Pathological": 2
    }
    
    return {
        "original_label": base_label,
        "adjusted_label": adjusted_label,
        "code": code_map.get(adjusted_label, 0),
        "adjustment_applied": adjustment_applied,
        "risk_score": risk_score,
        "adjustment_reason": f"Высокий балл риска анамнеза ({risk_score})" if adjustment_applied else None
    }


def adjust_nichd_classification(base_label: str, risk_score: int) -> Dict[str, any]:
    """
    Корректировка NICHD/ACOG классификации с учетом факторов риска
    
    Параметры:
    - base_label: базовая классификация ("Category I", "Category II", "Category III")
    - risk_score: балл риска из анамнеза
    
    Возвращает:
    - словарь с скорректированной классификацией
    """
    adjusted_label = base_label
    adjustment_applied = False
    
    # Если балл риска >= 4, повышаем категорию
    if risk_score >= 4:
        if base_label == "Category I":
            adjusted_label = "Category II"
            adjustment_applied = True
        elif base_label == "Category II":
            adjusted_label = "Category III"
            adjustment_applied = True
    
    # Код для категории
    code_map = {
        "Category I": 0,
        "Category II": 1,
        "Category III": 2
    }
    
    return {
        "original_label": base_label,
        "adjusted_label": adjusted_label,
        "code": code_map.get(adjusted_label, 0),
        "adjustment_applied": adjustment_applied,
        "risk_score": risk_score,
        "adjustment_reason": f"Высокий балл риска анамнеза ({risk_score})" if adjustment_applied else None
    }


def get_active_risk_factors(risk_factors: Dict[str, bool]) -> list:
    """
    Получение списка активных факторов риска
    
    Возвращает список названий активных факторов
    """
    factor_names = {
        "diabetes": "Сахарный диабет",
        "anemia": "Анемия",
        "hypertension": "Хроническая гипертония",
        "preeclampsia": "Преэклампсия",
        "infections": "Инфекционные заболевания",
        "multiple": "Многоплодная беременность",
        "placenta": "Патологии плаценты и пуповины",
        "term": "Нарушение срока беременности"
    }
    
    active = []
    for key, value in risk_factors.items():
        if value and key in factor_names:
            active.append({
                "factor": factor_names[key],
                "score": RISK_SCORES.get(key, 0)
            })
    
    return active

