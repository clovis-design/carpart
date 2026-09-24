from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Client, ClientCreate, ClientRead, ClientUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        yield
    finally:
        engine.dispose()


app = FastAPI(
    title="CarPart - API Gestion des Clients",
    description="Gestion des fiches clients et du nombre de commandes saisi par les employés.",
    version="1.0.0",
    lifespan=lifespan,
)

Database = Annotated[Session, Depends(get_db)]
ClientId = Annotated[int, Path(gt=0)]


def find_client(db: Session, client_id: int) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return client


@app.get("/", tags=["Health"])
def root():
    return {"message": "CarPart API - Gestion des clients", "status": "ok"}


@app.get("/health", tags=["Health"])
def health(db: Database):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503, content={"status": "error", "database": "disconnected"}
        )


@app.post("/clients", response_model=ClientRead,
          status_code=status.HTTP_201_CREATED, tags=["Clients"])
def create_client(payload: ClientCreate, db: Database):
    """Ajouter un client, avec zéro commande par défaut."""
    client = Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@app.get("/clients", response_model=list[ClientRead], tags=["Clients"])
def list_clients(db: Database, skip: int = Query(0, ge=0),
                 limit: int = Query(100, ge=1, le=1000)):
    return db.scalars(select(Client).order_by(Client.id).offset(skip).limit(limit)).all()


@app.get("/clients/{client_id}", response_model=ClientRead, tags=["Clients"])
def get_client(client_id: ClientId, db: Database):
    """Consulter une fiche client."""
    return find_client(db, client_id)


@app.put("/clients/{client_id}", response_model=ClientRead, tags=["Clients"])
def update_client(client_id: ClientId, payload: ClientUpdate, db: Database):
    """Modifier les champs fournis, dont le nombre de commandes saisi par un employé."""
    client = find_client(db, client_id)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")
    for field, value in updates.items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@app.delete("/clients/{client_id}", tags=["Clients"])
def delete_client(client_id: ClientId, db: Database):
    """Supprimer une fiche client."""
    client = find_client(db, client_id)
    db.delete(client)
    db.commit()
    return {"message": "Client supprimé", "id": client_id}
