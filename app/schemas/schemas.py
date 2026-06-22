from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime, date
from app.models.user import RoleEnum
from app.models.tresorerie import TypeLigne

# ── AUTH ──
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    @field_validator("new_password")
    def min_length(cls, v):
        if len(v) < 6:
            raise ValueError("Le mot de passe doit faire au moins 6 caractères")
        return v

# ── USERS ──
class UserCreate(BaseModel):
    nom: str
    prenom: str
    fonction: Optional[str] = None
    telephone: Optional[str] = None
    email: EmailStr
    password: str
    role: RoleEnum = RoleEnum.consultation

class UserUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    fonction: Optional[str] = None
    telephone: Optional[str] = None

class UserUpdateAdmin(UserUpdate):
    email: Optional[EmailStr] = None
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserOut(BaseModel):
    id: int
    nom: str
    prenom: str
    fonction: Optional[str]
    telephone: Optional[str]
    email: str
    role: RoleEnum
    is_active: bool
    created_at: Optional[datetime]
    class Config:
        from_attributes = True

# ── LIBELLES ──
class LibelleCreate(BaseModel):
    nom: str
    type: TypeLigne
    ordre: int = 0

class LibelleUpdate(BaseModel):
    nom: Optional[str] = None
    type: Optional[TypeLigne] = None
    ordre: Optional[int] = None
    actif: Optional[bool] = None

class LibelleOut(BaseModel):
    id: int
    nom: str
    type: TypeLigne
    ordre: int
    actif: bool
    is_ben_ber: bool
    class Config:
        from_attributes = True

# ── LIGNES ──
class LigneCreate(BaseModel):
    type: TypeLigne
    designation: str
    montant: int

class LigneOut(BaseModel):
    id: int
    type: TypeLigne
    designation: str
    montant: int
    is_ben_ber: bool
    class Config:
        from_attributes = True

# ── SESSIONS ──
class SessionCreate(BaseModel):
    date_culte: date
    libelle_culte: str = "Culte du dimanche"
    solde_initial: Optional[int] = None  # si absent → report auto du dernier solde

class SessionUpdate(BaseModel):
    date_culte: Optional[date] = None
    libelle_culte: Optional[str] = None
    solde_initial: Optional[int] = None
    cloturee: Optional[bool] = None

class LigneAvecSolde(LigneOut):
    solde_apres: int

class SessionDetail(BaseModel):
    id: int
    date_culte: date
    libelle_culte: str
    solde_initial: int
    cloturee: bool
    total_entrees: int
    total_sorties: int
    solde_final: int
    lignes: List[LigneAvecSolde]
    class Config:
        from_attributes = True

class SessionResume(BaseModel):
    id: int
    date_culte: date
    libelle_culte: str
    solde_initial: int
    total_entrees: int
    total_sorties: int
    solde_final: int
    cloturee: bool

# ── BEN/BER ──
class BenBerRequest(BaseModel):
    """Calcule et ajoute les lignes BEN et BER à une session."""
    base_offrandes: Optional[int] = None  # si absent → somme auto des entrées offrandes+dîmes

class BenBerConfig(BaseModel):
    taux_ben: float  # en pourcentage, ex: 10 pour 10%
    taux_ber: float

# ── CONFIG ──
class ConfigOut(BaseModel):
    taux_ben: float
    taux_ber: float
