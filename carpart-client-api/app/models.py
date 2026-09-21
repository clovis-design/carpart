from typing import Optional
from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    nom: str = Field(..., min_length=1, description="Nom du client")
    prenom: str = Field(..., description="Prénom du client")
    addresse: Optional[str] = Field(None, description="Adresse du client")
    mail: Optional[str] = Field(None, description="Adresse e-mail du client")
    nbCommande: Optional[float] = Field(None, ge=0,description="Nombre de commande du client")


class ClientUpdate(BaseModel):
    nom: Optional[str] = Field(None, min_length=1)
    prenom: Optional[str] = Field(None, description="Descriptif du client")
    addresse: Optional[str] = Field(None, description="Adresse du client")
    mail: Optional[str] = Field(None, description="Adresse e-mail du client")
    nbCommande: Optional[float] = Field(None, ge=0, description="Nombre de commande du client")

