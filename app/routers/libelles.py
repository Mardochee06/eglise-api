from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_tresorier
from app.models.tresorerie import Libelle
from app.schemas.schemas import LibelleCreate, LibelleOut, LibelleUpdate

router = APIRouter(prefix="/libelles", tags=["Libellés"])

@router.get("/", response_model=List[LibelleOut])
def list_libelles(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(Libelle).filter(Libelle.actif == True).order_by(Libelle.type, Libelle.ordre, Libelle.nom).all()

@router.post("/", response_model=LibelleOut)
def create_libelle(payload: LibelleCreate, db: Session = Depends(get_db), _=Depends(require_tresorier)):
    lib = Libelle(nom=payload.nom, type=payload.type, ordre=payload.ordre)
    db.add(lib); db.commit(); db.refresh(lib)
    return lib

@router.put("/{lib_id}", response_model=LibelleOut)
def update_libelle(lib_id: int, payload: LibelleUpdate, db: Session = Depends(get_db), _=Depends(require_tresorier)):
    lib = db.query(Libelle).filter(Libelle.id == lib_id).first()
    if not lib:
        raise HTTPException(status_code=404, detail="Libellé introuvable")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(lib, k, v)
    db.commit(); db.refresh(lib)
    return lib

@router.delete("/{lib_id}")
def delete_libelle(lib_id: int, db: Session = Depends(get_db), _=Depends(require_tresorier)):
    lib = db.query(Libelle).filter(Libelle.id == lib_id).first()
    if not lib:
        raise HTTPException(status_code=404, detail="Libellé introuvable")
    if lib.is_ben_ber:
        raise HTTPException(status_code=400, detail="Les libellés BEN/BER ne peuvent pas être supprimés")
    lib.actif = False  # soft delete
    db.commit()
    return {"message": "Libellé supprimé"}
