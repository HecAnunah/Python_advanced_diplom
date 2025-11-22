from datetime import datetime
from typing import List

from sqlalchemy import Column, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

# User
user_to_user = Table(
    "user_to_user",
    Base.metadata,
    Column("follower_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("following_id", Integer, ForeignKey("users.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    api_key: Mapped[str] = mapped_column(String(255))
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    tweets: Mapped[List["Tweet"]] = relationship(
        backref="user", cascade="all, delete-orphan"
    )
    likes: Mapped[List["Like"]] = relationship(
        backref="user", cascade="all, delete-orphan"
    )

    following: Mapped[List["None"]] = relationship(
        "User",
        secondary=user_to_user,
        primaryjoin=lambda: User.id == user_to_user.c.follower_id,
        secondaryjoin=lambda: User.id == user_to_user.c.following_id,
        backref="followers",
        lazy="selectin",
    )

    def __repr__(self):
        return self._repr(
            id=self.id,
            api_key=self.api_key,
            username=self.username,
        )


# Твит *
class Tweet(Base):
    __tablename__ = "tweets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    create_date: Mapped[datetime] = mapped_column(server_default=func.now())
    tweet_data: Mapped[str] = mapped_column(String(2500))
    media: Mapped[List["Media"]] = relationship(backref="tweets", cascade="all, delete")
    likes: Mapped[List["Like"]] = relationship(backref="tweets", cascade="all, delete")

    def __repr__(self):
        return self._repr(
            id=self.id,
            user_id=self.user_id,
            create_date=self.create_date,
            tweet_data=self.tweet_data,
        )


# Like models *
class Like(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweets.id"), nullable=False)

    def __repr__(self):
        return self._repr(
            id=self.id,
            user_id=self.user_id,
            tweets_id=self.tweet_id,
        )


# media


class Media(Base):
    __tablename__ = "media"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)

    media_path: Mapped[str] = mapped_column(String(255))  # *
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweets.id"), nullable=True)

    def __repr__(self):
        return self._repr(
            id=self.id,
            media_path=self.media_path,
            tweet_id=self.tweet_id,
        )
