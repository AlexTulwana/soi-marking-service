import httpx

MAX_BYTES = 15 * 1024 * 1024  # 15 MB limit per file


# Downloads a file from a signed URL.
# Stops if the file is too big, so one bad upload cannot hurt the service.
def fetch_file(url: str) -> bytes:
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        if len(response.content) > MAX_BYTES:
            raise ValueError("File is too large")
        return response.content
