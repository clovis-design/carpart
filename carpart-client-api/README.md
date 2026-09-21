# CarPart - API Gestion des Stocks

API FastAPI + MongoDB pour la gestion des stocks de pièces détachées.

## Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | /products | Ajouter un produit |
| GET | /products | Lister les produits |
| GET | /products/{id} | Descriptif + quantité restante |
| PUT | /products/{id} | Modifier descriptif / quantité |
| PATCH | /products/{id}/quantity | Ajouter/réduire quantité (delta) |
| DELETE | /products/{id} | Supprimer un produit |
| GET | /health | État de la BDD |
| GET | /docs | Documentation Swagger |

## Lancement manuel (sans compose, comme demandé)

### 1. Build des images

```bash
docker build -f Dockerfile.mongo -t carpart-mongo .
docker build -f Dockerfile.api -t carpart-api .
```

### 2. Créer un réseau

```bash
docker network create carpart-net
```

### 3. Lancer MongoDB

```bash
docker run -d --name carpart-mongo --network carpart-net -p 27017:27017 carpart-mongo
```

### 4. Lancer l'API

```bash
docker run -d --name carpart-api --network carpart-net -p 8000:8000 \
  -e MONGO_URL=mongodb://carpart-mongo:27017 \
  carpart-api
```

### 5. Tester

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/products -H "Content-Type: application/json" \
  -d '{"name":"Plaquettes de frein","description":"AV - Clio 4","quantity":50,"price":29.99,"reference":"PF-CLIO4-AV"}'
curl http://localhost:8000/products
curl http://localhost:8000/docs
```

## Lancement local (sans Docker)

```bash
pip install -r requirements.txt
# Lancer Mongo localement d'abord
MONGO_URL=mongodb://localhost:27017 uvicorn app.main:app --reload
```
