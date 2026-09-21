from typing import Optional
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Nom de la pièce")
    description: Optional[str] = Field(None, description="Descriptif de la pièce")
    quantity: int = Field(..., ge=0, description="Quantité en stock")
    price: Optional[float] = Field(None, ge=0, description="Prix unitaire")
    reference: Optional[str] = Field(None, description="Référence pièce")


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, ge=0)
    reference: Optional[str] = None


class QuantityUpdate(BaseModel):
    delta: int = Field(..., description="Variation de quantité (positif = ajout, négatif = retrait)")
