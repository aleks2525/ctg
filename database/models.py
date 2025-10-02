from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./ctg_database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True, nullable=False)
    diagnosis = Column(Text, nullable=True)
    
    # Векторы анамнеза (факторы риска)
    diabetes = Column(Boolean, default=False)
    anemia = Column(Boolean, default=False)
    hypertension = Column(Boolean, default=False)
    preeclampsia = Column(Boolean, default=False)
    infections = Column(Boolean, default=False)
    multiple = Column(Boolean, default=False)
    placenta = Column(Boolean, default=False)
    term = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    sessions = relationship("CTGSession", back_populates="patient", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="patient", cascade="all, delete-orphan")


class CTGSession(Base):
    __tablename__ = "ctg_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    session_date = Column(DateTime, default=datetime.utcnow)
    
    # Пути к загруженным файлам
    fhr_file_path = Column(String, nullable=True)
    uc_file_path = Column(String, nullable=True)
    
    # Результаты анализа - базовые метрики
    baseline_fhr = Column(Float, nullable=True)
    variability = Column(Float, nullable=True)
    accelerations_count = Column(Integer, default=0)
    decelerations_count = Column(Integer, default=0)
    
    # Статус КТГ (normal, bradycardia, tachycardia)
    status = Column(String, nullable=True)
    
    # Результаты классификаций (JSON)
    figo_result = Column(Text, nullable=True)
    nichd_result = Column(Text, nullable=True)
    ai_result = Column(Text, nullable=True)
    
    # Прогнозы (JSON)
    forecast_15min = Column(Text, nullable=True)
    forecast_30min = Column(Text, nullable=True)
    forecast_60min = Column(Text, nullable=True)
    
    # Риск гипоксии (JSON array)
    hypoxia_risk = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Отношения
    patient = relationship("Patient", back_populates="sessions")
    report = relationship("Report", back_populates="session", uselist=False, cascade="all, delete-orphan")


class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("ctg_sessions.id"), nullable=False)
    
    report_date = Column(DateTime, default=datetime.utcnow)
    report_content = Column(Text, nullable=False)  # JSON с полным отчетом
    report_html = Column(Text, nullable=True)  # HTML версия отчета
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Отношения
    patient = relationship("Patient", back_populates="reports")
    session = relationship("CTGSession", back_populates="report")


def init_db():
    """Инициализация базы данных"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Получение сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

