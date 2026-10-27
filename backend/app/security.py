from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
def hash_password(password: str) -> str: return pwd_context.hash(password)
def verify_password(password: str, hashed: str) -> bool: return pwd_context.verify(password, hashed)
def create_access_token(user_id: int, company_id: int, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(user_id), "company_id": company_id, "role": role, "exp": expires}, settings.secret_key, algorithm=ALGORITHM)
