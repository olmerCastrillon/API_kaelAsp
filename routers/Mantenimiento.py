from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from database import get_db
from models import Maquina, Mantenimiento, RolEnum, Usuario
from auth import verificar_rol

router = APIRouter(prefix="/api/mantenimiento", tags=["Mantenimiento Técnico KAEL"])

# Esquema para recibir el reporte de mantenimiento desde el frontend o app móvil
class MantenimientoCreate(BaseModel):
    maquina_id: int
    descripcion: str

@router.get("/maquinas-ubicacion")
def ver_ubicacion_maquinas_mantenimiento(db: Session = Depends(get_db), current_user: Usuario = Depends(verificar_rol([RolEnum.AUX_MANTENIMIENTO]))):
    maquinas = db.query(Maquina).all()
    # Retorna la lista con los datos clave para el técnico en campo
    return [
        {
            "id": m.id,
            "nombre_sitio": m.nombre_sitio,
            "ubicacion": m.ubicacion,
            "conjunto_id": m.conjunto_id
        } for m in maquinas
    ]

@router.post("/registrar")
def registrar_soporte_tecnico(data: MantenimientoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(verificar_rol([RolEnum.AUX_MANTENIMIENTO]))):
    nueva_tarea = Mantenimiento(
        maquina_id=data.maquina_id,
        descripcion=data.descripcion,
        fecha=datetime.now(),
        usuario_id=current_user.id
    )
    db.add(nueva_tarea)
    db.commit()
    db.refresh(nueva_tarea)
    
    return {"mensaje": "Mantenimiento registrado correctamente", "mantenimiento_id": nueva_tarea.id}
