from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    name : str
    email : EmailStr
    password : str

class UserOut(BaseModel):
    id : int
    name : str
    email : EmailStr

# Login schema for user authentication
class UserLogin(BaseModel):
    email : EmailStr
    password : str

class Token(BaseModel):
    access_token : str
    token_type : str = "bearer"

class AccountOut(BaseModel):
    id : int
    owner_id : int
    created_at : datetime

    class Config:
        from_attributes = True

class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: int