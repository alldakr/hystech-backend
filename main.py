# -*- coding: utf-8 -*-
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict

from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import logging


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


# 연결된 클라이언트 소켓 저장
connected_clients: Dict[str, WebSocket] = {}

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


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()

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


# 로그 설정
logging.basicConfig(level=logging.INFO)
connected_clients_ai= {}
@app.websocket("/ws/ai_server")
async def websocket_ai_server(websocket: WebSocket, client_id: str = 'ai_server'):
    connected_clients_ai[client_id] = websocket
    await websocket.accept()
    logging.info(f"Client {client_id} connected to /ws/ai_server")

    try:
        while True:
            data = await websocket.receive_text()
            logging.info(f"Received data from {client_id} (ai_server): {data}")
            
            # /ws/front에 연결된 모든 클라이언트에게 데이터 전송
            for cid, ws in connected_clients_front.items():
                await ws.send_text(f"Message from AI Server ({client_id}): {data}")

    except WebSocketDisconnect:
        del connected_clients_ai[client_id]
        logging.info(f"Client {client_id} disconnected from /ws/ai_server")
        
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        del connected_clients_ai[client_id]


# /ws/front 엔드포인트
connected_clients_front = {}
@app.websocket("/ws/front")
async def websocket_front(websocket: WebSocket, client_id: str = 'front'):
    connected_clients_front[client_id] = websocket
    await websocket.accept()
    logging.info(f"Client {client_id} connected to /ws/front")

    try:
        while True:
            data = await websocket.receive_text()
            logging.info(f"Received data from {client_id} (front): {data}")

            # 필요시 추가 처리 로직 (예: 다른 front 클라이언트에게 전송)

    except WebSocketDisconnect:
        del connected_clients_front[client_id]
        logging.info(f"Client {client_id} disconnected from /ws/front")
        
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        del connected_clients_front[client_id]


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
