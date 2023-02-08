from typing import List
from typing import Optional
from sqlalchemy.orm import Mapped
from sqlalchemy import Integer, String, ForeignKey, Table, Column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


# declarative base class
class Base(DeclarativeBase):
    pass

groupPhoto = Table(
    "groupPhoto",
    Base.metadata,
    Column("photo_id", ForeignKey("photo.id")),
    Column("group_id", ForeignKey("group.id")),
)

groupUser = Table(
    "groupUser",
    Base.metadata,
    Column("user_id", ForeignKey("user.id")),
    Column("group_id", ForeignKey("group.id")),
)


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    full_name: Mapped[Optional[str]]
    telegram_id: Mapped[str]
    photos: Mapped[List["Photo"]] = relationship()

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, full_name={self.full_name!r}),\
                telegram_id={self.telegram_id!r}"

class Photo(Base):
    __tablename__ = "photo"

    id: Mapped[int] = mapped_column(primary_key=True)
    hash: Mapped[str]
    likes: Mapped[int]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"));


    def __repr__(self) -> str:
        return f"Photo(id={self.id!r}, hashsum={self.hash!r})"

class Group(Base):
    __tablename__ = "group"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    telegram_id: Mapped[str]
    contest_theme: Mapped[str]

    def __repr__(self) -> str:
        return f"Group(id={self.id!r}, name={self.name!r}, telegram_id={self.telegram_id!r}, contest_theme={self.contest_theme})"
