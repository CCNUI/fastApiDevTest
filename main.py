# main.py
import sys
import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, Teacher as TeacherModel, Student as StudentModel, MFARequestLog as MFARequestLogModel
from schemas import TeacherCreate, Teacher, StudentCreate, Student, MFARequestLogCreate, MFARequestLog
from datetime import datetime
import time
import hmac
import base64
import struct
import hashlib

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

MFA_SECRET = os.environ.get("MFA_SECRET")
if not MFA_SECRET:
    raise ValueError("MFA_SECRET environment variable not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI()

version = f"{sys.version_info.major}.{sys.version_info.minor}"

def get_totp_token(secret, interval=30):
    key = base64.b32decode(secret, True)
    msg = struct.pack(">Q", int(time.time()) // interval)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = h[19] & 15
    token = (struct.unpack(">I", h[o:o + 4])[0] & 0x7fffffff) % 1000000
    return f"{token:06d}"

@app.get("/")
async def read_root():
    message = f"Hello world! From FastAPI running on Uvicorn with Gunicorn. Using Python {version}"
    return {"message": message}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/teachers/", response_model=Teacher)
def create_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    try:
        db_teacher = TeacherModel(name=teacher.name)
        db.add(db_teacher)
        db.commit()
        db.refresh(db_teacher)
        return Teacher.from_orm(db_teacher)
    except Exception as e:
        logging.error(f"Error creating teacher: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/teachers/", response_model=list[Teacher])
def read_teachers(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    try:
        teachers = db.query(TeacherModel).offset(skip).limit(limit).all()
        return [Teacher.from_orm(teacher) for teacher in teachers]
    except Exception as e:
        logging.error(f"Error reading teachers: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/teachers/{teacher_id}", response_model=Teacher)
def read_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(TeacherModel).filter(TeacherModel.id == teacher_id).first()
    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return Teacher.from_orm(teacher)

@app.delete("/teachers/{teacher_id}", response_model=Teacher)
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(TeacherModel).filter(TeacherModel.id == teacher_id).first()
    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    db.delete(teacher)
    db.commit()
    return Teacher.from_orm(teacher)

@app.post("/students/", response_model=Student)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    try:
        teacher = db.query(TeacherModel).filter(TeacherModel.id == student.teacher_id).first()
        if teacher is None:
            raise HTTPException(status_code=400, detail="Teacher not found")

        db_student = StudentModel(name=student.name, teacher_id=student.teacher_id)
        db.add(db_student)
        db.commit()
        db.refresh(db_student)
        return Student.from_orm(db_student)
    except Exception as e:
        logging.error(f"Error creating student: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/students/", response_model=list[Student])
def read_students(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    students = db.query(StudentModel).offset(skip).limit(limit).all()
    return [Student.from_orm(student) for student in students]

@app.get("/students/{student_id}", response_model=Student)
def read_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return Student.from_orm(student)

@app.delete("/students/{student_id}", response_model=Student)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return Student.from_orm(student)

@app.get("/mfa/")
async def get_mfa_code(request: Request, db: Session = Depends(get_db)):
    try:
        ip_address = request.client.host
        mfa_code = get_totp_token(MFA_SECRET)

        db_log = MFARequestLogModel(ip_address=ip_address)
        db.add(db_log)
        db.commit()
        db.refresh(db_log)

        return {"mfa_code": mfa_code}
    except Exception as e:
        logging.error(f"Error generating MFA code: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
