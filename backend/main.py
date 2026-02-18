from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import init_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    
    yield 
    
    close_db()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def index():
    return {"message": "Sistem çalışıyor"}