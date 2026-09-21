from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from .database import get_collection, get_client, MONGO_COLLECTION
from .models import ClientCreate, ClientUpdate


def serialize_client(doc: dict) -> dict:
    """Convertit un document Mongo en dict JSON sérialisable."""
    doc["id"] = str(doc.pop("_id"))
    return doc


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Vérifie la connexion au démarrage
    try:
        client = get_client()
        await client.admin.command("ping")
        print("Connecté à MongoDB")
    except Exception as e:
        print(f"Impossible de se connecter à MongoDB: {e}")
    yield
    if get_client() is not None:
        get_client().close()


app = FastAPI(
    title="CarPart - API Gestion des Stocks",
    description="API de gestion des stocks de pièces détachées pour CarPart",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Health"])
async def root():
    return {"message": "CarPart API - Gestion des stocks", "status": "ok"}


@app.get("/health", tags=["Health"])
async def health():
    try:
        await get_client().admin.command("ping")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503, content={"status": "error", "database": "disconnected", "detail": str(e)}
        )


# --- CRUD Produits ---

@app.post("/clients", status_code=status.HTTP_201_CREATED, tags=["Clients"])
async def create_client(client: ClientCreate):
    """Ajouter un client."""
    collection = get_collection()
    doc = client.model_dump()
    result = await collection.insert_one(doc)
    created = await collection.find_one({"_id": result.inserted_id})
    return serialize_client(created)


@app.get("/clients", tags=["Clients"])
async def list_clients(skip: int = 0, limit: int = 100):
    """Lister tous les clients."""
    collection = get_collection()
    cursor = collection.find().skip(skip).limit(limit)
    clients = [serialize_client(doc) async for doc in cursor]
    return clients


@app.get("/clients/{client_id}", tags=["Clients"])
async def get_client(client_id: str):
    """Accéder au descriptif du client et la quantité restante."""
    collection = get_collection()
    try:
        oid = ObjectId(client_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalide")
    doc = await collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return serialize_client(doc)


@app.put("/clients/{client_id}", tags=["Clients"])
async def update_client(client_id: str, payload: ClientUpdate):
    """Modifier un client (descriptif, quantité, etc.)."""
    collection = get_collection()
    try:
        oid = ObjectId(client_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalide")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

    result = await collection.update_one({"_id": oid}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    doc = await collection.find_one({"_id": oid})
    return serialize_client(doc)


@app.delete("/clients/{client_id}", tags=["Clients"])
async def delete_client(client_id: str):
    """Supprimer un client."""
    collection = get_collection()
    try:
        oid = ObjectId(client_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalide")

    result = await collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return {"message": "Client supprimé", "id": client_id}
