from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
import enum
from database import Base  # Asumiendo que tienes tu base de datos configurada



class RolEnum(str, enum.Enum):
    SUPERADMIN = "superadmin"                # Tú / KAEL Master (Acceso total global)
    ADMIN = "admin"                          # Administrador del conjunto (Gestiona sus conjuntos, máquinas y recaudo)
    AUX_ADMIN = "aux_admin"                  # Auxiliar administrativo (Acceso a máquinas del conjunto asignado)
    AUX_MANTENIMIENTO = "aux_mantenimiento"  # Auxiliar técnico KAEL (Acceso a máquinas, ubicación y mantenimientos)

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    rol = Column(String, nullable=False, default=RolEnum.ADMIN)
    
    # Si es Admin, posee una lista de Conjuntos
    conjuntos = relationship("Conjunto", back_populates="administrador", cascade="all, delete-orphan")
    
    # Si es auxiliar (administrativo o mantenimiento), puede estar ligado a un conjunto específico o trabajar globalmente
    conjunto_id = Column(Integer, ForeignKey("conjuntos.id"), nullable=True)

class Conjunto(Base):
    __tablename__ = "conjuntos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    direccion = Column(String, nullable=False)
    
    # Administrador dueño de este conjunto
    administrador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    administrador = relationship("Usuario", back_populates="conjuntos", foreign_keys=[administrador_id])
    
    # Máquinas instaladas en este conjunto
    maquinas = relationship("Maquina", back_populates="conjunto", cascade="all, delete-orphan")

class Maquina(Base):
    __tablename__ = "maquinas"

    id = Column(Integer, primary_key=True, index=True)
    nombre_sitio = Column(String, nullable=False) # Ej: Aspiradora-Torre-A
    ubicacion = Column(String, nullable=False)      # Ej: Sótano 2, Parqueadero visitantes
    
    conjunto_id = Column(Integer, ForeignKey("conjuntos.id"), nullable=False)
    conjunto = relationship("Conjunto", back_populates="maquinas")
    
    recaudos = relationship("Recaudo", back_populates="maquina", cascade="all, delete-orphan")
    mantenimientos = relationship("Mantenimiento", back_populates="maquina", cascade="all, delete-orphan")

class Recaudo(Base):
    __tablename__ = "recaudos"

    id = Column(Integer, primary_key=True, index=True)
    maquina_id = Column(Integer, ForeignKey("maquinas.id"), nullable=False)
    monto = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    maquina = relationship("Maquina", back_populates="recaudos")

class Mantenimiento(Base):
    __tablename__ = "mantenimiento"

    id = Column(Integer, primary_key=True, index=True)
    maquina_id = Column(Integer, ForeignKey("maquinas.id"), nullable=False)
    descripcion = Column(String, nullable=False)  # Ej: Cambio de filtros, revisión de monedero
    fecha = Column(DateTime, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False) # Quién hizo el mantenimiento
    
    maquina = relationship("Maquina", back_populates="mantenimientos")
    