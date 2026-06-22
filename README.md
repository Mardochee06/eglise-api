# Trésorerie Église EADC — API

Backend FastAPI pour la gestion de la trésorerie d'une église (Assemblées de Dieu du Congo).

## Principe
Registre par session de culte avec solde courant calculé automatiquement.
Chaque culte : solde initial (reporté) → entrées → sorties → BEN/BER → solde final.

## Rôles
- `tresorier` : accès total + gestion des comptes
- `adjoint` : saisie complète
- `consultation` : lecture seule (pasteur, responsables)

## BEN / p
Reversements calculés sur (Offrandes + Dîmes) × taux configurable.
- BEN → Bureau National (EADC)
- BER → Bureau Régional
Les taux se règlent dans Configuration (par défaut 10% et 5%, à ajuster).

## Compte initial
- Email : tresorier@eadc.org
- Mot de passe : eadc2024!
(à changer en production)

## Déploiement Railway
1. Pousser sur GitHub
2. Railway → Deploy from GitHub repo
3. Ajouter MySQL
4. Variables : DATABASE_URL (mysql+pymysql://...), SECRET_KEY, ALGORITHM=HS256, PORT=8080
5. Generate Domain (port 8080)
