from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from typing import List
from datetime import date
from app.core.database import get_db
from app.core.security import get_current_user, require_tresorier
from app.models.tresorerie import Session, LigneOperation, Config, TypeLigne, Libelle
from app.schemas.schemas import (
    SessionCreate, SessionUpdate, SessionDetail, SessionResume,
    LigneCreate, LigneOut, LigneAvecSolde, BenBerRequest, BenBerConfig, ConfigOut
)

router = APIRouter(prefix="/sessions", tags=["Sessions de culte"])

# ── Helpers ──────────────────────────────────────────────
def get_taux(db: DBSession):
    def val(key, default):
        c = db.query(Config).filter(Config.key == key).first()
        return float(c.value) if c else default
    return val("taux_ben", 10.0), val("taux_ber", 5.0)

def compute_session(session: Session):
    """Calcule totaux + solde courant ligne par ligne."""
    solde = session.solde_initial
    total_e = total_s = 0
    lignes_out = []
    for l in session.lignes:
        if l.type == TypeLigne.entree:
            solde += l.montant; total_e += l.montant
        else:
            solde -= l.montant; total_s += l.montant
        lignes_out.append(LigneAvecSolde(
            id=l.id, type=l.type, designation=l.designation,
            montant=l.montant, is_ben_ber=l.is_ben_ber, solde_apres=solde
        ))
    return total_e, total_s, solde, lignes_out

def build_detail(session: Session) -> SessionDetail:
    total_e, total_s, solde_final, lignes = compute_session(session)
    return SessionDetail(
        id=session.id, date_culte=session.date_culte, libelle_culte=session.libelle_culte,
        solde_initial=session.solde_initial, cloturee=session.cloturee,
        total_entrees=total_e, total_sorties=total_s, solde_final=solde_final, lignes=lignes
    )

def last_solde_final(db: DBSession) -> int:
    """Solde final de la dernière session clôturée (pour report auto)."""
    last = db.query(Session).order_by(desc(Session.date_culte), desc(Session.id)).first()
    if not last:
        return 0
    _, _, solde, _ = compute_session(last)
    return solde

# ── Liste des sessions ───────────────────────────────────
@router.get("/", response_model=List[SessionResume])
def list_sessions(db: DBSession = Depends(get_db), current_user=Depends(get_current_user)):
    sessions = db.query(Session).order_by(desc(Session.date_culte), desc(Session.id)).all()
    out = []
    for s in sessions:
        te, ts, sf, _ = compute_session(s)
        out.append(SessionResume(
            id=s.id, date_culte=s.date_culte, libelle_culte=s.libelle_culte,
            solde_initial=s.solde_initial, total_entrees=te, total_sorties=ts,
            solde_final=sf, cloturee=s.cloturee
        ))
    return out

# ── Détail d'une session ─────────────────────────────────
@router.get("/{session_id}", response_model=SessionDetail)
def get_session(session_id: int, db: DBSession = Depends(get_db), current_user=Depends(get_current_user)):
    s = db.query(Session).filter(Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return build_detail(s)

# ── Créer une session ────────────────────────────────────
@router.post("/", response_model=SessionDetail)
def create_session(payload: SessionCreate, db: DBSession = Depends(get_db), _=Depends(require_tresorier)):
    solde_init = payload.solde_initial if payload.solde_initial is not None else last_solde_final(db)
    s = Session(
        date_culte=payload.date_culte, libelle_culte=payload.libelle_culte,
        solde_initial=solde_init
    )
    db.add(s); db.commit(); db.refresh(s)
    return build_detail(s)

# ── Modifier une session ─────────────────────────────────
@router.put("/{session_id}", response_model=SessionDetail)
def update_session(session_id: int, payload: SessionUpdate, db: DBSession = Depends(get_db), _=Depends(require_tresorier)):
    s = db.query(Session).filter(Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session introuvable")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit(); db.refresh(s)
    return build_detail(s)

# ── Supprimer une session ────────────────────────────────
@router.delete("/{session_id}")
def delete_session(session_id: int, db: DBSession = Depends(get_db), _=Depends(require_tresorier)):
    s = db.query(Session).filter(Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session introuvable")
    db.delete(s); db.commit()
    return {"message": "Session supprimée"}

# ── Ajouter une ligne ────────────────────────────────────
@router.post("/{session_id}/lignes", response_model=SessionDetail)
def add_ligne(session_id: int, payload: LigneCreate, db: DBSession = Depends(get_db), _=Depends(require_tresorier)):
    s = db.query(Session).filter(Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session introuvable")
    if s.cloturee:
        raise HTTPException(status_code=400, detail="Session clôturée, modification impossible")
    ligne = LigneOperation(
        session_id=session_id, type=payload.type,
        designation=payload.designation, montant=payload.montant
    )
    db.add(ligne); db.commit(); db.refresh(s)
    return build_detail(s)

# ── Supprimer une ligne ──────────────────────────────────
@router.delete("/{session_id}/lignes/{ligne_id}", response_model=SessionDetail)
def delete_ligne(session_id: int, ligne_id: int, db: DBSession = Depends(get_db), _=Depends(require_tresorier)):
    s = db.query(Session).filter(Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session introuvable")
    if s.cloturee:
        raise HTTPException(status_code=400, detail="Session clôturée, modification impossible")
    ligne = db.query(LigneOperation).filter(LigneOperation.id == ligne_id, LigneOperation.session_id == session_id).first()
    if ligne:
        db.delete(ligne); db.commit(); db.refresh(s)
    return build_detail(s)

# ── Calculer et ajouter BEN/BER ──────────────────────────
@router.post("/{session_id}/ben-ber", response_model=SessionDetail)
def calculer_ben_ber(session_id: int, payload: BenBerRequest, db: DBSession = Depends(get_db), _=Depends(require_tresorier)):
    s = db.query(Session).filter(Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session introuvable")
    if s.cloturee:
        raise HTTPException(status_code=400, detail="Session clôturée")

    taux_ben, taux_ber = get_taux(db)

    # Base = somme des entrées Offrandes + Dîmes (ou valeur fournie)
    if payload.base_offrandes is not None:
        base = payload.base_offrandes
    else:
        base = 0
        for l in s.lignes:
            if l.type == TypeLigne.entree and not l.is_ben_ber:
                nom = l.designation.lower()
                if "offrande" in nom or "dime" in nom or "dîme" in nom:
                    base += l.montant

    # Supprimer d'anciennes lignes BEN/BER pour recalcul propre
    for l in list(s.lignes):
        if l.is_ben_ber:
            db.delete(l)
    db.commit(); db.refresh(s)

    montant_ben = round(base * taux_ben / 100)
    montant_ber = round(base * taux_ber / 100)

    db.add(LigneOperation(session_id=session_id, type=TypeLigne.sortie,
        designation=f"BEN ({taux_ben:g}%)", montant=montant_ben, is_ben_ber=True))
    db.add(LigneOperation(session_id=session_id, type=TypeLigne.sortie,
        designation=f"BER ({taux_ber:g}%)", montant=montant_ber, is_ben_ber=True))
    db.commit(); db.refresh(s)
    return build_detail(s)
