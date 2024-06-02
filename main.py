import sys
import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Request
from game_app import game_app  # 导入游戏子应用
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, Teacher as TeacherModel, Student as StudentModel, MFARequestLog as MFARequestLogModel
from schemas import TeacherCreate, Teacher, StudentCreate, Student
import pyotp
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
MFA_SECRET = os.environ.get("MFA_SECRET")
if not DATABASE_URL or not MFA_SECRET:
    raise ValueError("DATABASE_URL and MFA_SECRET environment variables must be set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI()

version = f"{sys.version_info.major}.{sys.version_info.minor}"


def get_totp_token(secret):
    totp = pyotp.TOTP(secret)
    return totp.now()


@app.get("/")
async def read_root():
    message = f"Hello world! From FastAPI running on Uvicorn with Gunicorn. Using Python {version}"
    return {"message": message}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

# 将游戏子应用挂载到主应用的 `/game` 路径下
app.mount("/game", game_app)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# MFA Endpoints
@app.get("/mfa/")
async def get_mfa_code(request: Request, db: Session = Depends(get_db)):
    try:
        ip_address = request.client.host
        mfa_code = get_totp_token(MFA_SECRET)
        timestamp = datetime.utcnow()

        db_log = MFARequestLogModel(ip_address=ip_address, mfa_code=mfa_code, timestamp=timestamp)
        db.add(db_log)
        db.commit()
        db.refresh(db_log)

        return {"mfa_code": mfa_code, "timestamp": timestamp}
    except Exception as e:
        logging.error(f"Error generating MFA code: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/verify-mfa/")
async def verify_mfa_code(client_mfa_code: str, request: Request, db: Session = Depends(get_db)):
    try:
        ip_address = request.client.host
        current_mfa_code = get_totp_token(MFA_SECRET)
        verified = client_mfa_code == current_mfa_code
        timestamp = datetime.utcnow()

        db_log = MFARequestLogModel(ip_address=ip_address, mfa_code=current_mfa_code, verified=verified,
                                    client_mfa_code=client_mfa_code, timestamp=timestamp)
        db.add(db_log)
        db.commit()
        db.refresh(db_log)

        return {"verified": verified, "timestamp": timestamp, "current_mfa_code": current_mfa_code,
                "client_mfa_code": client_mfa_code}
    except Exception as e:
        logging.error(f"Error verifying MFA code: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# Teacher CRUD
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)