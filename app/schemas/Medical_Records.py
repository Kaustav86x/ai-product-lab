from typing import Optional
from pydantic import BaseModel

from app.schemas.Patients import Patient  # importing the Patient schema from Patients.py

class MedicalRecord(BaseModel):
    patient: Patient                      # using the Patient schema as a field in the MedicalRecord schema
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
