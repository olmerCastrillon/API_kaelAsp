from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import Usuario
from auth import ACCESS_TOKEN_EXPIRE_MINUTES, crear_token_acceso

router = APIRouter(prefix="/api", tags=["Autenticación"])

# Contexto de seguridad para cifrado y verificación con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_password(plain_password: str, hashed_password: str) -> bool:
    """Valida la contraseña en texto plano contra el hash almacenado en la BD,
    aplicando el recorte de seguridad de 72 bytes requerido por bcrypt."""
    if not plain_password or not hashed_password:
        return False
    return pwd_context.verify(plain_password[:72], hashed_password)

@router.post("/login")
def login_para_obtener_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Endpoint de Autenticación:
    - Recibe 'username' (que usaremos para el correo electrónico) y 'password'.
    - Valida contra PostgreSQL.
    - Retorna el token JWT de acceso.
    """
    # 1. Buscamos al usuario por su correo electrónico
    usuario = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    
    # 2. Verificamos si el usuario existe y si la contraseña coincide
    if not usuario or not verificar_password(form_data.password, usuario.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Generamos el Token JWT con vigencia configurada e incorporamos su rol
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crear_token_acceso(
        data={"sub": usuario.email, "rol": usuario.rol.value}, 
        expires_delta=access_token_expires
    )
    
    # 4. Retornamos la respuesta con el token y metadatos útiles para el frontend
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "rol": usuario.rol,
        "email": usuario.email
    }