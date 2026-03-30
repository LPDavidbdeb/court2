from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from core.schemas import ProducedExhibitSchema # Importing the correctly mapped schema

class LegalCaseSchema(BaseModel):
    id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True

class AISuggestionSchema(BaseModel):
    id: int
    created_at: datetime
    model_version: str
    content: dict
    parsing_success: bool
    
    class Config:
        from_attributes = True

class PerjuryContestationSchema(BaseModel):
    id: int
    case_id: int
    title: str
    final_sec1_declaration: str
    final_sec2_proof: str
    final_sec3_mens_rea: str
    final_sec4_intent: str
    updated_at: datetime
    police_report_data: dict
    police_report_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class LegalCaseDetailSchema(LegalCaseSchema):
    contestations: List[PerjuryContestationSchema]
    produced_exhibits: List[ProducedExhibitSchema]
