# CarPart — API de gestion des clients

API développée avec **Python 3.10+**, **FastAPI** et **MySQL 8.4** via SQLAlchemy
et PyMySQL. L'image Docker utilise Python 3.11.

Une fiche contient un identifiant entier généré par MySQL, un nom, un prénom,
une adresse e-mail valide et un nombre entier de commandes positif ou nul.
Les commandes sont passées par mail : les employés mettent manuellement à jour
`nbCommande` ; l'API ne traite pas les mails.

## Lancement avec Docker Compose

Depuis le dossier parent `carpart` :

```bash
docker compose up --build -d api_client
```

Cette commande démarre MySQL, attend qu'il soit prêt, puis démarre l'API.
La table `clients` est créée automatiquement au démarrage. Les données sont
conservées dans le volume `mysql_client`.

- API : http://localhost:7000
- Swagger (pour tester les routes) : http://localhost:7000/docs
- État de la connexion MySQL : http://localhost:7000/health

## Lancement local

Depuis `carpart`, démarrer la base :

```bash
docker compose up -d mysql_client
```

Puis, depuis `carpart-client-api` :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 7000
```

La configuration peut être fournie par variables d'environnement ou dans un
fichier `.env` local (chargé par python-dotenv) :

| Variable | Valeur par défaut |
|----------|-------------------|
| `MYSQL_HOST` | `localhost` |
| `MYSQL_PORT` | `3307` |
| `MYSQL_DATABASE` | `carpart_clients` |
| `MYSQL_USER` | `carpart` |
| `MYSQL_PASSWORD` | `carpart_dev` |

Ces identifiants correspondent à l'environnement de développement du Compose.
MySQL est exposé sur le port local 3307 ; les conteneurs utilisent le port 3306.
Pour une base MySQL existante, créer au préalable la base et un utilisateur
ayant les droits de création de table, lecture, insertion, modification et suppression.

## Routes

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/clients` | Ajouter un client (201) |
| GET | `/clients?skip=0&limit=100` | Lister les clients avec pagination |
| GET | `/clients/{id}` | Consulter une fiche client |
| PUT | `/clients/{id}` | Modifier les champs fournis d'une fiche |
| DELETE | `/clients/{id}` | Supprimer un client |
| GET | `/health` | État de MySQL (200 ou 503) |

`nom`, `prenom` et `mail` sont obligatoires à la création. `nbCommande` vaut 0
par défaut. Les noms ne peuvent pas être vides ; les nombres de commandes
fractionnaires, négatifs ou supérieurs à 2147483647 sont refusés.
Une modification conserve les champs omis et refuse les valeurs `null`.
Une fiche inexistante retourne 404, un corps invalide 422 et une modification
vide 400. Les identifiants sont des entiers strictement positifs.

## Exemple de cycle complet

```bash
curl -X POST http://localhost:7000/clients \
  -H 'Content-Type: application/json' \
  -d '{"nom":"Dupont","prenom":"Alice","mail":"alice@example.com","nbCommande":2}'

# Remplacer 1 par l'identifiant renvoyé lors de la création.
curl http://localhost:7000/clients/1

curl -X PUT http://localhost:7000/clients/1 \
  -H 'Content-Type: application/json' \
  -d '{"nbCommande":3}'

curl -X DELETE http://localhost:7000/clients/1
```

## Tests d'intégration

Avec l'API et MySQL démarrés, depuis `carpart-client-api` :

```bash
python3 -m unittest discover -s tests -v
```

Ces tests HTTP vérifient le cycle création/consultation/modification/suppression,
les validations et la connexion MySQL. Ils suppriment les fiches qu'ils créent.
La variable `API_URL` permet de cibler une autre adresse.
