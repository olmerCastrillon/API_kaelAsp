from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Maquina, RolEnum, Usuario
from auth import verificar_rol

router = APIRouter(prefix="/api/aux_admin", tags=["Auxiliar Administrativo"])

@router.get("/maquinas")
def ver_maquinas_conjunto_asignado(db: Session = Depends(get_db), current_user: Usuario = Depends(verificar_rol([RolEnum.AUX_ADMIN]))):
    if not current_user.conjunto_id:
        raise HTTPException(status_code=400, detail="El auxiliar no tiene un conjunto asignado en el sistema.")
    
    maquinas = db.query(Maquina).filter(Maquina.conjunto_id == current_user.conjunto_id).all()
    return {
        "conjunto_id": current_user.conjunto_id,
        "maquinas": maquinas
    }
