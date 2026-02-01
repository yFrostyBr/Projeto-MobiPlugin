from fastapi import FastAPI

from app.routes.teste import router as teste_router

app = FastAPI(title="Plubin API", version="0.1.0")

app.include_router(teste_router)
