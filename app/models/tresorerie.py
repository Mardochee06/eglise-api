from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Date, BigInteger, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class TypeLigne(str, enum.Enum):
    entree = "entree"
    sortie = "sortie"

class Libelle(Base):
    """Libellés pré-enregistrés (récurrents) — entrées et sorties."""
    __tablename__ = "libelles"

    id      = Column(Integer, primary_key=True, index=True)
    nom     = Column(String(150), nullable=False)
    type    = Column(Enum(TypeLigne), nullable=False)
    ordre   = Column(Integer, default=0)        # pour trier l'affichage
    actif   = Column(Boolean, default=True)
    is_ben_ber = Column(Boolean, default=False) # marque les libellés BEN/BER spéciaux

class Session(Base):
    """Une session = un culte (dimanche ou semaine)."""
    __tablename__ = "sessions"

    id            = Column(Integer, primary_key=True, index=True)
    date_culte    = Column(Date, nullable=False)
    libelle_culte = Column(String(150), default="Culte du dimanche")
    solde_initial = Column(BigInteger, nullable=False, default=0)
    cloturee      = Column(Boolean, default=False)   # une fois clôturée, plus de modif
    created_by    = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    lignes = relationship("LigneOperation", back_populates="session", cascade="all, delete-orphan", order_by="LigneOperation.id")

class LigneOperation(Base):
    """Chaque entrée ou sortie d'une session."""
    __tablename__ = "lignes"

    id          = Column(Integer, primary_key=True, index=True)
    session_id  = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    type        = Column(Enum(TypeLigne), nullable=False)
    designation = Column(String(200), nullable=False)
    montant     = Column(BigInteger, nullable=False, default=0)
    is_ben_ber  = Column(Boolean, default=False)  # ligne générée par le calcul BEN/BER
    ordre       = Column(Integer, default=0)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="lignes")

class Config(Base):
    """Paramètres globaux : taux BEN, taux BER, etc."""
    __tablename__ = "config"

    id    = Column(Integer, primary_key=True)
    key   = Column(String(50), unique=True, nullable=False)
    value = Column(String(255), nullable=False)
