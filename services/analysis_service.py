from sqlalchemy.orm import Session
from typing import Dict, Any, List
import json

from database.models import Patient, CTGSession
from services.database_service import SessionService
from services.file_service import FileService
from ctg_analysis import figo_nice, nichd_acog, variability, hypoxia, ai_module, risk_adjustment


class AnalysisService:
    """Сервис для анализа КТГ"""
    
    @staticmethod
    def analyze_ctg_session(
        db: Session,
        session: CTGSession,
        patient: Patient,
        use_figo: bool = True,
        use_nichd: bool = True,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Полный анализ КТГ сессии
        
        Включает:
        - Расчет базовых метрик (baseline FHR, вариабельность)
        - Определение статуса (норма/брадикардия/тахикардия)
        - Подсчет акселераций и децелераций
        - Классификацию по FIGO/NICE (если включено)
        - Классификацию по NICHD/ACOG (если включено)
        - Прогноз с ИИ (если включено)
        - Расчет риска гипоксии
        """
        
        try:
            # Загрузка данных из файлов
            fhr_data = FileService.read_csv_data(session.fhr_file_path)
            uc_data = FileService.read_csv_data(session.uc_file_path)
            
            if not fhr_data or not uc_data:
                raise ValueError("Не удалось загрузить данные из файлов")
                
        except Exception as e:
            raise ValueError(f"Ошибка загрузки данных: {str(e)}")
        
        try:
            # Извлечение временных рядов
            fhr_series = [point['value'] for point in fhr_data]
            uc_series = [point['value'] for point in uc_data]
            time_series = [point['time'] for point in fhr_data]
            
            # 1. Расчет базовых метрик
            from ctg_analysis.common import calc_baseline, detect_accelerations, detect_decelerations
            
            baseline_fhr = calc_baseline(fhr_series)
            variability_value = variability.calculate_variability(fhr_series)
            accelerations = detect_accelerations(fhr_series, baseline_fhr)
            decelerations = detect_decelerations(fhr_series, baseline_fhr)
            
            # 2. Определение статуса
            status = AnalysisService._determine_status(baseline_fhr)
            
        except Exception as e:
            raise ValueError(f"Ошибка расчета базовых метрик: {str(e)}")
        
        # 3. Подготовка факторов риска пациентки
        # patient может быть как объектом SQLAlchemy, так и словарем
        if isinstance(patient, dict):
            risk_factors = {
                "diabetes": patient.get("diabetes", False),
                "anemia": patient.get("anemia", False),
                "hypertension": patient.get("hypertension", False),
                "preeclampsia": patient.get("preeclampsia", False),
                "infections": patient.get("infections", False),
                "multiple": patient.get("multiple", False),
                "placenta": patient.get("placenta", False),
                "term": patient.get("term", False)
            }
        else:
            risk_factors = {
                "diabetes": patient.diabetes,
                "anemia": patient.anemia,
                "hypertension": patient.hypertension,
                "preeclampsia": patient.preeclampsia,
                "infections": patient.infections,
                "multiple": patient.multiple,
                "placenta": patient.placenta,
                "term": patient.term
            }
        
        risk_score = risk_adjustment.calculate_risk_score(risk_factors)
        
        try:
            # 4. Классификация по FIGO/NICE
            figo_result = None
            if use_figo:
                figo_result = figo_nice.classify_figo(fhr_series, risk_factors)
            
            # 5. Классификация по NICHD/ACOG
            nichd_result = None
            if use_nichd:
                nichd_result = nichd_acog.classify_nichd(fhr_series, risk_factors)
            
            # 6. ИИ прогноз
            ai_result = None
            if use_ai:
                ai_result = ai_module.predict_outcomes(fhr_series, uc_series, risk_factors)
            
            # 7. Расчет риска гипоксии
            hypoxia_risk = hypoxia.calculate_hypoxia_risk(
                fhr_series=fhr_series,
                uc_series=uc_series,
                variability_value=variability_value,
                time_series=time_series
            )
            
        except Exception as e:
            # Устанавливаем значения по умолчанию при ошибке
            figo_result = {"category": "Ошибка", "confidence": 0.0, "details": f"Ошибка: {str(e)}"}
            nichd_result = {"category": "Ошибка", "confidence": 0.0, "details": f"Ошибка: {str(e)}"}
            ai_result = {"15min": "Ошибка", "30min": "Ошибка", "60min": "Ошибка"}
            hypoxia_risk = [{"time": 0, "risk": 0.0, "level": "Ошибка"}]
        
        try:
            # 8. Формирование прогнозов с учетом риска гипоксии
            forecast_15min = AnalysisService._generate_forecast_with_hypoxia_risk(
                figo_result, nichd_result, ai_result, hypoxia_risk, "15min"
            )
            forecast_30min = AnalysisService._generate_forecast_with_hypoxia_risk(
                figo_result, nichd_result, ai_result, hypoxia_risk, "30min"
            )
            forecast_60min = AnalysisService._generate_forecast_with_hypoxia_risk(
                figo_result, nichd_result, ai_result, hypoxia_risk, "60min"
            )
            
        except Exception as e:
            # Устанавливаем прогнозы по умолчанию при ошибке
            forecast_15min = {"prediction": "Ошибка", "confidence": 0.0, "hypoxia_risk": 0.0}
            forecast_30min = {"prediction": "Ошибка", "confidence": 0.0, "hypoxia_risk": 0.0}
            forecast_60min = {"prediction": "Ошибка", "confidence": 0.0, "hypoxia_risk": 0.0}
        
        # 9. Формирование результата
        analysis_result = {
            "session_id": session.id,
            "fhr_base": baseline_fhr,
            "variability": variability_value,
            "status": status,
            "accelerations": accelerations,
            "decelerations": decelerations,
            "figo_result": figo_result,
            "nichd_result": nichd_result,
            "ai_result": ai_result,
            "forecast_15min": forecast_15min,
            "forecast_30min": forecast_30min,
            "forecast_60min": forecast_60min,
            "hypoxia_risk": hypoxia_risk,
            "statistics": {
                "accelerations": accelerations,
                "decelerations": decelerations,
                "variability": variability_value,
                "baseline_fhr": baseline_fhr,
                "risk_score": risk_score
            }
        }
        
        # 10. Сохранение результатов в БД
        SessionService.update_session_analysis(db, session.id, analysis_result)
        
        return analysis_result
    
    @staticmethod
    def _determine_status(baseline_fhr: float) -> str:
        """
        Определение статуса по базовому ритму
        
        - Норма: 110-160 уд/мин
        - Брадикардия: < 110 уд/мин
        - Тахикардия: > 160 уд/мин
        """
        if baseline_fhr < 110:
            return "bradycardia"
        elif baseline_fhr > 160:
            return "tachycardia"
        else:
            return "normal"
    
    @staticmethod
    def _generate_forecast_with_hypoxia_risk(
        figo_result: Dict,
        nichd_result: Dict,
        ai_result: Dict,
        hypoxia_risk: List[Dict],
        timeframe: str
    ) -> Dict[str, str]:
        """
        Генерация прогноза с учетом риска гипоксии для разных временных интервалов
        """
        # Получаем текущий риск гипоксии (последнее значение)
        current_hypoxia_risk = 0.0
        if hypoxia_risk and len(hypoxia_risk) > 0:
            current_hypoxia_risk = hypoxia_risk[-1].get('risk', 0.0)
        
        
        # Рассчитываем прогнозируемый риск для разных временных интервалов
        predicted_risk = AnalysisService._predict_hypoxia_risk_for_timeframe(
            current_hypoxia_risk, hypoxia_risk, timeframe
        )
        
        # Базовые прогнозы от модулей
        forecasts = []
        
        # Прогноз от FIGO/NICE
        if figo_result:
            forecast_text = f"FIGO/NICE: {figo_result.get('label', 'Unknown')}"
            forecasts.append(forecast_text)
        
        # Прогноз от NICHD/ACOG
        if nichd_result:
            forecast_text = f"NICHD/ACOG: {nichd_result.get('label', 'Unknown')}"
            forecasts.append(forecast_text)
        
        # Прогноз от ИИ
        if ai_result and timeframe in ai_result:
            forecast_text = f"ИИ: {ai_result[timeframe].get('prediction', 'Unknown')}"
            forecasts.append(forecast_text)
        
        # Добавляем прогноз риска гипоксии
        hypoxia_text = AnalysisService._format_hypoxia_risk_prediction(predicted_risk, timeframe)
        forecasts.append(f"Риск гипоксии: {hypoxia_text}")
        
        # Определение статуса с учетом риска гипоксии
        status = AnalysisService._determine_forecast_status(
            figo_result, nichd_result, ai_result, predicted_risk, timeframe
        )
        
        result = {
            "status": status,
            "text": " | ".join(forecasts) if forecasts else "Нет данных",
            "hypoxia_risk": predicted_risk
        }
        
        
        return result
    
    @staticmethod
    def _predict_hypoxia_risk_for_timeframe(
        current_risk: float,
        hypoxia_risk_history: List[Dict],
        timeframe: str
    ) -> float:
        """
        Прогнозирование риска гипоксии для конкретного временного интервала
        """
        if not hypoxia_risk_history or len(hypoxia_risk_history) < 2:
            return current_risk
        
        # Анализируем тренд риска
        recent_risks = [point['risk'] for point in hypoxia_risk_history[-10:]]  # Последние 10 точек
        trend = AnalysisService._calculate_risk_trend(recent_risks)
        
        # Прогнозируем риск в зависимости от временного интервала
        if timeframe == "15min":
            # Для 15 минут - небольшое изменение
            time_multiplier = 1.1
        elif timeframe == "30min":
            # Для 30 минут - умеренное изменение
            time_multiplier = 1.3
        else:  # 60min+
            # Для 60+ минут - значительное изменение
            time_multiplier = 1.6
        
        # Применяем тренд и временной множитель
        predicted_risk = current_risk * (1 + trend * time_multiplier)
        
        # Ограничиваем диапазон [0, 1]
        return max(0.0, min(1.0, predicted_risk))
    
    @staticmethod
    def _calculate_risk_trend(risk_values: List[float]) -> float:
        """
        Расчет тренда изменения риска
        Возвращает значение от -1 (снижение) до +1 (рост)
        """
        if len(risk_values) < 2:
            return 0.0
        
        # Простой линейный тренд
        n = len(risk_values)
        x = list(range(n))
        y = risk_values
        
        # Коэффициент корреляции
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        if n * sum_x2 - sum_x ** 2 == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        # Нормализуем к диапазону [-1, 1]
        return max(-1.0, min(1.0, slope * 10))
    
    @staticmethod
    def _format_hypoxia_risk_prediction(risk: float, timeframe: str) -> str:
        """
        Форматирование прогноза риска гипоксии
        """
        risk_percent = int(risk * 100)
        
        if risk < 0.3:
            level = "низкий"
        elif risk < 0.6:
            level = "умеренный"
        else:
            level = "высокий"
        
        return f"{risk_percent}% ({level})"
    
    @staticmethod
    def _determine_forecast_status(
        figo_result: Dict,
        nichd_result: Dict,
        ai_result: Dict,
        hypoxia_risk: float,
        timeframe: str
    ) -> str:
        """
        Определение статуса прогноза с учетом риска гипоксии
        """
        # Базовый статус от модулей
        base_status = 'normal'
        
        if ai_result and timeframe in ai_result:
            base_status = ai_result[timeframe].get('status', 'normal')
        elif figo_result and figo_result.get('code', 0) >= 2:
            base_status = 'danger'
        elif nichd_result and nichd_result.get('code', 0) >= 2:
            base_status = 'danger'
        elif figo_result and figo_result.get('code', 0) == 1:
            base_status = 'warning'
        elif nichd_result and nichd_result.get('code', 0) == 1:
            base_status = 'warning'
        
        # Корректировка с учетом риска гипоксии
        if hypoxia_risk > 0.7:
            return 'danger'
        elif hypoxia_risk > 0.4:
            if base_status == 'normal':
                return 'warning'
            else:
                return base_status
        else:
            return base_status
    
    @staticmethod
    def get_detailed_statistics(db: Session, session: CTGSession) -> Dict[str, Any]:
        """
        Получение подробной статистики для модального окна
        """
        # Проверяем наличие сохраненных результатов
        statistics = {
            "accelerations": session.accelerations_count,
            "decelerations": session.decelerations_count,
            "variability": session.variability,
            "baseline_fhr": session.baseline_fhr,
            "status": session.status
        }
        
        # Добавляем источники данных
        sources = []
        
        if session.figo_result:
            figo_data = json.loads(session.figo_result)
            sources.append({
                "module": "FIGO/NICE",
                "data": figo_data
            })
        
        if session.nichd_result:
            nichd_data = json.loads(session.nichd_result)
            sources.append({
                "module": "NICHD/ACOG",
                "data": nichd_data
            })
        
        if session.ai_result:
            ai_data = json.loads(session.ai_result)
            sources.append({
                "module": "ИИ модуль",
                "data": ai_data
            })
        
        statistics["sources"] = sources
        
        return statistics

