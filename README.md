# Gestion des tâches étudiantes — Study Task

Application web Django permettant à un étudiant d'organiser ses matières, tâches, échéances, calendrier, statistiques et emploi du temps.

## Fonctionnalités

- Inscription, connexion, déconnexion et profil étudiant.
- Isolation stricte des données par utilisateur.
- CRUD des matières avec couleur, code, enseignant et description.
- CRUD des tâches avec type, priorité, statut, échéance, heure et durée estimée.
- Marquage terminé / remise en cours avec conservation de `completed_at`.
- Recherche, filtres combinés et tri des tâches.
- Vue liste et vue Kanban.
- Dashboard avec tâches du jour, tâches urgentes, échéances, rappels et progression réelle.
- Calendrier mensuel et vue par journée.
- Page échéances : aujourd'hui, demain, semaine, en retard.
- Page “Ma semaine” avec charge de travail estimée.
- Emploi du temps hebdomadaire.
- Statistiques globales, par matière et évolution des tâches terminées.
- Notifications internes calculées à partir des vraies échéances.
- Interface responsive desktop, tablette et mobile.

## Stack technique

- Python 3.11+
- Django 5
- SQLite en développement
- Django Templates
- CSS personnalisé responsive
- JavaScript léger

## Installation locale

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

L'application sera disponible sur :

```text
http://127.0.0.1:8000/
```

## Données de démonstration

Une commande facultative crée un compte de démo avec 5 matières, 15 tâches et quelques créneaux d'emploi du temps :

```bash
python manage.py seed_demo --reset
```

Identifiants de démonstration :

```text
Email : demo@example.com
Mot de passe : DemoPass123!
```

## Tests

```bash
python manage.py test
```

Les tests couvrent notamment :

- inscription, email unique, connexion, mauvais mot de passe, déconnexion ;
- CRUD matières ;
- CRUD tâches ;
- statut terminé / remise en cours ;
- recherche et filtres ;
- échéances et tâches en retard ;
- sécurité d'accès entre utilisateurs ;
- emploi du temps ;
- statistiques calculées depuis les données réelles.

## Structure principale

```text
accounts/       Authentification et profil
subjects/       Matières académiques
tasks/          Tâches, calendrier, échéances, semaine
schedule/       Emploi du temps
analytics/      Statistiques
dashboard/      Tableau de bord
notifications/  Rappels internes
templates/      Templates Django
static/         CSS et JavaScript
```
