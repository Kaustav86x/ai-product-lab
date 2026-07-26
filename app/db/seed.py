# script designated to insert data in our database

from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from app.db.models import Base, Patient, Doctor, Appointment
from datetime import datetime

DATABASE_URL = "postgresql+psycopg2://healthuser:healthpass@localhost:5432/healthdb"

engine = create_engine(DATABASE_URL, echo=True)


def seed():
    Base.metadata.create_all(engine)  #create the tables if they don't exist

    with Session(engine) as session:

        # patients
        patient_A = Patient(name="AAAA", dob="22-11-2000")
        patient_B = Patient(name="BBBB", dob="23-12-2001")

        # doctors
        doctor_C = Doctor(name="CCCC", dob="12-02-1980")
        doctor_D = Doctor(name="DDDD", dob="13-04-1981")

        # appointments
        appt1 = Appointment(
            scheduled_at=datetime(2024, 1, 2, 3, 4),
            notes="Regular checkup",
            doctor="CCCC",
            patient="BBBB",
        )

        appt2 = Appointment(
            scheduled_at=datetime(2026, 2, 3, 4, 5),
            notes="Heart checkup",
            doctor="DDDD",
            patient="AAAA",
        )

        appt3 = Appointment(
            scheduled_at=datetime(2026, 4, 5, 7, 9),
            notes="Kidney screening",
            doctor="CCCC",
            patient="AAAA",
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
        results = session.scalars(stmt).all() # as ORM objects are being used, session.scalars() is ideal or session.execute() - when we want the raw rows, tuples and columns

        print("Appointments : ")

        for appt in results:
            print(f" [{appt.scheduled_at}] { appt.doctor.name} -> {appt.patient.name} | {appt.notes}")

if __name__ == "__main__":
    seed()



