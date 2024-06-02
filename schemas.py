# schemas.py
from pydantic import BaseModel
from datetime import datetime

class TeacherBase(BaseModel):
    name: str

class TeacherCreate(TeacherBase):
    pass

class Teacher(TeacherBase):
    id: int

    class Config:
        orm_mode = True

class StudentBase(BaseModel):
    name: str
    teacher_id: int

class StudentCreate(StudentBase):
    pass

class Student(StudentBase):
    id: int

    class Config:
        orm_mode = True

class MFARequestLogBase(BaseModel):
    ip_address: str
    mfa_code: str
    verified: bool = False
    client_mfa_code: str = None

class MFARequestLogCreate(MFARequestLogBase):
    pass

class MFARequestLog(MFARequestLogBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True
