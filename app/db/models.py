from datetime import datetime
from sqlalchemy import (String, Integer, ForeignKey, DateTime, Text 
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship
)

class Base( DeclarativeBase):
    pass

class Patient(Base):
    __tablename__ = 'patients' #lowercase only

    id: Mapped[int] = mapped_column(primary_key=True) # primary key 
    name: Mapped[str] = mapped_column(String(100))  
    dob: Mapped[str] = mapped_column(String(30)) 
    # the direction has been defined ( one-to-many )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        back_populates="patient",
        lazy="selectin",
        )
    def __repr__(self):
        return f"<Patient id={self.id} name={self.name} dob={self.dob}>"


class Doctor(Base):
    __tablename__ = 'doctors'

    id: Mapped[int] = mapped_column(primary_key=True) # primary key
    name: Mapped[str] = mapped_column(String(100)) 
    speciality: Mapped[str] = mapped_column(String(100))
    # the direction has been defined(one-to-many)
    appointments: Mapped[list["Appointment"]] = relationship(
            "Appointment",
            back_populates="doctor",
            lazy="selectin",  #eager loding
            )
    def __repr__(self):
        return f"<Doctor id={self.id} Doctor's name={self.name} speciality={self.speciality}>"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True) # optional

    # Foreign keys for this table
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)

    # many-to-one sides,lazy="joined" makes it joined with other two tables
    # the direction has been defined ( many-to-one )
    # lazy="joined" automatically adds a JOIN when this relationship is accessed. ( model level decision )
    # If you also write an explicit .join() in your select statement, SQLAlchemy  ( query level decision )
    # will JOIN the same table twice — causing redundant SQL.
    # In production, either rely on lazy="joined" or write explicit joins, not both.
    # To have more control and flexibility, explicit join is preferred. 
    doctor: Mapped["Doctor"] = relationship(
        "Doctor",
        back_populates="appointments",
        lazy="joined",   # for many-to-one relationships using "joined" is ideal.
    )
    # the direction has been defined ( many-to-one )
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="appointments",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<Appointment id={self.id} at={self.scheduled_at}>"