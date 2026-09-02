from fastapi import FastAPI

app = FastAPI(title="CareerLens API")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Report that the API is available."""
    return {"status": "healthy"}
