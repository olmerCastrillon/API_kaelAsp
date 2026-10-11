from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configura tu conexión a PostgreSQL: 
# "postgresql://usuario:contraseña@localhost:5432/nombre_de_tu_base"
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Lag11Msu@localhost:5432/kael_db"

# Creación del motor de base de datos
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Fábrica de sesiones para las transacciones con la BD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa para que tus modelos hereden de ella (class Maquina(Base): ...)
Base = declarative_base()

# Dependencia de FastAPI para inyectar la sesión en cada petición
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        