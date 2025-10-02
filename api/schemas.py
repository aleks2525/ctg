from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============== Patient Schemas ==============
class PatientBase(BaseModel):
    full_name: str
    diagnosis: Optional[str] = None
    diabetes: bool = False
    anemia: bool = False
    hypertension: bool = False
    preeclampsia: bool = False
    infections: bool = False
    multiple: bool = False
    placenta: bool = False
    term: bool = False


class PatientCreate(PatientBase):
    pass


class PatientUpdate(PatientBase):
    full_name: Optional[str] = None


class PatientResponse(PatientBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_session: Optional[str] = None
    sessions: List["CTGSessionResponse"] = []
    
    class Config:
        from_attributes = True


# ============== CTG Session Schemas ==============
class CTGSessionBase(BaseModel):
    patient_id: int


class CTGSessionCreate(CTGSessionBase):
    pass


class CTGSessionResponse(BaseModel):
    id: int
    patient_id: int
    session_date: datetime
    fhr_file_path: Optional[str] = None
    uc_file_path: Optional[str] = None
    baseline_fhr: Optional[float] = None
    variability: Optional[float] = None
    accelerations_count: int = 0
    decelerations_count: int = 0
    status: Optional[str] = None
    figo_result: Optional[Dict[str, Any]] = None
    nichd_result: Optional[Dict[str, Any]] = None
    ai_result: Optional[Dict[str, Any]] = None
    forecast_15min: Optional[Dict[str, Any]] = None
    forecast_30min: Optional[Dict[str, Any]] = None
    forecast_60min: Optional[Dict[str, Any]] = None
    hypoxia_risk: Optional[List[Dict[str, float]]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============== Analysis Schemas ==============
class AnalysisParams(BaseModel):
    figo_nice: bool = True
    nichd_acog: bool = True
    ai: bool = True


class AnalysisResult(BaseModel):
    session_id: int
    fhr_base: float
    variability: float
    status: str  # normal, bradycardia, tachycardia
    accelerations: int
    decelerations: int
    figo_result: Optional[Dict[str, Any]] = None
    nichd_result: Optional[Dict[str, Any]] = None
    ai_result: Optional[Dict[str, Any]] = None
    forecast_15min: Dict[str, Any]
    forecast_30min: Dict[str, Any]
    forecast_60min: Dict[str, Any]
    hypoxia_risk: List[Dict[str, float]]
    statistics: Dict[str, Any]


# ============== Report Schemas ==============
class ReportCreate(BaseModel):
    session_id: int


class ReportResponse(BaseModel):
    id: int
    patient_id: int
    session_id: int
    report_date: datetime
    report_content: Dict[str, Any]
    report_html: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============== File Upload Response ==============
class FileUploadResponse(BaseModel):
    filename: str
    file_path: str
    file_type: str  # fhr or uc
    points_count: int
    duration_seconds: float
    upload_status: str


# Rebuild models to resolve forward references
PatientResponse.model_rebuild()

