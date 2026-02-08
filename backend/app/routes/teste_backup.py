from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import json
from pathlib import Path

from app.db.database import Base, engine, get_db
from app.models.db_models import Dimensoes
from app.models.schemas import (
    DimensoesCreate,
    DimensoesResponse,
    SketchResponse,
    SketchHeight,
    SketchDimensions,
    FaceProps,
    BlockDefinition,
    BlockResponse,
    PartProps,
    PartDimensions,
    AssemblyDefinition,
    AssemblyResponse,
    AssetGeometry,
    AssetResponse,
)

router = APIRouter(prefix="/teste", tags=["teste"])

# Cria as tabelas localmente (SQLite) na primeira importação.
Base.metadata.create_all(bind=engine)


@router.get("", response_model=DimensoesResponse)
def get_teste():
    return DimensoesResponse(id=0, largura=100.0, altura=50.0, profundidade=25.0)


@router.get("/sketch_default", response_model=SketchResponse)
def get_sketch_default():
    return SketchResponse(name="quadrado", x=10, y=10, z=10)


@router.post("/sketch/altura", response_model=SketchResponse)
def post_sketch_altura(payload: SketchHeight):
    """Recebe JSON {"altura": <int>} e retorna as dimensões do caixote."""
    altura = payload.altura
    return SketchResponse(name="quadrado", x=10, y=10, z=altura)


@router.post("/sketch/caixote", response_model=SketchResponse)
def post_sketch_caixote(payload: SketchDimensions):
    """Recebe JSON {"largura":.., "altura":.., "profundidade":..} e retorna as dimensões do caixote."""
    return SketchResponse(name="caixote", x=payload.largura, y=payload.profundidade, z=payload.altura)


