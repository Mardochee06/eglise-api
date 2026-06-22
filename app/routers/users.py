from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_admin, hash_password
from app.models.user import User
from app.schemas.schemas import UserCreate, UserOut, UserUpdate, UserUpdateAdmin

router = APIRouter(prefix="/users", tags=["Utilisateurs"])

@router.get("/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(User).order_by(User.nom).all()

@router.post("/", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    user = User(
        nom=payload.nom, prenom=payload.prenom, fonction=payload.fonction,
        telephone=payload.telephone, email=payload.email,
        password=hash_password(payload.password), role=payload.role,
    )
    db.add(user); db.commit(); db.refresh(user)
    return user

@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdateAdmin, db: Session = Depends(get_db), _=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    data = payload.model_dump(exclude_unset=True)
    if data.get("password"):
        data["password"] = hash_password(data["password"])
    for k, v in data.items():
        setattr(user, k, v)
    db.commit(); db.refresh(user)
    return user

@router.patch("/{user_id}/toggle-active", response_model=UserOut)
def toggle_active(user_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Impossible de désactiver votre propre compte")
    user.is_active = not user.is_active
    db.commit(); db.refresh(user)
    return user

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Impossible de supprimer votre propre compte")
    db.delete(user); db.commit()
    return {"message": f"{user.prenom} {user.nom} supprimé(e)"}

@router.put("/me/profile", response_model=UserOut)
def update_my_profile(payload: UserUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, k, v)
    db.commit(); db.refresh(current_user)
    return current_user
