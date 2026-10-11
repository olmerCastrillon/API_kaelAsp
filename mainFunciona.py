from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Numeric, Text, func, cast, Date
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

# --- CONFIGURACIÓN DE POSTGRESQL ---
DATABASE_URL = "postgresql://postgres:Lag11Msu@localhost/kael_db"

motor = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20
)
SesionLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor)
Base = declarative_base()

# --- MODELOS DE BASE DE DATOS ---

class UsuarioDB(Base):
    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(20))
    rol = Column(String(50), nullable=False, default="cliente")
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    conjuntos = relationship("ConjuntoDB", back_populates="usuario")

class ConjuntoDB(Base):
    __tablename__ = "conjunto"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    latitud = Column(Numeric(10, 8), nullable=False)
    longitud = Column(Numeric(11, 8), nullable=False)
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

# Crear tablas en caso de que no existan
Base.metadata.create_all(bind=motor)

# --- ESQUEMAS (Pydantic) ---
# Estructura del JSON enviado por las BeagleBones
class RecaudoEntrante(BaseModel):
    sitio: str
    recaudo: int
    timestamp: float

# --- INICIALIZACIÓN DE LA APP ---
app = FastAPI(title="KAEL API Central")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()

# --- RUTAS DE LA API ---

@app.get("/", response_class=HTMLResponse)
@app.get("/admin", response_class=HTMLResponse)
async def ver_dashboard_central():
    with open("dashboard.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# Endpoint que recibe la información del IoT
@app.post("/api/recaudo")
def recibir_recaudo(datos: RecaudoEntrante, db: Session = Depends(get_db)):
    # 1. Verificar si la máquina ya existe en la base de datos
    maquina = db.query(MaquinaDB).filter(MaquinaDB.id_maquina == datos.sitio).first()
    
    # 2. Si no existe, crear la referencia base para evitar fallos de llave foránea
    if not maquina:
        maquina = MaquinaDB(
            id_maquina=datos.sitio, 
            ubicacion="Por Asignar", 
            estado="ACTIVA"
        )
        db.add(maquina)
        db.flush()  # Garantiza que el id_maquina esté disponible en la transacción actual

    # 3. Registrar el recaudo vinculado a la máquina
    nuevo_recaudo = RecaudoDB(id_maquina=datos.sitio, monto=datos.recaudo)
    db.add(nuevo_recaudo)
    db.commit()
    
    return {"status": "ok", "mensaje": "Recaudo guardado exitosamente"}

# Reporte para las gráficas y resumen del dashboard
@app.get("/api/reportes/resumen")
def obtener_resumen_administrativo(db: Session = Depends(get_db)):
    resultados = db.query(
        RecaudoDB.id_maquina, 
        func.sum(RecaudoDB.monto).label("total_recaudado"),
        func.count(RecaudoDB.id).label("cantidad_transacciones")
    ).group_by(RecaudoDB.id_maquina).all()

    reporte = []
    for id_maq, total, cantidad in resultados:
        maquina = db.query(MaquinaDB).filter(MaquinaDB.id_maquina == id_maq).first()
        
        conjunto_nombre = maquina.conjunto.nombre if (maquina and maquina.conjunto) else "Sin Asignar"
        usuario_nombre = maquina.conjunto.usuario.nombre if (maquina and maquina.conjunto and maquina.conjunto.usuario) else "Sin Asignar"
        
        reporte.append({
            "maquina": id_maq,
            "conjunto": conjunto_nombre,
            "propietario": usuario_nombre,
            "total_dinero": total or 0,
            "transacciones": cantidad or 0
        })
    return {"reporte": reporte}

# Reporte agrupado por día
@app.get("/api/reportes/diario")
def obtener_reporte_diario(db: Session = Depends(get_db)):
    resultados = db.query(
        RecaudoDB.id_maquina,
        cast(RecaudoDB.fecha_hora, Date).label('fecha'),
        func.sum(RecaudoDB.monto).label('total_dia')
    ).group_by(
        RecaudoDB.id_maquina,
        cast(RecaudoDB.fecha_hora, Date)
    ).order_by(
        cast(RecaudoDB.fecha_hora, Date).desc()
    ).all()

    reporte = []
    for id_maq, fecha, total in resultados:
        reporte.append({
            "sitio": id_maq,
            "fecha": str(fecha),
            "total": total or 0
        })
    return {"reporte_diario": reporte}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)