import sys
from fastapi import FastAPI
from app.api.routes import router



app = FastAPI(title="SQL Agent")

app.include_router(router)