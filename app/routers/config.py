from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession
from app.core.database import get_db
from app.core.security import get_current_user, require_tresorier
from app.models.tresorerie import Config
from app.schemas.schemas import BenBerConfig, ConfigOut

router = APIRouter(prefix="/config", tags=["Configuration"])

def get_taux(db: DBSession):
    def val(key, default):
        c = db.query(Config).filter(Config.key == key).first()
        return float(c.value) if c else default
    return val("taux_ben", 10.0), val("taux_ber", 5.0)

@router.get("/taux", response_model=ConfigOut)
def get_config(db: DBSession = Depends(get_db), current_user=Depends(get_current_user)):
    ben, ber = get_taux(db)
    return ConfigOut(taux_ben=ben, taux_ber=ber)

@router.put("/taux", response_model=ConfigOut)
def update_config(payload: BenBerConfig, db: DBSession = Depends(get_db), _=Depends(require_tresorier)):
    for key, value in [("taux_ben", payload.taux_ben), ("taux_ber", payload.taux_ber)]:
        c = db.query(Config).filter(Config.key == key).first()
        if c:
            c.value = str(value)
        else:
            db.add(Config(key=key, value=str(value)))
    db.commit()
    return ConfigOut(taux_ben=payload.taux_ben, taux_ber=payload.taux_ber)
