#!/usr/bin/env python3
"""
Upload SKP file to Supabase Storage and create asset record
"""
import os
from pathlib import Path
from app.supabase_client import supabase_manager
from supabase import create_client, Client
from dotenv import load_dotenv
import base64

load_dotenv()


def init_supabase_from_env() -> Client:
    """Create a lightweight Supabase client using SUPABASE_URL and SUPABASE_KEY env vars."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    # Trim possible surrounding quotes
    if url:
        url = url.strip().strip('"').strip("'")
    if key:
        key = key.strip().strip('"').strip("'")
    if not url or not key:
        raise RuntimeError('SUPABASE_URL and SUPABASE_KEY (or SUPABASE_ANON_KEY) must be set in environment')
    return create_client(url, key)


def list_todos_via_env_client():
    """Query the `todos` table and print results (mimics the generated Flask example)."""
    try:
        client = init_supabase_from_env()
        resp = client.table('todos').select('*').execute()
        todos = resp.data or []
        print('Todos:')
        for t in todos:
            print('-', t.get('name'))
    except Exception as e:
        print(f'Error listing todos: {e}')

def upload_balcao_to_supabase():
    """Upload the Balcao Simples.skp file to Supabase"""
    try:
        # Local file path
        local_file = Path("D:/Projeto Plubin/Balcao Simples.skp")
        
        if not local_file.exists():
            print(f"File not found: {local_file}")
            return None
        
        print(f"Importing {local_file} into database (base64)...")

        # Read and base64-encode the SKP file
        with open(local_file, 'rb') as f:
            data = f.read()
        b64 = base64.b64encode(data).decode('ascii')

        # Prepare asset update payload to store in SQL
        asset_data = {
            "skp_base64": b64,
            "skp_filename": local_file.name
        }

        # Find existing asset by name
        assets = supabase_manager.list_assets()
        balcao_asset = None
        for asset in assets:
            if asset.get('name') == 'balcao_simples':
                balcao_asset = asset
                break

        if balcao_asset:
            updated_asset = supabase_manager.update_asset(balcao_asset['id'], asset_data)
            if updated_asset:
                print(f"Asset record updated successfully! ID: {balcao_asset['id']}")
                return balcao_asset['id']
            else:
                print("Failed to update asset record")
                return None
        else:
            new_asset_data = {
                "name": "balcao_simples",
                "type": "furniture",
                "version": "1.0",
                "skp_base64": b64,
                "skp_filename": local_file.name,
                "default_params": {"width": 1200, "height": 900, "depth": 600},
                "tags": ["furniture", "balcao", "cabinet"]
            }

            # Try to create; if creation fails, attempt to find existing asset and update it
            try:
                created_asset = supabase_manager.create_asset(new_asset_data)
            except Exception as e:
                print(f"Error creating asset (exception): {e}")
                created_asset = None

            if created_asset:
                print(f"New asset created successfully! ID: {created_asset.get('id')}")
                return created_asset.get('id')
            else:
                print("Create returned no result — attempting to find and update existing asset by name...")
                # Re-query assets and try update
                try:
                    assets = supabase_manager.list_assets()
                    for asset in assets:
                        if asset.get('name') == 'balcao_simples':
                            balcao_asset = asset
                            break
                    if balcao_asset:
                        updated_asset = supabase_manager.update_asset(balcao_asset['id'], new_asset_data)
                        if updated_asset:
                            print(f"Existing asset updated successfully after create conflict. ID: {balcao_asset['id']}")
                            return balcao_asset['id']
                        else:
                            print("Failed to update existing asset after create conflict")
                            return None
                    else:
                        print("No existing asset found to update after failed create")
                        return None
                except Exception as e:
                    print(f"Error while attempting fallback update: {e}")
                    return None
            
    except Exception as e:
        print(f"Error uploading to Supabase: {e}")
        return None

if __name__ == "__main__":
    # Optional: list todos using simple env-based client (like the Flask example)
    try:
        list_todos_via_env_client()
    except Exception:
        pass

    upload_balcao_to_supabase()