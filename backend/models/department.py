from sqlalchemy import Column, String, Integer, Text
from backend.database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(100), nullable=False)
    operating_hours = Column(String(100), default="8:00 AM - 6:00 PM")
    contact_phone = Column(String(50), default="Ext. 2000")
