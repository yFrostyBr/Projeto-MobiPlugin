from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
import os
import json
from pathlib import Path

from app.db.database import Base, engine, get_db
from app.models.db_models import Dimensoes
from app.supabase_client import supabase_manager
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
    AssetCreate,
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


@router.get("/assets", response_model=List[AssetResponse])
def list_assets(asset_type: str = None, limit: int = 100):
    """Lista assets disponíveis do Supabase. Filtra por tipo se especificado."""
    try:
        assets_data = supabase_manager.list_assets(asset_type, limit)
        
        assets = []
        for asset_data in assets_data:
            # Convert Supabase data to AssetResponse format
            json_spec = None
            if asset_data.get('json_spec'):
                json_spec = AssetGeometry(**asset_data['json_spec'])
            
            asset = AssetResponse(
                id=asset_data['id'],
                name=asset_data['name'],
                type=asset_data['type'],
                version=asset_data.get('version', '1.0'),
                json_spec=json_spec,
                skp_url=asset_data.get('skp_url'),
                skp_base64=asset_data.get('skp_base64'),
                default_params=asset_data.get('default_params'),
                tags=asset_data.get('tags', [])
            )
            assets.append(asset)
        
        return assets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching assets: {str(e)}")


@router.post("/assets", response_model=AssetResponse)
def create_asset(asset: AssetCreate):
    """Cria um novo asset (aceita `skp_base64` ou `skp_url`)."""
    try:
        asset_payload = asset.dict()
        created = supabase_manager.create_asset(asset_payload)

        if not created:
            raise HTTPException(status_code=500, detail="Failed to create asset")

        json_spec = None
        if created.get('json_spec'):
            json_spec = AssetGeometry(**created['json_spec'])

        return AssetResponse(
            id=created['id'],
            name=created['name'],
            type=created['type'],
            version=created.get('version', '1.0'),
            json_spec=json_spec,
            skp_url=created.get('skp_url'),
            skp_base64=created.get('skp_base64'),
            default_params=created.get('default_params'),
            tags=created.get('tags', []),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating asset: {str(e)}")


@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: str):
    """Busca um asset específico por ID no Supabase."""
    try:
        asset_data = supabase_manager.get_asset(asset_id)
        
        if not asset_data:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Convert Supabase data to AssetResponse format
        json_spec = None
        if asset_data.get('json_spec'):
            json_spec = AssetGeometry(**asset_data['json_spec'])
        
        return AssetResponse(
            id=asset_data['id'],
            name=asset_data['name'],
            type=asset_data['type'],
            version=asset_data.get('version', '1.0'),
            json_spec=json_spec,
            skp_url=asset_data.get('skp_url'),
            skp_base64=asset_data.get('skp_base64'),
            default_params=asset_data.get('default_params'),
            tags=asset_data.get('tags', [])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching asset: {str(e)}")


@router.get("/assets/{asset_id}/download")
def download_asset_skp(asset_id: str):
    """Redireciona para o download do arquivo .skp no Supabase Storage."""
    try:
        asset_data = supabase_manager.get_asset(asset_id)
        
        if not asset_data:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        if asset_data.get('skp_url'):
            # Redirect to Supabase Storage URL
            return RedirectResponse(url=asset_data['skp_url'], status_code=302)
        else:
            raise HTTPException(status_code=404, detail="SKP file not available for this asset")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing asset download: {str(e)}")