from enum import Enum

class PatientStatus(str, Enum):
    Active = "active"
    Inactive = "inactive"
    Discharged = "discharged"