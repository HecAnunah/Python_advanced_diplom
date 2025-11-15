import asyncio

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from .database import Base, engine, session
from .models import Follow, Like, Media, Tweet, User


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def seed():
    async with session() as db:
        try:
            # --- ПОЛЬЗОВАТЕЛИ ---
            u1 = User(name="Testov Test", api_key="test")
            u2 = User(name="Maria Sm", api_key="test_2")
            u3 = User(name="Oleg Kric", api_key="test_3")

            db.add_all([u1, u2, u3])
            await db.commit()
            await db.refresh(u1)
            await db.refresh(u2)
            await db.refresh(u3)

            # --- ПОДПИСКИ ---
            await db.execute(
                Follow.__table__.insert(),
                [
                    {"follower_id": u1.id, "following_id": u2.id},
                    {"follower_id": u1.id, "following_id": u3.id},
                    {"follower_id": u2.id, "following_id": u3.id},
                ],
            )
            await db.commit()

            # --- МЕДИА ---
            m1 = Media(
                filename="cat.jpg",
                storage_path="/uploads/cat.jpg",
                mime_type="image/jpeg",
            )
            m2 = Media(
                filename="diagram.png",
                storage_path="/uploads/diagram.png",
                mime_type="image/png",
            )
            db.add_all([m1, m2])
            await db.commit()
            await db.refresh(m1)
            await db.refresh(m2)

            # --- ТВИТЫ ---
            t1 = Tweet(
                author_id=u2.id,
                content="Всем доброго утра! Вот фото нашего офиса.",
                medias=[m1],
            )
            t2 = Tweet(
                author_id=u3.id,
                content="Релиз сегодня в 18:00. Готовы? #deploy",
                medias=[m2],
            )
            t3 = Tweet(author_id=u2.id, content="Короткий замет: обновил документацию.")

            db.add_all([t1, t2, t3])
            await db.commit()
            await db.refresh(t1)
            await db.refresh(t2)

            # --- ЛАЙКИ ---
            like1 = Like(user_id=u1.id, tweet_id=t1.id)
            like2 = Like(user_id=u1.id, tweet_id=t2.id)
            db.add_all([like1, like2])
            await db.commit()

            # --- ОБНОВЛЕНИЕ like_count ---
            res1 = await db.execute(select(func.count()).where(Like.tweet_id == t1.id))
            t1.like_count = res1.scalar()

            res2 = await db.execute(select(func.count()).where(Like.tweet_id == t2.id))
            t2.like_count = res2.scalar()

            await db.commit()

            print("Seed done.")
        except IntegrityError as e:
            await db.rollback()
            print("Integrity error:", e)


async def main():
    await create_all()
    await seed()


if __name__ == "__main__":
    asyncio.run(main())
