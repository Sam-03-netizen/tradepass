from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
from .config import settings
from .security import ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    invalid = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        user_id = int(sub)
    except (JWTError, TypeError, ValueError):
        raise invalid
    user = db.get(User, user_id)
    if not user: raise invalid
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin": raise HTTPException(status_code=403, detail="Administrator access required")
    return user
