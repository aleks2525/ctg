from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import json

from database.models import Report, CTGSession, Patient
from services.database_service import PatientService


class ReportService:
    """Сервис для работы с отчетами"""
    
    @staticmethod
    def generate_report(db: Session, session: CTGSession) -> Report:
        """Генерация отчета по результатам КТГ"""
        
        # Получение пациентки
        patient = PatientService.get_patient_by_id(db, session.patient_id)
        
        # Формирование содержимого отчета
        report_content = {
            "patient_name": patient.full_name,
            "patient_diagnosis": patient.diagnosis,
            "session_date": session.session_date.strftime("%d.%m.%Y %H:%M"),
            "baseline_fhr": session.baseline_fhr,
            "variability": session.variability,
            "accelerations": session.accelerations_count,
            "decelerations": session.decelerations_count,
            "status": session.status,
            "risk_factors": {
                "diabetes": patient.diabetes,
                "anemia": patient.anemia,
                "hypertension": patient.hypertension,
                "preeclampsia": patient.preeclampsia,
                "infections": patient.infections,
                "multiple": patient.multiple,
                "placenta": patient.placenta,
                "term": patient.term
            }
        }
        
        # Добавление результатов классификаций
        if session.figo_result:
            report_content["figo_classification"] = json.loads(session.figo_result)
        
        if session.nichd_result:
            report_content["nichd_classification"] = json.loads(session.nichd_result)
        
        if session.ai_result:
            report_content["ai_prediction"] = json.loads(session.ai_result)
        
        # Добавление прогнозов
        if session.forecast_15min:
            report_content["forecast_15min"] = json.loads(session.forecast_15min)
        if session.forecast_30min:
            report_content["forecast_30min"] = json.loads(session.forecast_30min)
        if session.forecast_60min:
            report_content["forecast_60min"] = json.loads(session.forecast_60min)
        
        # Генерация HTML версии
        report_html = ReportService._generate_html_report(report_content)
        
        # Создание записи в БД
        db_report = Report(
            patient_id=session.patient_id,
            session_id=session.id,
            report_content=json.dumps(report_content, ensure_ascii=False),
            report_html=report_html
        )
        
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        return db_report
    
    @staticmethod
    def get_report_by_id(db: Session, report_id: int) -> Optional[Report]:
        """Получение отчета по ID"""
        return db.query(Report).filter(Report.id == report_id).first()
    
    @staticmethod
    def get_report_by_session(db: Session, session_id: int) -> Optional[Report]:
        """Получение отчета по сессии"""
        return db.query(Report).filter(Report.session_id == session_id).first()
    
    @staticmethod
    def get_reports_by_patient(db: Session, patient_id: int) -> List[Report]:
        """Получение всех отчетов пациентки"""
        return db.query(Report).filter(
            Report.patient_id == patient_id
        ).order_by(Report.report_date.desc()).all()
    
    @staticmethod
    def _generate_html_report(content: dict) -> str:
        """Генерация HTML версии отчета"""
        
        status_text = {
            "normal": "Норма",
            "bradycardia": "Брадикардия",
            "tachycardia": "Тахикардия"
        }
        
        html = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>Отчет КТГ - {content['patient_name']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .header {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px 20px; }}
                .label {{ font-weight: bold; }}
                .status {{ padding: 5px 10px; border-radius: 3px; display: inline-block; }}
                .status-normal {{ background: #4caf50; color: white; }}
                .status-warning {{ background: #ff9800; color: white; }}
                .status-danger {{ background: #f44336; color: white; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Отчет анализа кардиотокограммы (КТГ)</h1>
                <p><strong>Пациентка:</strong> {content['patient_name']}</p>
                <p><strong>Дата обследования:</strong> {content['session_date']}</p>
                {f"<p><strong>Диагноз:</strong> {content['patient_diagnosis']}</p>" if content.get('patient_diagnosis') else ""}
            </div>
            
            <div class="section">
                <h2>Основные показатели</h2>
                <div class="metric">
                    <span class="label">Базовый ритм:</span> {content['baseline_fhr']:.1f} уд/мин
                </div>
                <div class="metric">
                    <span class="label">Вариабельность:</span> {content['variability']:.1f} мс
                </div>
                <div class="metric">
                    <span class="label">Статус:</span> 
                    <span class="status status-{'normal' if content['status'] == 'normal' else 'warning'}">
                        {status_text.get(content['status'], content['status'])}
                    </span>
                </div>
            </div>
            
            <div class="section">
                <h2>Статистика КТГ</h2>
                <div class="metric">
                    <span class="label">Акселерации:</span> {content['accelerations']}
                </div>
                <div class="metric">
                    <span class="label">Децелерации:</span> {content['decelerations']}
                </div>
            </div>
            
            {ReportService._generate_classification_section(content)}
            
            {ReportService._generate_forecast_section(content)}
            
            <div class="section">
                <h2>Факторы риска</h2>
                {ReportService._generate_risk_factors_html(content.get('risk_factors', {}))}
            </div>
            
            <div class="section" style="margin-top: 40px; font-size: 12px; color: #666;">
                <p>Отчет сгенерирован: {datetime.now().strftime("%d.%m.%Y %H:%M")}</p>
                <p>Программный комплекс анализа КТГ - ИТЭЛМА</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    @staticmethod
    def _generate_classification_section(content: dict) -> str:
        """Генерация секции с классификациями"""
        html = '<div class="section"><h2>Результаты классификаций</h2>'
        
        if 'figo_classification' in content:
            figo = content['figo_classification']
            html += f"""
            <h3>FIGO/NICE классификация</h3>
            <p><strong>Результат:</strong> {figo.get('label', 'N/A')}</p>
            """
        
        if 'nichd_classification' in content:
            nichd = content['nichd_classification']
            html += f"""
            <h3>NICHD/ACOG классификация</h3>
            <p><strong>Результат:</strong> {nichd.get('label', 'N/A')}</p>
            """
        
        html += '</div>'
        return html
    
    @staticmethod
    def _generate_forecast_section(content: dict) -> str:
        """Генерация секции с прогнозами"""
        html = '<div class="section"><h2>Прогнозы</h2>'
        
        if 'forecast_15min' in content:
            html += f"<p><strong>15 минут:</strong> {content['forecast_15min'].get('text', 'N/A')}</p>"
        
        if 'forecast_30min' in content:
            html += f"<p><strong>30 минут:</strong> {content['forecast_30min'].get('text', 'N/A')}</p>"
        
        if 'forecast_60min' in content:
            html += f"<p><strong>60+ минут:</strong> {content['forecast_60min'].get('text', 'N/A')}</p>"
        
        html += '</div>'
        return html
    
    @staticmethod
    def _generate_risk_factors_html(risk_factors: dict) -> str:
        """Генерация HTML для факторов риска"""
        factor_names = {
            "diabetes": "Сахарный диабет",
            "anemia": "Анемия",
            "hypertension": "Хроническая гипертония",
            "preeclampsia": "Преэклампсия",
            "infections": "Инфекционные заболевания",
            "multiple": "Многоплодная беременность",
            "placenta": "Патологии плаценты",
            "term": "Нарушение срока беременности"
        }
        
        active_factors = [
            factor_names[key] for key, value in risk_factors.items()
            if value and key in factor_names
        ]
        
        if active_factors:
            return "<ul>" + "".join([f"<li>{factor}</li>" for factor in active_factors]) + "</ul>"
        else:
            return "<p>Нет выявленных факторов риска</p>"

