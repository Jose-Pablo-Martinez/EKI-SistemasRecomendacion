"""
Módulo: auth.py
Fecha de modificación: 2026-05-23
Función: Manejo de autenticación, 
generación y validación de JSON Web Tokens (JWT), 
encriptación de contraseñas y dependencias de seguridad.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
# pyrefly: ignore [missing-import]
from fastapi import Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from fastapi.security import OAuth2PasswordBearer
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.usuarios import Usuario

# ─── Configuración de JWT ─────────────────────────────────────────────────────
# Idealmente usar variables de entorno para esto en producción
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "eki_super_secret_dev_key_12345")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440")) # 24 horas por defecto

# ─── Configuración de Criptografía ────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/usuarios/login")

# ─── Funciones de Hashing ─────────────────────────────────────────────────────
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña plana coincide con el hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Retorna el hash bcrypt de la contraseña."""
    return pwd_context.hash(password)

# ─── Funciones JWT ────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Genera un token JWT firmado."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ─── Dependencias de Autenticación ───────────────────────────────────────────
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    """
    Decodifica el JWT, verifica que el usuario exista en la base de datos
    y lo retorna. Levanta HTTPException 401 si falla la autenticación.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None:
        raise credentials_exception
        
    if not usuario.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
        
    return usuario

def get_current_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Verifica que el usuario autenticado sea un administrador."""
    if current_user.tipo_usuario != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes (se requiere rol de administrador)"
        )
    return current_user
