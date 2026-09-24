from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (CheckConstraint("nbCommande >= 0", name="positive_order_count"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    prenom: Mapped[str] = mapped_column(String(100))
    mail: Mapped[str] = mapped_column(String(254))
    nbCommande: Mapped[int] = mapped_column(Integer, default=0)


class ClientFields(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class ClientCreate(ClientFields):
    nom: str = Field(min_length=1, max_length=100, description="Nom du client")
    prenom: str = Field(min_length=1, max_length=100, description="Prénom du client")
    mail: EmailStr = Field(max_length=254, description="Adresse e-mail du client")
    nbCommande: int = Field(default=0, strict=True, ge=0, le=2147483647,
                            description="Nombre de commandes mis à jour par les employés")


class ClientUpdate(ClientFields):
    nom: str | None = Field(default=None, min_length=1, max_length=100)
    prenom: str | None = Field(default=None, min_length=1, max_length=100)
    mail: EmailStr | None = Field(default=None, max_length=254)
    nbCommande: int | None = Field(default=None, strict=True, ge=0, le=2147483647)

    @model_validator(mode="after")
    def reject_explicit_null(self):
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Les champs fournis ne peuvent pas être null")
        return self


class ClientRead(ClientCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
