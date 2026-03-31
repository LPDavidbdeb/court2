from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from core.schemas import ProducedExhibitSchema

class CaseCreateSchema(BaseModel):
    title: str

class LegalCaseSchema(BaseModel):
    id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True

class ContestationCreateSchema(BaseModel):
    title: str
    final_sec1_declaration: Optional[str] = ""
    final_sec2_proof: Optional[str] = ""
    final_sec3_mens_rea: Optional[str] = ""
    final_sec4_intent: Optional[str] = ""

class PerjuryContestationSchema(BaseModel):
    id: int
    case_id: int
    title: str
    final_sec1_declaration: str
    final_sec2_proof: str
    final_sec3_mens_rea: str
    final_sec4_intent: str
    updated_at: datetime
    
    class Config:
        from_attributes = True

class LegalCaseDetailSchema(LegalCaseSchema):
    contestations: List[PerjuryContestationSchema] = []
    produced_exhibits: List[ProducedExhibitSchema] = []
