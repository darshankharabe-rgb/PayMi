from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.schemas import UserCreate, UserOut, UserLogin, Token
from app.auth import hash_password, verify_password, create_access_token, decode_access_token
from app.database import get_db
from app.models import User, Account
from app.schemas import AccountOut

import uuid
from sqlalchemy import func
from app.models import LedgerEntry
from app.schemas import TransferCreate


app = FastAPI(title="PayMi Backend Service", version="1.0.0")

@app.get("/")
def root():
    return {"message": "Welcome to the PayMi Backend Service!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hash_password(user.password),
    )
    db.add(new_user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token payload invalid")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@app.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/accounts", response_model=AccountOut)
def create_account(
    db:Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_account = Account(owner_id=current_user.id)
    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return new_account


# --- HELPER FUNCTION ---
def get_account_balance(db: Session, account_id: int) -> int:
    # scalar() returns the raw number from the database instead of a tuple
    # 'or 0' handles the case where the account has no entries yet (returns None)
    credits = db.query(func.sum(LedgerEntry.amount)).filter(
        LedgerEntry.account_id == account_id,
        LedgerEntry.entry_type == "credit"
    ).scalar() or 0

    debits = db.query(func.sum(LedgerEntry.amount)).filter(
        LedgerEntry.account_id == account_id,
        LedgerEntry.entry_type == "debit"
    ).scalar() or 0

    return credits - debits


# --- ROUTES ---
@app.get("/accounts/{account_id}/balance")
def read_balance(
    account_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Verify the account exists and belongs to the user
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account or account.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Account not found")

    balance = get_account_balance(db, account_id)
    return {"account_id": account_id, "balance": balance}


@app.post("/transfer")
def transfer_funds(
    transfer: TransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # 1. Verify sender owns the from_account
    sender_account = db.query(Account).filter(Account.id == transfer.from_account_id).first()
    if not sender_account or sender_account.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to transfer from this account")

    # 2. Check for sufficient funds
    current_balance = get_account_balance(db, transfer.from_account_id)
    if current_balance < transfer.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # 3. Create the atomic transfer
    tx_id = str(uuid.uuid4())
    
    debit = LedgerEntry(
        account_id=transfer.from_account_id,
        amount=transfer.amount,
        entry_type="debit",
        transaction_id=tx_id
    )
    
    credit = LedgerEntry(
        account_id=transfer.to_account_id,
        amount=transfer.amount,
        entry_type="credit",
        transaction_id=tx_id
    )
    
    # Stage both writes
    db.add(debit)
    db.add(credit)
    
    # ATOMICITY: Commit both rows to the database simultaneously.
    # If the server crashes here, the database rolls back both, saving the money.
    db.commit()
    
    return {"message": "Transfer successful", "transaction_id": tx_id}