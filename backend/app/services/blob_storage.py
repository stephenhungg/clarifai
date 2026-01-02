"""
Vercel Blob storage helper functions for PDFs and other files
"""

import os
from typing import Optional
from pathlib import Path
import tempfile

# Vercel Blob storage (optional, falls back to local storage)
try:
    from vercel_blob import put as vercel_put
    VERCEL_BLOB_AVAILABLE = True
except ImportError:
    VERCEL_BLOB_AVAILABLE = False

async def upload_to_blob(file_path: str, file_name: str) -> Optional[str]:
    """Upload any file to Vercel Blob storage and return the URL"""
    blob_token = os.getenv("BLOB_READ_WRITE_TOKEN")
    if not blob_token:
        print(f"[BLOB] BLOB_READ_WRITE_TOKEN not set, skipping upload for {file_name}")
        return None

    try:
        print(f"[BLOB] Uploading {file_name} to Vercel Blob...")
        file_size = os.path.getsize(file_path)
        print(f"[BLOB] File size: {file_size / (1024*1024):.2f} MB")
        
        # Read file data
        with open(file_path, "rb") as f:
            file_data = f.read()

        # Try using vercel_blob package first (if available)
        if VERCEL_BLOB_AVAILABLE:
            try:
                blob = vercel_put(
                    pathname=file_name,
                    body=file_data,
                    options={
                        "access": "public",
                        "token": blob_token,
                    }
                )
                blob_url = blob.get("url") if isinstance(blob, dict) else blob.url
                print(f"[BLOB] Upload successful (package): {blob_url}")
                return blob_url
            except Exception as package_err:
                print(f"[BLOB] Package upload failed: {package_err}, trying REST API...")
        
        # Fallback to REST API using httpx
        import httpx
        
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout for large files
            response = await client.put(
                f"https://blob.vercel-storage.com/{file_name}",
                headers={
                    "Authorization": f"Bearer {blob_token}",
                    "Content-Type": "application/octet-stream",
                },
                params={
                    "access": "public",
                },
                content=file_data
            )
            
            if response.status_code == 200:
                result = response.json()
                blob_url = result.get("url")
                print(f"[BLOB] Upload successful (REST API): {blob_url}")
                return blob_url
            else:
                print(f"[BLOB] REST API upload failed with status {response.status_code}: {response.text[:500]}")
                return None
                
    except ImportError:
        print("[BLOB] httpx not available, cannot upload")
        return None
    except Exception as e:
        print(f"[BLOB] Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def download_from_blob(blob_url: str) -> Optional[str]:
    """Download file from Vercel Blob and return temporary file path"""
    try:
        import httpx
        
        print(f"[BLOB] Downloading from {blob_url}...")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.get(blob_url)
            
            if response.status_code == 200:
                # Create temporary file
                suffix = Path(blob_url).suffix or ".pdf"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                
                print(f"[BLOB] Downloaded to temporary file: {tmp_path}")
                return tmp_path
            else:
                print(f"[BLOB] Download failed with status {response.status_code}")
                return None
                
    except Exception as e:
        print(f"[BLOB] Download failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def is_blob_url(url: str) -> bool:
    """Check if a URL is a Vercel Blob URL"""
    return url.startswith("https://") and ("blob.vercel-storage.com" in url or "public.blob.vercel-storage.com" in url)

