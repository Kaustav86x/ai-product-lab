import enum
from typing import Optional, Annotated
from pydantic import BaseModel, BeforeValidator, ValidationError, model_validator
from app.schemas.enums import PatientStatus

# guarding the age against non-interger inputs
def age_validator(age) -> int:
    if not isinstance(age, (int, float)):
        raise ValueError(f"Age must be a number, got {type(age).__name__} instead")
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
        if(self.status == PatientStatus.Active): 
            self.discharged = False
        return self
    
if __name__ == "__main__":
    patient = Patient(age=39, status='active', discharged=False)   # fields explictly provided during instantiation
    print(patient.model_fields_set)  # value of age variable will be excluded unless we mention exclude_unset = True
    print(patient.model_dump(exclude_unset=True))  # will give {'age': 39}

    try:
        pat = Patient.model_validate({'age': 25, 'status': 'active', 'height': 175.5})   
        print(pat.model_dump(mode='json'))         # mode is set to JSON for JSON compatiable types
    except ValidationError as e:    # throws an error if 'active' is not a valid enum value for status
        print(e)                