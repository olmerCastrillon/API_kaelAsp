from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Conjunto, Maquina, RolEnum, Usuario
from auth import verificar_rol

router = APIRouter(prefix="/api/admin", tags=["Administradores de Conjuntos"])

@router.get("/mis-conjuntos")
def ver_conjuntos_admin(db: Session = Depends(get_db), current_user: Usuario = Depends(verificar_rol([RolEnum.ADMIN]))):
    # Si es Administrador, devuelve únicamente los conjuntos que le pertenecen
    return db.query(Conjunto).filter(Conjunto.administrador_id == current_user.id).all()

@router.get("/conjunto/{conjunto_id}/maquinas")
def ver_maquinas_de_conjunto(conjunto_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(verificar_rol([RolEnum.ADMIN]))):
    # Validar que el conjunto pertenezca al administrador logueado
    conjunto = db.query(Conjunto).filter(Conjunto.id == conjunto_id).first()
    if not conjunto:
        raise HTTPException(status_code=404, detail="Conjunto residencial no encontrado.")
    
    if current_user.rol != RolEnum.SUPERADMIN and conjunto.administrador_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver este conjunto.")
    
    maquinas = db.query(Maquina).filter(Maquina.conjunto_id == conjunto_id).all()
    return maquinas