# RESTful endpoints to persist and retrieve sketches (dimensoes)
@router.post("/sketches", response_model=DimensoesResponse)
def create_sketch(payload: SketchDimensions, db: Session = Depends(get_db)):
    """Cria um registro de dimensões (caixote) no banco e retorna o registro."""
    registro = Dimensoes(
        largura=payload.largura,
        altura=payload.altura,
        profundidade=payload.profundidade,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


@router.get("/sketches/{sketch_id}", response_model=DimensoesResponse)
def get_sketch(sketch_id: int, db: Session = Depends(get_db)):
    registro = db.query(Dimensoes).filter(Dimensoes.id == sketch_id).first()
    if not registro:
        raise HTTPException(status_code=404, detail="Sketch not found")
    return registro


@router.get("/sketches", response_model=List[DimensoesResponse])
def list_sketches(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Dimensoes).limit(limit).all()


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


@router.post("/block", response_model=BlockResponse)
def create_block(payload: BlockDefinition):
    """Cria um bloco com dimensões e propriedades por face.

    Se `faces` vier vazio, o endpoint retorna as 6 faces padrão com nomes: front, back, left, right, top, bottom.
    Cada face aceita `color`, `material` e `thickness`.
    """
    default_face_names = ["front", "back", "left", "right", "top", "bottom"]
    if payload.faces and len(payload.faces) > 0:
        faces = payload.faces
    else:
        faces = [FaceProps(name=n) for n in default_face_names]

    return BlockResponse(
        name="block",
        largura=payload.largura,
        altura=payload.altura,
        profundidade=payload.profundidade,
        faces=faces,
    )


@router.post("/drawer", response_model=AssemblyResponse)
def create_drawer(payload: AssemblyDefinition):
    """Gera a lista completa de peças para uma gaveta (drawer) com todas as partes.

    A resposta não persiste nada — é uma definição pronta para o cliente montar o conjunto.
    """
    L = payload.largura
    H = payload.altura
    D = payload.profundidade

    parts: List[PartProps] = []

    # Drawer box components (sides, back, bottom)
    parts.append(PartProps(name="side_panel", type="panel", quantity=2,
                           dimensions=PartDimensions(largura=D, altura=H, profundidade=10),
                           material="MDF", notes="Lateral esquerda/direita"))
    parts.append(PartProps(name="back_panel", type="panel", quantity=1,
                           dimensions=PartDimensions(largura=L, altura=H, profundidade=10),
                           material="MDF", notes="Painel traseiro"))
    parts.append(PartProps(name="bottom_panel", type="panel", quantity=1,
                           dimensions=PartDimensions(largura=L, altura=D, profundidade=6),
                           material="Compensado", notes="Fundo da gaveta"))

    # Front panel (faixada)
    parts.append(PartProps(name="front_panel", type="panel", quantity=1,
                           dimensions=PartDimensions(largura=L, altura=H * 0.9, profundidade=18),
                           material="MDF", notes="Painel frontal da gaveta"))

    # Handle
    if payload.include_handle:
        parts.append(PartProps(name="handle", type="hardware", quantity=1,
                               dimensions=PartDimensions(largura=120, altura=30, profundidade=40),
                               material="Metal", notes="Puxador - montar na frente"))

    # Runners / slides
    parts.append(PartProps(name="runner", type="hardware", quantity=2,
                           dimensions=PartDimensions(largura=D, altura=30, profundidade=20),
                           material="Steel", notes="Corrediças laterais"))

    # Bearings / rolamentos (approx per runner)
    parts.append(PartProps(name="ball_bearing", type="hardware", quantity=8,
                           material="Steel", notes="Rolamentos para corrediças"))

    # Screws and fasteners
    if payload.include_screws:
        parts.append(PartProps(name="screw_pan_head", type="fastener", quantity=24,
                               dimensions=PartDimensions(largura=4, altura=20, profundidade=0),
                               material="Steel", notes="Parafusos para montagem"))
        parts.append(PartProps(name="cam_lock", type="fastener", quantity=4,
                               material="Zamak", notes="Travas de montagem"))

    # Small extras
    parts.append(PartProps(name="glue", type="consumable", quantity=1,
                           notes="Cola para madeira - 1 tubo"))

    return AssemblyResponse(name="drawer", largura=L, altura=H, profundidade=D, parts=parts)


# Mock asset data
MOCK_ASSETS = {
    1: AssetResponse(
        id=1,
        name="puxador_standard",
        type="hardware",
        version="1.0",
        json_spec=AssetGeometry(
            vertices=[[0,0,0], [120,0,0], [120,30,0], [0,30,0], [0,0,40], [120,0,40], [120,30,40], [0,30,40]],
            faces=[[0,1,2,3], [4,7,6,5], [0,4,5,1], [1,5,6,2], [2,6,7,3], [3,7,4,0]],
            materials=["metal", "metal", "metal", "metal", "metal", "metal"]
        ),
        skp_url="https://example.com/assets/puxador_standard.skp",
        tags=["handle", "metal", "standard"]
    ),
    2: AssetResponse(
        id=2,
        name="corredicá_lateral",
        type="hardware",
        version="1.0",
        json_spec=None,
        skp_url="https://example.com/assets/corredicá_lateral.skp",
        default_params={"length": 450, "load_capacity": "45kg"},
        tags=["runner", "slide", "hardware"]
    ),
    3: AssetResponse(
        id=3,
        name="painel_mdf",
        type="component",
        version="1.0",
        json_spec=AssetGeometry(
            vertices=[[0,0,0], [600,0,0], [600,400,0], [0,400,0], [0,0,18], [600,0,18], [600,400,18], [0,400,18]],
            faces=[[0,1,2,3], [4,7,6,5], [0,4,5,1], [1,5,6,2], [2,6,7,3], [3,7,4,0]],
            materials=["mdf", "mdf", "mdf", "mdf", "mdf", "mdf"]
        ),
        default_params={"thickness": 18, "material": "MDF"},
        tags=["panel", "mdf", "wood"]
    ),
    4: AssetResponse(
        id=4,
        name="balcao_simples",
        type="furniture",
        version="1.0",
        json_spec=None,
        skp_url="https://firebasestorage.googleapis.com/v0/b/projeto-plubin.appspot.com/o/assets%2Fbalcao_simples.skp?alt=media",
        default_params={"width": 1200, "height": 900, "depth": 600},
        tags=["furniture", "balcao", "cabinet"]
    )
}


@router.get("/assets", response_model=List[AssetResponse])
def list_assets(asset_type: str = None, limit: int = 100):
    """Lista assets disponíveis. Filtra por tipo se especificado."""
    assets = list(MOCK_ASSETS.values())
    if asset_type:
        assets = [a for a in assets if a.type == asset_type]
    return assets[:limit]


@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int):
    """Busca um asset específico por ID."""
    if asset_id not in MOCK_ASSETS:
        raise HTTPException(status_code=404, detail="Asset not found")
    return MOCK_ASSETS[asset_id]


@router.get("/assets/{asset_id}/download")
def download_asset_skp(asset_id: int):
    """Baixa o arquivo .skp de um asset específico."""
    if asset_id not in MOCK_ASSETS:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset = MOCK_ASSETS[asset_id]
    
    # Para o balcao_simples (ID 4), serve o arquivo real
    if asset_id == 4:
        skp_path = Path("D:/Projeto Plubin/Balcao Simples.skp")
        if skp_path.exists():
            return FileResponse(
                path=str(skp_path),
                filename="balcao_simples.skp",
                media_type="application/octet-stream"
            )
        else:
            raise HTTPException(status_code=404, detail="SKP file not found")
    
    # Para outros assets, retorna erro por enquanto (não temos arquivos reais)
    raise HTTPException(status_code=404, detail="SKP file not available for this asset")


@router.get("/assets/{asset_id}/download")
def download_asset_skp(asset_id: int):
    """Baixa o arquivo .skp de um asset específico."""
    if asset_id not in MOCK_ASSETS:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset = MOCK_ASSETS[asset_id]
    
    # Para o balcao_simples (ID 4), serve o arquivo real
    if asset_id == 4:
        skp_path = Path("D:/Projeto Plubin/Balcao Simples.skp")
        if skp_path.exists():
            return FileResponse(
                path=str(skp_path),
                filename="balcao_simples.skp",
                media_type="application/octet-stream"
            )
        else:
            raise HTTPException(status_code=404, detail="SKP file not found")
    
    # Para outros assets, retorna erro por enquanto (não temos arquivos reais)
    raise HTTPException(status_code=404, detail="SKP file not available for this asset")
