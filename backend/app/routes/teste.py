from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import Base, engine, get_db
from app.models.db_models import Dimensoes
from app.models.schemas import DimensoesCreate, DimensoesResponse

router = APIRouter(prefix="/teste", tags=["teste"])

# Cria as tabelas localmente (SQLite) na primeira importação.
Base.metadata.create_all(bind=engine)


@router.get("", response_model=DimensoesResponse)
def get_teste():
    return DimensoesResponse(id=0, largura=100.0, altura=50.0, profundidade=25.0)


@router.post("", response_model=DimensoesResponse)
def post_teste(payload: DimensoesCreate, db: Session = Depends(get_db)):
    registro = Dimensoes(
        largura=payload.largura,
        altura=payload.altura,
        profundidade=payload.profundidade,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro
