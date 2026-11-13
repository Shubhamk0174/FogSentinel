import sys
import time
import requests
from pathlib import Path

URL = "https://archive.ics.uci.edu/static/public/442/detection+of+iot+botnet+attacks+n+baiot.zip"
TARGET = Path("data/raw/detection_of_iot_botnet_attacks_n_baiot.zip")

def download_dataset():
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    print(f"Starting download from: {URL}")
    print(f"Saving to: {TARGET}")
    
    headers = {"User-Agent": "FogSentinel-Downloader/1.0"}
    
    start_time = time.time()
    last_log_time = start_time
    downloaded = 0
    
    # Check if existing partial file exists
    mode = "wb"
    resume_header = {}
    if TARGET.exists():
        downloaded = TARGET.stat().st_size
        if downloaded > 0:
            print(f"Existing file found: {downloaded / (1024*1024):.2f} MB")
            # If large enough, maybe complete? But server might not support range.
    
    with requests.get(URL, headers=headers, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        total_header = resp.headers.get("content-length")
        total_size = int(total_header) if total_header else None
        
        with open(TARGET, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024): # 1MB chunks
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    curr_time = time.time()
                    if curr_time - last_log_time >= 5.0:
                        speed = downloaded / (1024 * 1024 * (curr_time - start_time + 1e-6))
                        if total_size:
                            pct = (downloaded / total_size) * 100
                            print(f"Downloaded {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({pct:.1f}%) at {speed:.2f} MB/s", flush=True)
                        else:
                            print(f"Downloaded {downloaded / (1024*1024):.1f} MB at {speed:.2f} MB/s", flush=True)
                        last_log_time = curr_time

    total_time = time.time() - start_time
    print(f"Download complete: {downloaded / (1024*1024):.2f} MB in {total_time:.1f}s", flush=True)

if __name__ == "__main__":
    download_dataset()

