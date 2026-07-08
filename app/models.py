from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import BaseModel


# Link model
class LinkModel(BaseModel):
    __tablename__ = "links"

    code: Mapped[str] = mapped_column(primary_key=True)
    original_url: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    clicks: Mapped[list["StatsModel"]] = relationship(
        back_populates="link", cascade="all, delete-orphan"
    )


# Stats model
class StatsModel(BaseModel):
    __tablename__ = "clicks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    link_code: Mapped[str] = mapped_column(ForeignKey("links.code"))
    ip_address: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    link: Mapped["LinkModel"] = relationship(back_populates="clicks")
