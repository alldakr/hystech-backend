# -*- coding: utf-8 -*-
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session


# PostgreSQL 연결 정보
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_DB = "postgres"
POSTGRES_HOST = "192.168.56.100"
POSTGRES_PORT = "5432"

# PostgreSQL 연결 URL
SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# SQLAlchemy 엔진 생성
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# SQLAlchemy 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy Base 모델 생성
Base = declarative_base()

# FastAPI 애플리케이션 생성
app = FastAPI()


# 데이터베이스 세션 주입 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestModel(Base):
    __tablename__ = "tb_test"

    title = Column(String, primary_key=True)
    message = Column(String)


class InsertRequest(BaseModel):
    title: str
    message: str


@app.get("/")
async def root():
    return {"title": "Hello World", "body": "This is Body"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.post("/insert")
def insert_data(request: InsertRequest, db: Session = Depends(get_db)):
    title = request.title
    message = request.message

    test_data = TestModel(title=title, message=message)

    db.add(test_data)
    db.commit()
    return {"message": "Data inserted successfully"}


# CORS middleware를 추가하지 않음으로써 CORS를 비활성화합니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, log_level="info")
