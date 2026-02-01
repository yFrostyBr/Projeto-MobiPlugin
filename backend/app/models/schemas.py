from pydantic import BaseModel, Field


class DimensoesBase(BaseModel):
    largura: float = Field(..., description="Largura em mm")
    altura: float = Field(..., description="Altura em mm")
    profundidade: float = Field(..., description="Profundidade em mm")


class DimensoesCreate(DimensoesBase):
    pass


class DimensoesResponse(DimensoesBase):
    id: int

    class Config:
        from_attributes = True
