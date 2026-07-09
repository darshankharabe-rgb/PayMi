from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas import UserCreate, UserOut, UserLogin, Token
from app.auth import hash_password, verify_password, create_access_token, decode_access_token

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

@app.post("/login", response_model=Token)
def login(credentials: UserLogin):
    user = None
    for existing_user in fake_users_db:
        if existing_user["email"] == credentials.email:
            user = existing_user
            break
    
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": str(user["id"])})
    return {"access_token": access_token, "token_type": "bearer"}

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    for user in fake_users_db:
        if str(user["id"]) == user_id:
            return user
    
    raise HTTPException(status_code=401, detail="User not found")

@app.get("/me", response_model=UserOut)
def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user
