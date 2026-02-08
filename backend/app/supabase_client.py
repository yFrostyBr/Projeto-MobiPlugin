import os
try:
    import requests
except Exception:
    try:
        import httpx as _httpx

        class _RequestsShim:
            def get(self, url, headers=None, timeout=None):
                r = _httpx.get(url, headers=headers, timeout=timeout)

                class Resp:
                    def __init__(self, r):
                        self._r = r
                        self.status_code = r.status_code
                        self.text = r.text

                    def json(self):
                        return self._r.json()

                return Resp(r)

        requests = _RequestsShim()
    except Exception:
        requests = None

from supabase import create_client, Client
from typing import Optional, List, Dict, Any

class SupabaseManager:
    def __init__(self):
        # Prefer environment variables for secrets and configuration.
        # Set these in Heroku with: heroku config:set SUPABASE_URL=... SUPABASE_ANON_KEY=... SUPABASE_SERVICE_ROLE_KEY=...
        self.supabase_url = os.getenv('SUPABASE_URL', 'https://pcaqqbooticnykbxtfjm.supabase.co')
        self.anon_key = os.getenv('SUPABASE_ANON_KEY', os.getenv('SUPABASE_ANON', None))
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', os.getenv('SUPABASE_SERVICE_KEY', None))

        if not self.anon_key:
            # Fallback to embedded key if none provided (local dev only)
            self.anon_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBjYXFxYm9vdGljbnlrYnh0ZmptIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzMjQ5ODgsImV4cCI6MjA4NTkwMDk4OH0.4v9jXKMHa1AJs6liCUFv2i-sm2cxNPDQ2AuNtMKcaOo'

        # Clients are created lazily to avoid import-time failures (e.g. httpx/proxy mismatch)
        self.supabase: Optional[Client] = None
        self.service_client: Optional[Client] = None

    def _ensure_clients(self):
        """Initialize supabase clients if not already created. Exceptions are caught
        and logged so import-time initialization doesn't crash the app during deploy.
        """
        if self.supabase is None:
            try:
                self.supabase = create_client(self.supabase_url, self.anon_key)
            except Exception as e:
                print(f"Could not initialize supabase client: {e}")
                self.supabase = None

        if self.service_client is None and self.service_role_key:
            try:
                self.service_client = create_client(self.supabase_url, self.service_role_key)
            except Exception as e:
                print(f"Could not initialize supabase service client: {e}")
                self.service_client = None
    
    def create_asset(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new asset in the database"""
        try:
            self._ensure_clients()
            client = self.service_client or self.supabase
            if client is None:
                print("No supabase client available to create asset")
                return None
            response = client.table('assets').insert(asset_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating asset: {e}")
            return None
    
    def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get asset by ID"""
        try:
            self._ensure_clients()
            if not self.supabase:
                print("No supabase client available to get asset")
                return None
            response = self.supabase.table('assets').select("*").eq('id', asset_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting asset: {e}")
            return None
    
    def list_assets(self, asset_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List assets with optional type filter"""
        try:
            self._ensure_clients()
            if not self.supabase:
                print("No supabase client available to list assets")
                return []
            query = self.supabase.table('assets').select("*")
            
            if asset_type:
                query = query.eq('type', asset_type)
            
            response = query.limit(limit).execute()
            return response.data or []
        except Exception as e:
            print(f"Error listing assets: {e}")
            return []
    
    def update_asset(self, asset_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update asset by ID"""
        try:
            self._ensure_clients()
            client = self.service_client or self.supabase
            if client is None:
                print("No supabase client available to update asset")
                return None
            response = client.table('assets').update(update_data).eq('id', asset_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating asset: {e}")
            return None
    
    def delete_asset(self, asset_id: str) -> bool:
        """Delete asset by ID"""
        try:
            self._ensure_clients()
            client = self.service_client or self.supabase
            if client is None:
                print("No supabase client available to delete asset")
                return False
            response = client.table('assets').delete().eq('id', asset_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting asset: {e}")
            return False
    
    def upload_file_to_storage(self, file_path: str, bucket_name: str, remote_path: str) -> Optional[str]:
        """Upload file to Supabase Storage"""
        try:
            with open(file_path, 'rb') as file:
                # Use service client for upload when available (required for private buckets)
                self._ensure_clients()
                client_to_use = self.service_client or self.supabase
                if client_to_use is None:
                    print("No supabase client available to upload file")
                    return None
                upload_resp = client_to_use.storage.from_(bucket_name).upload(remote_path, file)

            # If upload_resp indicates error, raise
            if not upload_resp:
                print(f"Upload returned empty response: {upload_resp}")
                return None

            # Attempt to return a usable URL. If bucket is public this URL works:
            public_url = f"{self.supabase_url}/storage/v1/object/public/{bucket_name}/{remote_path}"

            # If the bucket is private, and we have a service role key, request a signed URL
            if self.service_client:
                try:
                    sign_endpoint = f"{self.supabase_url}/storage/v1/object/sign/{bucket_name}/{remote_path}"
                    headers = {
                        'Authorization': f'Bearer {self.service_role_key}',
                        'apikey': self.service_role_key
                    }
                    if requests is None:
                        print("No HTTP client available to request signed URL; returning public URL")
                        return public_url
                    r = requests.get(sign_endpoint, headers=headers, timeout=10)
                    if r.status_code == 200:
                        data = r.json()
                        # The signed URL is returned directly as a string or under 'signedURL'
                        signed_url = data.get('signedURL') or data.get('signed_url') or data.get('signedUrl') or data.get('url') or data.get('signedURL')
                        if signed_url:
                            return signed_url
                    else:
                        # If signing failed, fall back to public URL (might 403 for private)
                        print(f"Signing request returned {r.status_code}: {r.text}")
                except Exception as e:
                    print(f"Error requesting signed URL: {e}")

            return public_url
        except Exception as e:
            print(f"Error uploading file: {e}")
            return None
    
    def get_public_url(self, bucket_name: str, file_path: str) -> str:
        """Get public URL for a file in Supabase Storage"""
        self._ensure_clients()
        if not self.supabase:
            print("No supabase client available to get public URL")
            return ""
        return self.supabase.storage.from_(bucket_name).get_public_url(file_path)

# Global instance
supabase_manager = SupabaseManager()