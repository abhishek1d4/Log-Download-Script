import os
import requests
import tarfile
import zipfile
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# For colored output
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Lists to keep track of skipped dirs and failed downloads
skipped_dirs = []
failed_files = []

def download_file(url, path):
    """Download a file from the given URL and save it to the specified path."""
    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded: {path}")
        else:
            print(f"{RED}[FAIL]{RESET} Failed to download (HTTP {response.status_code}): {url}")
            failed_files.append(url)
    except Exception as e:
        print(f"{RED}[FAIL]{RESET} Error downloading {url}: {e}")
        failed_files.append(url)

def unzip_file(file_path):
    """Unzip a file (supports .tar.gz and .zip) and extract its contents to the same directory."""
    try:
        if file_path.endswith(".tar.gz"):
            with tarfile.open(file_path, "r:gz") as tar:
                tar.extractall(path=os.path.dirname(file_path))
            print(f"Unzipped: {file_path}")
            os.remove(file_path)
        elif file_path.endswith(".zip"):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(path=os.path.dirname(file_path))
            print(f"Unzipped: {file_path}")
            os.remove(file_path)
    except Exception as e:
        print(f"{RED}[FAIL]{RESET} Error extracting {file_path}: {e}")
        failed_files.append(file_path)

def download_recursive(url, base_path):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"{RED}[SKIP]{RESET} Failed to access (HTTP {response.status_code}): {url}")
            skipped_dirs.append(url)
            return
    except Exception as e:
        print(f"{RED}[SKIP]{RESET} Error accessing {url}: {e}")
        skipped_dirs.append(url)
        return

    # Parse current root domain
    parsed_base = urlparse(url)

    soup = BeautifulSoup(response.text, 'html.parser')
    for link in soup.find_all('a'):
        href = link.get('href')
        if href == '../' or href == '/':
            continue

        full_url = urljoin(url, href)
        parsed_full = urlparse(full_url)

        # Reject any absolute URL that doesn't start under our current path
        if parsed_full.netloc != parsed_base.netloc:
            # Different host
            continue
        if not full_url.startswith(url):
            # Avoid going to higher or side paths
            continue

        if href.endswith('/'):  # It's a directory
            dir_path = os.path.join(base_path, href)
            os.makedirs(dir_path, exist_ok=True)
            download_recursive(full_url, dir_path)
        else:  # It's a file
            file_path = os.path.join(base_path, href)
            download_file(full_url, file_path)
            if file_path.endswith((".tar.gz", ".zip")):
                unzip_file(file_path)

if __name__ == "__main__":
    base_url = input("Enter the base URL to download files from: ").strip()
    if not base_url.endswith('/'):
        base_url += '/'

    folder_name = input("Enter the DIAL number: ").strip()
    desktop_path = os.path.join("/home/abhishek.bisla/mywork/dials", folder_name)
    base_path = desktop_path

    os.makedirs(base_path, exist_ok=True)

    print(f"Downloading files from: {base_url}")
    download_recursive(base_url, base_path)
    print("Download and extraction completed!")

    # Summary
    print(f"\n{BLUE}========== SUMMARY =========={RESET}")
    if skipped_dirs:
        print(f"{BLUE}Directories skipped:{RESET}")
        for d in skipped_dirs:
            print(f"{RED}[SKIP]{RESET} {d}")
    else:
        print("No directories were skipped.")

    if failed_files:
        print(f"\n{BLUE}Files failed to download or extract:{RESET}")
        for f in failed_files:
            print(f"{RED}[FAIL]{RESET} {f}")
    else:
        print("No files failed.")

    print(f"{BLUE}============================={RESET}")