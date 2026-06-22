from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_current_user, hash_password
from app.models.user import User
from app.schemas.schemas import LoginRequest, TokenResponse, UserOut, ChangePasswordRequest

router = APIRouter(prefix="/auth", tags=["Authentification"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé. Contactez le trésorier.")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))

@router.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_user)):
    return current_user

@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(payload.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="Ancien mot de passe incorrect")
    current_user.password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Mot de passe mis à jour"}
