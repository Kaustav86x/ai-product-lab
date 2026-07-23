import enum
from typing import Optional, Annotated
from pydantic import BaseModel, BeforeValidator, ValidationError, model_validator
from app.schemas.enums import PatientStatus


def age_validator(age : int) -> int:
    if age < 0:
        raise ValueError("Age must be a non-negative integer.")
    return age

class Patient(BaseModel):
    age: Annotated[int, BeforeValidator(age_validator)]   # using BeforeValidator to validate age before assignment
    status: PatientStatus
    height: Optional[float] = None
    discharged: bool

    @model_validator(mode='after')
    def patient_status_validation(self):
        if(self.status == PatientStatus.ACTIVE): 
            self.discharged = False
        return self

patient = Patient(age=39, status="ACTIVE", discharged=False)   # fields explictly provided during instantiation
print(patient.model_fields_set)  # value of age variable will be excluded unless we mention exclude_unset = True

print(patient.model_dump(exclude_unset=True))  # will give {'age': 39}

try:
    pat = Patient.model_validate({'age': 25, 'status': 'active', 'height': 175.5})   
    print(pat.model_dump(mode='json'))         # mode is set to JSON for JSON compatiable types
except ValidationError as e:    # throws an error if 'active' is not a valid enum value for status
    print(e)                