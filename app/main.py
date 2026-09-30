from fastapi import FastAPI

# Main FastAPI app for the SOI marking service.
# Laravel sends submissions here for OCR and marking.
app = FastAPI(title="SOI Marking Service")


# Simple health check.
# Used to confirm the service is up (and later by the load balancer).
@app.get("/health")
def health():
    return {"status": "ok"}
