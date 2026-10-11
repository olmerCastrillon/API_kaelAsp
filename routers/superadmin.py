from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Usuario, Conjunto, Maquina, Recaudo, RolEnum
from auth import verificar_rol

router = APIRouter(prefix="/api/superadmin", tags=["Superadmin (KAEL Master)"])

@router.get("/dashboard-global")
def ver_todo_global(db: Session = Depends(get_db), current_user: Usuario = Depends(verificar_rol([RolEnum.SUPERADMIN]))):
    conjuntos = db.query(Conjunto).all()
    maquinas = db.query(Maquina).all()
    recaudos = db.query(Recaudo).all()
    
    ingresos_totales = sum(r.monto for r in recaudos)
    
    return {
        "total_conjuntos": len(conjuntos),
        "total_maquinas": len(maquinas),
        "ingresos_globales": ingresos_totales,
        "conjuntos": conjuntos
    }
