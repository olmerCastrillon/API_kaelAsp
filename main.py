import datetime
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Numeric, Text, func, cast, Date
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.staticfiles import StaticFiles
from config import settings

# --- CONFIGURACIÓN DE SEGURIDAD Y JWT ---
SECRET_KEY = "KAEL_SECRET_KEY_SUPER_SECRETA_CAMBIAR_EN_PRODUCCION"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 día de sesión

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

# --- CONFIGURACIÓN DE POSTGRESQL ---
motor = create_engine(settings.DATABASE_URL)
SesionLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor)
Base = declarative_base()

# --- MODELOS DE BASE DE DATOS ---
class UsuarioDB(Base):
    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(20))
    rol = Column(String(50), nullable=False, default="cliente")  # 'superadmin' o 'cliente'
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    conjuntos = relationship("ConjuntoDB", back_populates="usuario")

class ConjuntoDB(Base):
    __tablename__ = "conjunto"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    latitud = Column(Numeric(10, 8), nullable=False, default=0.0)
    longitud = Column(Numeric(11, 8), nullable=False, default=0.0)
    descripcion = Column(Text)
    usuario_id = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)

    usuario = relationship("UsuarioDB", back_populates="conjuntos")
    maquinas = relationship("MaquinaDB", back_populates="conjunto")

class MaquinaDB(Base):
    __tablename__ = "maquinas"
    id_maquina = Column(String(50), primary_key=True, index=True)
    ubicacion = Column(String(150), default="Por Asignar")
    estado = Column(String(20), default="ACTIVA")
    conjunto_id = Column(Integer, ForeignKey("conjunto.id", ondelete="SET NULL"), nullable=True)

    conjunto = relationship("ConjuntoDB", back_populates="maquinas")
    recaudos = relationship("RecaudoDB", back_populates="maquina")

class RecaudoDB(Base):
    __tablename__ = "recaudos"
    id = Column(Integer, primary_key=True, index=True)
    id_maquina = Column(String(50), ForeignKey("maquinas.id_maquina"))
    monto = Column(Integer, nullable=False)
    fecha_hora = Column(DateTime, default=func.now())

    maquina = relationship("MaquinaDB", back_populates="recaudos")

Base.metadata.create_all(bind=motor)

# --- ESQUEMAS PYDANTIC ---
class RecaudoEntrante(BaseModel):
    sitio: str
    recaudo: int
    timestamp: float

class Token(BaseModel):
    access_token: str
    token_type: str
    rol: str
    nombre: str

class UsuarioCrear(BaseModel):
    nombre: str
    email: str
    password: str
    telefono: Optional[str] = None
    rol: str = "cliente"

class ConjuntoCrear(BaseModel):
    nombre: str
    latitud: float = 0.0
    longitud: float = 0.0
    descripcion: Optional[str] = None
    usuario_id: int

class MaquinaCrear(BaseModel):
    id_maquina: str
    ubicacion: str
    conjunto_id: int

# --- FUNCIONES DE AUTENTICACIÓN ---
def verificar_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def obtener_password_hash(password):
    return pwd_context.hash(password)

