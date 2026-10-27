from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..database import get_db
from ..models import Company, User
from ..schemas import RegisterRequest, UserResponse, LoginRequest, TokenResponse
from ..security import verify_password, hash_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])
def authenticate(email: str, password: str, db: Session) -> User:
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password", headers={"WWW-Authenticate": "Bearer"})
    return user
def token_for(user: User): return TokenResponse(access_token=create_access_token(user.id, user.company_id, user.role))

@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = str(payload.user.email).lower()
    if db.query(User).filter(User.email == email).first(): raise HTTPException(status_code=409, detail="Email already registered")
    company = Company(name=payload.company.name.strip(), country=payload.company.country, company_type=payload.company.company_type.strip())
    try:
        db.add(company); db.flush()
        user = User(name=payload.user.name.strip(), email=email, password_hash=hash_password(payload.user.password), company_id=company.id, role="admin")
        db.add(user); db.commit(); db.refresh(user)
        return user
    except IntegrityError:
        db.rollback(); raise HTTPException(status_code=409, detail="Account conflicts with an existing record")
    except Exception:
        db.rollback(); raise

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return token_for(authenticate(str(payload.email).lower(), payload.password, db))

@router.post("/token", response_model=TokenResponse)
def login_for_swagger(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return token_for(authenticate(form.username.lower(), form.password, db))
