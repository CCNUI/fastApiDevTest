from pydantic import BaseModel

class TeacherBase(BaseModel):
    name: str

class TeacherCreate(TeacherBase):
    pass

class Teacher(TeacherBase):
    id: int

    class Config:
        orm_mode = True  # 确保启用了 orm_mode

class StudentBase(BaseModel):
    name: str
    teacher_id: int

class StudentCreate(StudentBase):
    pass

class Student(StudentBase):
    id: int

    class Config:
        orm_mode = True  # 确保启用了 orm_mode