from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.routers import auth, users, libelles, sessions, config
from app.core.security import hash_password

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Trésorerie Église EADC — API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(libelles.router)
app.include_router(sessions.router)
app.include_router(config.router)

@app.get("/")
def root():
    return {"message": "Trésorerie Église EADC API v1.0", "status": "ok"}

@app.on_event("startup")
def seed():
    from app.core.database import SessionLocal
    from app.models.user import User, RoleEnum
    from app.models.tresorerie import Libelle, Config, TypeLigne

    db = SessionLocal()
    try:
        # Compte trésorier principal par défaut
        if not db.query(User).filter(User.email == "tresorier@eadc.org").first():
            db.add(User(
                nom="Trésorier", prenom="Principal", fonction="Trésorier",
                email="tresorier@eadc.org", password=hash_password("eadc2024!"),
                role=RoleEnum.tresorier, is_active=True
            ))

        # Libellés d'entrée récurrents
        entrees = ["Offrandes Ordinaires", "Dîmes", "Offrandes Spéciales"]
        # Libellés de sortie récurrents (extraits du cahier)
        sorties = [
            "Déplacement Famille Pastorale", "Communication + Internet",
            "Achat Carburant", "Achat Pils", "Achat Pack d'eau",
            "Achat Vin (Sainte Cène)", "Déplacement Fr William",
            "Déplacement Fr André", "Déplacement Sr Yvette",
            "Droit Statutaire", "Réparation Piano", "Achat Cahier-Journal",
        ]

        if db.query(Libelle).count() == 0:
            for i, nom in enumerate(entrees):
                db.add(Libelle(nom=nom, type=TypeLigne.entree, ordre=i))
            for i, nom in enumerate(sorties):
                db.add(Libelle(nom=nom, type=TypeLigne.sortie, ordre=i))

        # Taux BEN/BER par défaut (à ajuster quand la vraie formule sera connue)
        for key, val in [("taux_ben", "10"), ("taux_ber", "5")]:
            if not db.query(Config).filter(Config.key == key).first():
                db.add(Config(key=key, value=val))

        db.commit()
    finally:
        db.close()
