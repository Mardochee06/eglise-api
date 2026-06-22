from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class RoleEnum(str, enum.Enum):
    tresorier = "tresorier"   # Trésorier principal — accès total + comptes
    adjoint   = "adjoint"     # Trésorier adjoint — saisie complète
    consultation = "consultation"  # Pasteur, responsables — lecture seule

class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    nom        = Column(String(100), nullable=False)
    prenom     = Column(String(100), nullable=False)
    fonction   = Column(String(150), nullable=True)   # Pasteur, Trésorier, etc.
    telephone  = Column(String(30), nullable=True)
    email      = Column(String(150), unique=True, nullable=False, index=True)
    password   = Column(String(255), nullable=False)
    role       = Column(Enum(RoleEnum), default=RoleEnum.consultation, nullable=False)
    is_active  = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
