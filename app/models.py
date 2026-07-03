from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(String, unique=True, index=True, nullable=False)
    student_name = Column(String, nullable=False)
    student_email = Column(String, nullable=False)
    achievement = Column(String, nullable=False)
    organization_name = Column(String, nullable=False)
    event_name = Column(String, nullable=False)
    certificate_code = Column(String, unique=True, nullable=False)
    qr_code_path = Column(String)
    certificate_file_path = Column(String)
    issued_date = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=False)
