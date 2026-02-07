from pydantic import BaseModel, Field
from typing import List, Optional


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


class SketchResponse(BaseModel):
    name: str = Field("quadrado", description="Nome da forma")
    x: int = Field(10, description="Dimensão X padrão")
    y: int = Field(10, description="Dimensão Y padrão")
    z: int = Field(10, description="Dimensão Z padrão")


class SketchHeight(BaseModel):
    altura: int = Field(..., description="Altura desejada em mm")


class SketchDimensions(BaseModel):
    largura: int = Field(..., description="Largura em mm")
    altura: int = Field(..., description="Altura em mm")
    profundidade: int = Field(..., description="Profundidade em mm")


class FaceProps(BaseModel):
    name: str = Field(..., description="Face name: front, back, left, right, top, bottom")
    color: Optional[str] = Field(None, description="Color name or hex")
    material: Optional[str] = Field(None, description="Material identifier")
    thickness: Optional[float] = Field(None, description="Face thickness in mm")


class BlockDefinition(BaseModel):
    largura: float = Field(..., description="Largura do bloco em mm")
    altura: float = Field(..., description="Altura do bloco em mm")
    profundidade: float = Field(..., description="Profundidade do bloco em mm")
    faces: List[FaceProps] = Field(default_factory=list, description="Lista de propriedades por face")


class BlockResponse(BaseModel):
    name: str = Field("block", description="Nome do bloco")
    largura: float
    altura: float
    profundidade: float
    faces: List[FaceProps]


class PartDimensions(BaseModel):
    largura: float
    altura: float
    profundidade: float


class PartProps(BaseModel):
    name: str
    type: str
    quantity: int = 1
    dimensions: Optional[PartDimensions] = None
    material: Optional[str] = None
    notes: Optional[str] = None


class AssemblyDefinition(BaseModel):
    largura: float = Field(..., description="Largura total do conjunto em mm")
    altura: float = Field(..., description="Altura total do conjunto em mm")
    profundidade: float = Field(..., description="Profundidade total do conjunto em mm")
    include_handle: bool = Field(True, description="Incluir puxador")
    include_screws: bool = Field(True, description="Incluir parafusos")


class AssemblyResponse(BaseModel):
    name: str = Field("drawer", description="Nome do conjunto")
    largura: float
    altura: float
    profundidade: float
    parts: List[PartProps]


class AssetGeometry(BaseModel):
    vertices: List[List[float]] = Field(default_factory=list, description="Lista de vértices [x,y,z]")
    faces: List[List[int]] = Field(default_factory=list, description="Lista de faces (índices dos vértices)")
    materials: Optional[List[str]] = Field(None, description="Materiais por face")


class AssetResponse(BaseModel):
    id: str
    name: str
    type: str = Field(..., description="Tipo: hardware, component, panel")
    version: str = Field("1.0", description="Versão do asset")
    json_spec: Optional[AssetGeometry] = Field(None, description="Geometria em JSON")
    skp_url: Optional[str] = Field(None, description="URL para download do .skp")
    skp_base64: Optional[str] = Field(None, description="Arquivo .skp codificado em base64 (usado para import direto)")
    default_params: Optional[dict] = Field(None, description="Parâmetros padrão")
    tags: List[str] = Field(default_factory=list, description="Tags para busca")


class AssetCreate(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., description="Nome do asset")
    type: str = Field(..., description="Tipo do asset")
    version: Optional[str] = Field("1.0", description="Versão do asset")
    json_spec: Optional[AssetGeometry] = Field(None, description="Geometria em JSON")
    skp_url: Optional[str] = Field(None, description="URL para download do .skp")
    skp_base64: Optional[str] = Field(None, description="Arquivo .skp codificado em base64 (usado para import direto)")
    default_params: Optional[dict] = Field(None, description="Parâmetros padrão")
    tags: List[str] = Field(default_factory=list, description="Tags para busca")
