from fastapi import FastAPI, HTTPException
from app.schemas import UserCreate, UserOut
from app.auth import hash_password

# temporary in-memory store, will replace with real DB
fake_users_db = []


app = FastAPI(title="PayMi Backend Service", version="1.0.0")

@app.get("/")
def root():
    return {"message": "Welcome to the PayMi Backend Service!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/register", response_model=UserOut)
def register_user(user: UserCreate):
    # Check if user already exists
    for existing_user in fake_users_db:
        if existing_user["email"] == user.email:
            raise HTTPException(status_code=400, detail="Email already registered")

    # Create a new user and add to the in-memory store
    new_user = {
        "id" : len(fake_users_db) + 1,
        "name" : user.name,
        "email" : user.email,
        "password" : hash_password(user.password)  # In a real application hashed
    }
    fake_users_db.append(new_user)
    return new_user