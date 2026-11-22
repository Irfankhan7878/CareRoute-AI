import sys
from pathlib import Path
import datetime

# Ensure project root is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import init_db, SessionLocal
from backend.models import Department, AppointmentSlot, Patient, RoutingRecord, IntakeSession

DEPARTMENTS_DATA = [
    {
        "code": "GEN_MED",
        "name": "General Medicine",
        "description": "Comprehensive primary medical care, systemic ailments, chronic illness management, fever, infections, and general health evaluations.",
        "location": "Building A, Floor 1, Wing East",
        "operating_hours": "8:00 AM - 6:00 PM",
        "contact_phone": "Ext. 2010"
    },
    {
        "code": "ORTHO",
        "name": "Orthopaedics",
        "description": "Evaluation and management of musculoskeletal disorders, joint pain, fractures, ligament sprains, arthritis, and sports injuries.",
        "location": "Building B, Floor 2, Wing West",
        "operating_hours": "8:30 AM - 5:30 PM",
        "contact_phone": "Ext. 2020"
    },
    {
        "code": "ENT",
        "name": "ENT (Ear, Nose & Throat)",
        "description": "Diagnosis and management of disorders affecting the ear, nose, throat, sinuses, balance, and vocal cords.",
        "location": "Building A, Floor 3, Suite 302",
        "operating_hours": "9:00 AM - 5:00 PM",
        "contact_phone": "Ext. 2030"
    },
    {
        "code": "CARDIO",
        "name": "Cardiology",
        "description": "Cardiovascular evaluations, heart rhythm issues, hypertension, palpitations, and non-emergent cardiovascular care.",
        "location": "Heart Centre, Building C, Floor 1",
        "operating_hours": "8:00 AM - 6:00 PM",
        "contact_phone": "Ext. 2040"
    },
    {
        "code": "DERM",
        "name": "Dermatology",
        "description": "Skin, hair, and nail health, rashes, eczema, psoriasis, allergic skin reactions, and dermatological examinations.",
        "location": "Building A, Floor 2, Suite 210",
        "operating_hours": "9:00 AM - 4:30 PM",
        "contact_phone": "Ext. 2050"
    },
    {
        "code": "GASTRO",
        "name": "Gastroenterology",
        "description": "Digestive health, abdominal pain, reflux, liver health, bowel habit changes, and endoscopic diagnostic evaluations.",
        "location": "Building B, Floor 3, Suite 315",
        "operating_hours": "8:30 AM - 5:00 PM",
        "contact_phone": "Ext. 2060"
    },
    {
        "code": "NEURO",
        "name": "Neurology",
        "description": "Specialized assessment for chronic headaches, neuropathies, numbness, tremors, dizziness, and nervous system disorders.",
        "location": "Neurosciences Pavilion, Floor 2",
        "operating_hours": "9:00 AM - 5:00 PM",
        "contact_phone": "Ext. 2070"
    },
    {
        "code": "OPHTH",
        "name": "Ophthalmology",
        "description": "Eye health, vision changes, dry eye, eye redness, refractive assessments, and ocular health examinations.",
        "location": "Eye Centre, Building D, Floor 1",
        "operating_hours": "8:00 AM - 4:00 PM",
        "contact_phone": "Ext. 2080"
    },
    {
        "code": "PAED",
        "name": "Paediatrics",
        "description": "Dedicated care for infants, children, and adolescents under 18 years, growth tracking, vaccinations, and childhood conditions.",
        "location": "Children's Pavilion, Floor 1",
        "operating_hours": "8:00 AM - 6:00 PM",
        "contact_phone": "Ext. 2090"
    },
    {
        "code": "GYNAE",
        "name": "Gynaecology",
        "description": "Women's reproductive health, prenatal consultations, pelvic evaluations, hormonal health, and wellness screenings.",
        "location": "Women's Health Centre, Floor 3",
        "operating_hours": "8:30 AM - 5:00 PM",
        "contact_phone": "Ext. 2100"
    },
    {
        "code": "EMERG",
        "name": "Emergency Department",
        "description": "Immediate acute resuscitation and stabilization for life-threatening conditions, severe trauma, acute chest pain, and severe respiratory distress.",
        "location": "Ground Floor, Red Wing, Emergency Bay",
        "operating_hours": "Open 24/7 / 365 Days",
        "contact_phone": "Ext. 9999 / Direct Hotline: 108"
    }
]

