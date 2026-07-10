from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import BaseModel


# Link model
class LinkModel(BaseModel):
    __tablename__ = "links"

    # the short code itself is the primary key — that's the "short URL"
    code: Mapped[str] = mapped_column(primary_key=True)
    original_url: Mapped[str]
    # server_default lets Postgres stamp the timestamp, so it's correct
    # even for rows inserted outside of this app
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # optional TTL: once this passes, redirect should treat the link as gone
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # all clicks recorded for this link; deleting a link cascades to its clicks
    clicks: Mapped[list["StatsModel"]] = relationship(
        back_populates="link", cascade="all, delete-orphan"
    )


# Stats model
class StatsModel(BaseModel):
    __tablename__ = "clicks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    link_code: Mapped[str] = mapped_column(ForeignKey("links.code"))
    # stored so /stats can tell total clicks (COUNT(*)) apart from
    # unique clicks (COUNT(DISTINCT ip_address))
    ip_address: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    link: Mapped["LinkModel"] = relationship(back_populates="clicks")
