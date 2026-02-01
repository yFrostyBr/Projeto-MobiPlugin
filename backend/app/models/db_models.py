from sqlalchemy import Column, Float, Integer

from app.db.database import Base


class Dimensoes(Base):
    __tablename__ = "dimensoes"

    id = Column(Integer, primary_key=True, index=True)
    largura = Column(Float, nullable=False)
    altura = Column(Float, nullable=False)
    profundidade = Column(Float, nullable=False)