def crear_token_acceso(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_db():
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()

def obtener_usuario_actual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UsuarioDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales no válidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    usuario = db.query(UsuarioDB).filter(UsuarioDB.email == email).first()
    if usuario is None:
        raise credentials_exception
    return usuario

def verificar_superadmin(usuario: UsuarioDB = Depends(obtener_usuario_actual)):
    if usuario.rol != "superadmin":
        raise HTTPException(status_code=403, detail="Permisos insuficientes. Solo superadmin.")
    return usuario

# --- INICIALIZACIÓN DE LA APP ---
app = FastAPI(title="KAEL API Central")

app.mount("/static", StaticFiles(directory="."), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- RUTAS DE LA API ---
@app.get("/", response_class=HTMLResponse)
async def MostrarPage():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/login", response_class=HTMLResponse)
async def servir_interfaz():
    with open("dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# LOGIN
@app.post("/api/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(UsuarioDB).filter(UsuarioDB.email == form_data.username).first()
    if not usuario or not verificar_password(form_data.password, usuario.password):
        raise HTTPException(status_code=400, detail="Correo o contraseña incorrectos")
    
    access_token = crear_token_acceso(data={"sub": usuario.email, "rol": usuario.rol})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "rol": usuario.rol,
        "nombre": usuario.nombre
    }

# RECEPCIÓN DE RECAUDO DESDE LAS BEAGLEBONES
@app.post("/api/recaudo")
def recibir_recaudo(datos: RecaudoEntrante, db: Session = Depends(get_db)):
    maquina = db.query(MaquinaDB).filter(MaquinaDB.id_maquina == datos.sitio).first()
    if not maquina:
        maquina = MaquinaDB(id_maquina=datos.sitio, ubicacion="Por Asignar", estado="ACTIVA")
        db.add(maquina)
        db.flush()

    nuevo_recaudo = RecaudoDB(id_maquina=datos.sitio, monto=datos.recaudo)
    db.add(nuevo_recaudo)
    db.commit()
    return {"status": "ok", "mensaje": "Recaudo guardado"}

# OBTENER CONJUNTOS
@app.get("/api/conjuntos")
def obtener_conjuntos(db: Session = Depends(get_db), usuario_actual: UsuarioDB = Depends(obtener_usuario_actual)):
    if usuario_actual.rol == "superadmin":
        conjuntos = db.query(ConjuntoDB).all()
    else:
        conjuntos = db.query(ConjuntoDB).filter(ConjuntoDB.usuario_id == usuario_actual.id).all()

    resultado = []
    for c in conjuntos:
        total_conjunto = db.query(func.sum(RecaudoDB.monto))\
                           .join(MaquinaDB, RecaudoDB.id_maquina == MaquinaDB.id_maquina)\
                           .filter(MaquinaDB.conjunto_id == c.id).scalar() or 0
                           
        resultado.append({
            "id": c.id,
            "nombre": c.nombre,
            "propietario": c.usuario.nombre if c.usuario else "Sin Propietario",
            "descripcion": c.descripcion,
            "total_recaudado": total_conjunto,
            "totalAdmin": total_conjunto * 0.4,
            "totalKael": total_conjunto * 0.6
        })
    return {"conjuntos": resultado}

# OBTENER MÁQUINAS Y RECAUDOS DE UN CONJUNTO
@app.get("/api/conjunto/{conjunto_id}/maquinas")
def obtener_maquinas_conjunto(conjunto_id: int, db: Session = Depends(get_db), usuario_actual: UsuarioDB = Depends(obtener_usuario_actual)):
    conjunto = db.query(ConjuntoDB).filter(ConjuntoDB.id == conjunto_id).first()
    if not conjunto:
        raise HTTPException(status_code=404, detail="Conjunto no encontrado")

    if usuario_actual.rol != "superadmin" and conjunto.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver este conjunto")

    maquinas = db.query(MaquinaDB).filter(MaquinaDB.conjunto_id == conjunto_id).all()
    
    resultado = []
    for m in maquinas:
        total_m = db.query(func.sum(RecaudoDB.monto)).filter(RecaudoDB.id_maquina == m.id_maquina).scalar() or 0
        conteo_transacciones = db.query(func.count(RecaudoDB.id)).filter(RecaudoDB.id_maquina == m.id_maquina).scalar() or 0
        
        resultado.append({
            "id_maquina": m.id_maquina,
            "ubicacion": m.ubicacion,
            "estado": m.estado,
            "total_recaudado": total_m,
            "totalAdmin": total_m * 0.4,
            "totalKael": total_m * 0.6,
            "transacciones": conteo_transacciones
        })
    return {
        "conjunto": conjunto.nombre, 
        "propietario": conjunto.usuario.nombre, 
        "maquinas": resultado
    }

# --- RUTAS EXCLUSIVAS PARA SUPERADMIN ---

@app.get("/api/usuarios")
def listar_usuarios(db: Session = Depends(get_db), admin: UsuarioDB = Depends(verificar_superadmin)):
    usuarios = db.query(UsuarioDB).all()
    return [{"id": u.id, "nombre": u.nombre, "email": u.email, "rol": u.rol} for u in usuarios]

@app.post("/api/usuarios")
def crear_usuario(datos: UsuarioCrear, db: Session = Depends(get_db), admin: UsuarioDB = Depends(verificar_superadmin)):
    existe = db.query(UsuarioDB).filter(UsuarioDB.email == datos.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    hashed_pwd = obtener_password_hash(datos.password)
    nuevo_usuario = UsuarioDB(
        nombre=datos.nombre, 
        email=datos.email, 
        password=hashed_pwd, 
        rol=datos.rol, 
        telefono=datos.telefono
    )
    db.add(nuevo_usuario)
    db.commit()
    return {"mensaje": "Usuario creado exitosamente"}

@app.post("/api/conjunto")
def crear_conjunto(datos: ConjuntoCrear, db: Session = Depends(get_db), admin: UsuarioDB = Depends(verificar_superadmin)):
    nuevo_conjunto = ConjuntoDB(
        nombre=datos.nombre,
        latitud=datos.latitud,
        longitud=datos.longitud,
        descripcion=datos.descripcion,
        usuario_id=datos.usuario_id
    )
    db.add(nuevo_conjunto)
    db.commit()
    return {"mensaje": "Conjunto creado exitosamente"}

@app.post("/api/maquina")
def crear_maquina(datos: MaquinaCrear, db: Session = Depends(get_db), admin: UsuarioDB = Depends(verificar_superadmin)):
    existe = db.query(MaquinaDB).filter(MaquinaDB.id_maquina == datos.id_maquina).first()
    if existe:
        raise HTTPException(status_code=400, detail="El ID de la máquina ya existe")
    
    nueva_maquina = MaquinaDB(
        id_maquina=datos.id_maquina, 
        ubicacion=datos.ubicacion, 
        conjunto_id=datos.conjunto_id,
        estado="ACTIVA"
    )
    db.add(nueva_maquina)
    db.commit()
    return {"mensaje": "Máquina agregada exitosamente"}

@app.put("/api/maquina/{id_maquina}/estado")
def cambiar_estado_maquina(id_maquina: str, db: Session = Depends(get_db), admin: UsuarioDB = Depends(verificar_superadmin)):
    maquina = db.query(MaquinaDB).filter(MaquinaDB.id_maquina == id_maquina).first()
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")
    
    maquina.estado = "INACTIVA" if maquina.estado == "ACTIVA" else "ACTIVA"
    db.commit()
    return {"mensaje": f"Estado cambiado a {maquina.estado}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    