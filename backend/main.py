from fastapi import FastAPI

app = FastAPI(title="Payments Intelligence API")


@app.get("/")
def home():
    return {"status": "running"}