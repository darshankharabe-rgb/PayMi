from fastapi import FastAPI

app = FastAPI(title="PayMi Backend Service", version="1.0.0")

@app.get("/")
def root():
    return {"message": "Welcome to the PayMi Backend Service!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}