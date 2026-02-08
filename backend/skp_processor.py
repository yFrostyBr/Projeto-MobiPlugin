#!/usr/bin/env python3
"""
Script para processar arquivos .skp e prepará-los para servir via API
"""
import os
import base64
import json
import shutil
from pathlib import Path
from typing import Dict, Optional

class SKPProcessor:
    def __init__(self, assets_dir: str = "assets"):
        self.assets_dir = Path(assets_dir)
        self.assets_dir.mkdir(exist_ok=True)
        
    def process_skp_file(self, skp_path: str, asset_name: str, asset_type: str = "component") -> Dict:
        """
        Processa um arquivo .skp e cria entrada de asset
        
        Args:
            skp_path: Caminho para o arquivo .skp
            asset_name: Nome do asset
            asset_type: Tipo do asset (component, hardware, etc.)
            
        Returns:
            Dict com informações do asset processado
        """
        skp_file = Path(skp_path)
        if not skp_file.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {skp_path}")
            
        # Copia arquivo para diretório de assets
        asset_filename = f"{asset_name}.skp"
        asset_path = self.assets_dir / asset_filename
        shutil.copy2(skp_file, asset_path)
        
        # Obtém informações do arquivo
        file_stats = os.stat(asset_path)
        file_size = file_stats.st_size
        
        # Cria estrutura do asset
        asset_data = {
            "name": asset_name,
            "type": asset_type,
            "version": "1.0",
            "file_path": str(asset_path),
            "file_size": file_size,
            "skp_filename": asset_filename,
            "tags": [asset_type, "sketchup"]
        }
        
        return asset_data
    
    def encode_skp_to_base64(self, skp_path: str) -> str:
        """Codifica arquivo .skp em base64 para transporte"""
        with open(skp_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def save_asset_metadata(self, asset_data: Dict, metadata_file: str = "assets_metadata.json"):
        """Salva metadados do asset em arquivo JSON"""
        metadata_path = self.assets_dir / metadata_file
        
        # Carrega metadados existentes ou cria novo
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                all_assets = json.load(f)
        else:
            all_assets = {}
            
        # Gera ID baseado no nome ou usa próximo disponível
        asset_id = len(all_assets) + 1
        while str(asset_id) in all_assets:
            asset_id += 1
            
        asset_data['id'] = asset_id
        all_assets[str(asset_id)] = asset_data
        
        # Salva metadados atualizados
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(all_assets, f, indent=2, ensure_ascii=False)
            
        return asset_id

def main():
    """Processa o arquivo Balcao Simples.skp"""
    processor = SKPProcessor()
    
    # Processa o arquivo SKP do balcão
    balcao_path = "D:\\Projeto Plubin\\Balcao Simples.skp"
    
    if os.path.exists(balcao_path):
        print(f"Processando arquivo: {balcao_path}")
        
        asset_data = processor.process_skp_file(
            balcao_path, 
            "balcao_simples", 
            "furniture"
        )
        
        asset_id = processor.save_asset_metadata(asset_data)
        
        print(f"Asset criado com ID: {asset_id}")
        print(f"Dados: {json.dumps(asset_data, indent=2, ensure_ascii=False)}")
        
    else:
        print(f"Arquivo não encontrado: {balcao_path}")

if __name__ == "__main__":
    main()