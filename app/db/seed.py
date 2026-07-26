# script designated to insert data in our database

from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from models import Base, Patient, Doctor, Appointment
from datetime import datetime

DATABASE_URL = "postgresql+psycopg2://healthuser123:healthpassword123@localhost:5432/healthdb123"

engine = create_engine(DATABASE_URL, echo=True)


def seed():
    Base.metadata.create_all(engine)  #create the tables if they don't exist

    with Session(engine) as session:

        # patients
        patient_A = Patient(name="AAAA", dob="22-11-2000")
        patient_B = Patient(name="BBBB", dob="23-12-2001")

        # doctors
        doctor_C = Doctor(name="CCCC", speciality="MBBS")
        doctor_D = Doctor(name="DDDD", speciality="Kidney Specialist")

        # appointments
        appt1 = Appointment(
            scheduled_at=datetime(2024, 1, 2, 3, 4),
            notes="Regular checkup",
            doctor=doctor_C,
            patient=patient_A,
        )

        appt2 = Appointment(
            scheduled_at=datetime(2026, 2, 3, 4, 5),
            notes="Heart checkup",
            doctor=doctor_D,
            patient=patient_B,
        )

        appt3 = Appointment(
            scheduled_at=datetime(2026, 4, 5, 7, 9),
            notes="Kidney screening",
            doctor=doctor_C,
            patient=patient_A,
        )

        session.add_all([patient_A, patient_B, doctor_C, doctor_D, appt1, appt2, appt3])  # adding objects to db
        session.commit() # flush any pending changes to the database and commit the current ongoing transaction
        print("Insertion completed")

        # fetching the data from the db uisng select, join
        stmt = (
            select(Appointment)
            .join(Appointment.doctor)
            .join(Appointment.patient)
        )
        # as ORM objects are being used, session.scalars() is ideal 
        # session.execute() - when we want the raw rows, tuples and columns
        results = session.scalars(stmt).all() 

        print("Appointments : ")

        for appt in results:
            print(f" [{appt.scheduled_at}] { appt.doctor.name} -> {appt.patient.name} | {appt.notes}")

if __name__ == "__main__":
    seed()



