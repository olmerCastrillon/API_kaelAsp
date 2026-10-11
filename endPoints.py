from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import Usuario, Conjunto, Maquina, Recaudo, Mantenimiento, RolEnum
from database import get_db

router = APIRouter(prefix="/api", tags=["Gestión Multi-Tenant KAEL"])

# 1. RUTA PARA SUPERADMIN (Tú): Ve absolutamente todo el sistema
@router.get("/superadmin/dashboard-global")
def ver_todo_global(db: Session = Depends(get_db), user: Usuario = Depends(verificar_rol([RolEnum.SUPERADMIN]))):
    conjuntos = db.query(Conjunto).all()
    maquinas = db.query(Maquina).all()
    recaudos_totales = db.query(Recaudo).all()
    return {
        "total_conjuntos": len(conjuntos),
        "total_maquinas": len(maquinas),
        "data_global": conjuntos
    }

# 2. RUTA PARA ADMINISTRADOR: Ve sus conjuntos, máquinas de su conjunto y sus recaudos
@router.get("/admin/mis-conjuntos")
def ver_conjuntos_admin(db: Session = Depends(get_db), current_user: Usuario = Depends(verificar_rol([RolEnum.ADMIN]))):
    # Si es Superadmin ve todos, si es Admin ve únicamente los suyos
    if current_user.rol == RolEnum.SUPERADMIN:
        return db.query(Conjunto).all()
    
    return db.query(Conjunto).filter(Conjunto.administrador_id == current_user.id).all()

# 3. RUTA PARA AUXILIAR ADMINISTRATIVO: Acceso exclusivo a las máquinas del conjunto asignado
@router.get("/aux-admin/maquinas")
def ver_maquinas_conjunto_asignado(db: Session = Depends(get_db), current_user: Usuario = Depends(verificar_rol([RolEnum.AUX_ADMIN]))):
    # El auxiliar solo ve las máquinas del conjunto al que está amarrado (current_user.conjunto_id)
    maquinas = db.query(Maquina).filter(Maquina.conjunto_id == current_user.conjunto_id).all()
    return {"conjunto_id": current_user.conjunto_id, "maquinas": maquinas}

# 4. RUTA PARA AUXILIAR DE MANTENIMIENTO KAEL: Acceso a máquinas, su ubicación y registrar mantenimientos
@router.get("/mantenimiento/maquinas-ubicacion")
def ver_ubicacion_maquinas_mantenimiento(db: Session = Depends(get_db), current_user: Usuario = Depends(verificar_rol([RolEnum.AUX_MANTENIMIENTO]))):
    # Ve las máquinas con su respectiva ubicación física para la labor técnica
    maquinas = db.query(Maquina.id, Maquina.nombre_sitio, Maquina.ubicacion, Maquina.conjunto_id).all()
    return maquinas
