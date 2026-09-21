from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from .database import get_collection, get_client, MONGO_COLLECTION
from .models import ProductCreate, ProductUpdate, QuantityUpdate


def serialize_product(doc: dict) -> dict:
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

@app.post("/products", status_code=status.HTTP_201_CREATED, tags=["Products"])
async def create_product(product: ProductCreate):
    """Ajouter un produit."""
    collection = get_collection()
    doc = product.model_dump()
    result = await collection.insert_one(doc)
    created = await collection.find_one({"_id": result.inserted_id})
    return serialize_product(created)


@app.get("/products", tags=["Products"])
async def list_products(skip: int = 0, limit: int = 100):
    """Lister tous les produits."""
    collection = get_collection()
    cursor = collection.find().skip(skip).limit(limit)
    products = [serialize_product(doc) async for doc in cursor]
    return products


@app.get("/products/{product_id}", tags=["Products"])
async def get_product(product_id: str):
    """Accéder au descriptif du produit et la quantité restante."""
    collection = get_collection()
    try:
        oid = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalide")
    doc = await collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return serialize_product(doc)


@app.put("/products/{product_id}", tags=["Products"])
async def update_product(product_id: str, payload: ProductUpdate):
    """Modifier un produit (descriptif, quantité, etc.)."""
    collection = get_collection()
    try:
        oid = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalide")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

    result = await collection.update_one({"_id": oid}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Produit non trouvé")

    doc = await collection.find_one({"_id": oid})
    return serialize_product(doc)


@app.patch("/products/{product_id}/quantity", tags=["Products"])
async def update_quantity(product_id: str, payload: QuantityUpdate):
    """Ajouter ou réduire la quantité d'un produit (delta positif/négatif)."""
    collection = get_collection()
    try:
        oid = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalide")

    doc = await collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Produit non trouvé")

    new_quantity = doc["quantity"] + payload.delta
    if new_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuffisant. Quantité actuelle: {doc['quantity']}, delta demandé: {payload.delta}",
        )

    await collection.update_one({"_id": oid}, {"$set": {"quantity": new_quantity}})
    updated = await collection.find_one({"_id": oid})
    return serialize_product(updated)


@app.delete("/products/{product_id}", tags=["Products"])
async def delete_product(product_id: str):
    """Supprimer un produit."""
    collection = get_collection()
    try:
        oid = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalide")

    result = await collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return {"message": "Produit supprimé", "id": product_id}
