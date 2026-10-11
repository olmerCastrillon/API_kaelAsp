from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from models import Usuario, RolEnum

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def obtener_usuario_actual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == token).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de autenticación inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario

def verificar_rol(roles_permitidos: list[RolEnum]):
    def dependencia(current_user: Usuario = Depends(obtener_usuario_actual)):
        if current_user.rol != RolEnum.SUPERADMIN and current_user.rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para acceder a este recurso."
            )
        return current_user
    return dependencia


from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from database import get_db
from models import Usuario, RolEnum

# Configuración de seguridad
SECRET_KEY = "tu_clave_secreta_super_segura_kael"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # <-- Asegúrate de tener esta línea definida

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def crear_token_acceso(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Resto de funciones de autenticación...
