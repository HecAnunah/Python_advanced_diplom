from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from .database import Base

# Ассоциационная таблица tweets <-> medias (many-to-many)
tweet_medias = Table(
    "tweet_medias",
    Base.metadata,
    Column(
        "tweet_id",
        Integer,
        ForeignKey("tweets.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "media_id",
        Integer,
        ForeignKey("medias.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# кто на кого подписан
class Follow(Base):
    __tablename__ = "follows"
    follower_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    following_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    api_key = Column(
        String(128), unique=True, nullable=False, index=True
    )  # по этому полю будем искать пользователя
    avatar = Column(String(300), nullable=True)  # ссылка/путь к аватару (опционально)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tweets = relationship(
        "Tweet", back_populates="author", cascade="all, delete-orphan"
    )
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")

    # following: пользователи, на которых я подписан
    following = relationship(
        "User",
        secondary="follows",
        primaryjoin=id == Follow.follower_id,
        secondaryjoin=id == Follow.following_id,
        backref="followers",
    )

    def __repr__(self):
        return f"<User id={self.id} name={self.name!r}>"


class Media(Base):
    __tablename__ = "medias"

    id = Column(Integer, primary_key=True)
    filename = Column(String(300), nullable=False)  # оригинальное имя
    storage_path = Column(
        String(500), nullable=False
    )  # где лежит файл (относительный путь или URL)
    mime_type = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tweets = relationship("Tweet", secondary=tweet_medias, back_populates="medias")

    def __repr__(self):
        return f"<Media id={self.id} file={self.filename!r}>"


# Твит
class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True)
    author_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    # дополнительное поле для ускорения сортировки по "популярности" (можно поддерживать триггером / обновлять при like)
    like_count = Column(
        Integer, nullable=False, default=0, server_default="0", index=True
    )

    author = relationship("User", back_populates="tweets")
    medias = relationship("Media", secondary=tweet_medias, back_populates="tweets")
    likes = relationship("Like", back_populates="tweet", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<Tweet id={self.id} author_id={self.author_id} likes={self.like_count}>"
        )


class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tweet_id = Column(
        Integer, ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="likes")
    tweet = relationship("Tweet", back_populates="likes")

    __table_args__ = (
        UniqueConstraint(
            "user_id", "tweet_id", name="uq_user_tweet_like"
        ),  # нельзя лайкать дважды
    )

    def __repr__(self):
        return f"<Like id={self.id} user={self.user_id} tweet={self.tweet_id}>"


# Дополнительно: индексы для ускорения выборок ленты
Index("ix_tweets_author_created", Tweet.author_id, Tweet.created_at.desc())