DOCTORS_BY_DEPT = {
    "GEN_MED": ["Dr. Robert Chen, MD", "Dr. Sarah Jenkins, MD"],
    "ORTHO": ["Dr. Marcus Vance, MS Ortho", "Dr. Priya Patel, D.Ortho"],
    "ENT": ["Dr. Angela Davis, MS ENT", "Dr. Thomas Wright, MD"],
    "CARDIO": ["Dr. Elena Rostova, FACC", "Dr. David Kim, MD Cardiology"],
    "DERM": ["Dr. Claire Bennett, MD Derm", "Dr. Lucas Scott, FAAD"],
    "GASTRO": ["Dr. Michael Alvarez, FACG", "Dr. Anita Desai, DM Gastro"],
    "NEURO": ["Dr. Julian Mercer, MD Neuro", "Dr. Sophia Lee, PhD Neuro"],
    "OPHTH": ["Dr. Jonathan Pierce, FRCOphth", "Dr. Meera Iyer, MS"],
    "PAED": ["Dr. Hannah Abbott, MD Paed", "Dr. Samuel Green, FAAP"],
    "GYNAE": ["Dr. Victoria Sterling, FACOG", "Dr. Fatima Noor, MS OB/GYN"],
    "EMERG": ["Emergency Duty Physician Pool (Immediate Walk-In)"]
}

TIME_SLOTS = [
    "09:00 AM", "10:00 AM", "11:30 AM",
    "02:00 PM", "03:30 PM", "04:30 PM"
]

def seed():
    print("Initializing SQLite database tables...")
    init_db()
    db = SessionLocal()

    try:
        # 1. Seed Departments
        for dept_dict in DEPARTMENTS_DATA:
            existing = db.query(Department).filter(Department.code == dept_dict["code"]).first()
            if not existing:
                dept = Department(**dept_dict)
                db.add(dept)
        db.commit()
        print(f"Seeded {len(DEPARTMENTS_DATA)} departments.")

        # 2. Seed Appointment Slots for next 5 days
        today = datetime.date.today()
        created_slots = 0
        for i in range(1, 6):
            slot_date = (today + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            for dept_code, doctors in DOCTORS_BY_DEPT.items():
                if dept_code == "EMERG":
                    continue  # Emergency has no routine pre-booked slots
                for doctor in doctors:
                    for slot_time in TIME_SLOTS:
                        existing_slot = db.query(AppointmentSlot).filter(
                            AppointmentSlot.department_code == dept_code,
                            AppointmentSlot.date == slot_date,
                            AppointmentSlot.time_slot == slot_time,
                            AppointmentSlot.doctor_name == doctor
                        ).first()
                        if not existing_slot:
                            slot = AppointmentSlot(
                                department_code=dept_code,
                                date=slot_date,
                                time_slot=slot_time,
                                doctor_name=doctor,
                                is_available=True
                            )
                            db.add(slot)
                            created_slots += 1
        db.commit()
        print(f"Seeded {created_slots} appointment slots across next 5 days.")

        # 3. Seed Demonstration Returning Patient for Scenario 3
        demo_patient = db.query(Patient).filter(Patient.patient_id == "P-1001").first()
        if not demo_patient:
            demo_patient = Patient(
                patient_id="P-1001",
                full_name="Eleanor Vance",
                age=45
            )
            db.add(demo_patient)
            db.commit()

            # Past intake session
            past_session = IntakeSession(
                session_id="INTK-9001",
                patient_id="P-1001",
                patient_name="Eleanor Vance",
                age=45,
                described_concern="Persistent right knee swelling and stiffness after gardening",
                duration="2 weeks",
                additional_info="Prior mild osteoarthritis",
                is_returning_patient=False,
                status="ROUTED",
                created_at=datetime.datetime.utcnow() - datetime.timedelta(days=21)
            )
            db.add(past_session)

            # Past routing record
            past_routing = RoutingRecord(
                session_id="INTK-9001",
                patient_id="P-1001",
                selected_department="Orthopaedics",
                department_code="ORTHO",
                confidence_score=0.92,
                reason="Subacute joint swelling and stiffness in knee aligns with orthopaedic evaluation.",
                alternative_department="General Medicine",
                safety_status="NORMAL",
                advisory_notes="Advised bringing previous X-rays.",
                created_at=datetime.datetime.utcnow() - datetime.timedelta(days=21)
            )
            db.add(past_routing)
            db.commit()
            print("Seeded demonstration returning patient: P-1001 (Eleanor Vance).")

        print("Database seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
