import asyncio

from sqlalchemy.exc import IntegrityError

from .database import Base, engine, session
from .models import Like, Media, Tweet, User, user_to_user


async def create_db_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed():
    async with session() as db:
        try:
            # --- USERS ---
            u1 = User(username="testov", api_key="test")
            u2 = User(username="maria", api_key="test2")
            u3 = User(username="oleg", api_key="test3")

            db.add_all([u1, u2, u3])
            await db.commit()

            await db.refresh(u1)
            await db.refresh(u2)
            await db.refresh(u3)

            # --- FOLLOWING (user_to_user table) ---
            await db.execute(
                user_to_user.insert(),
                [
                    {"follower_id": u1.id, "following_id": u2.id},
                    {"follower_id": u1.id, "following_id": u3.id},
                    {"follower_id": u2.id, "following_id": u3.id},
                ],
            )
            await db.commit()

            # --- MEDIA ---
            m1 = Media(media_path="/uploads/cat.jpg")
            m2 = Media(media_path="/uploads/diagram.png")

            db.add_all([m1, m2])
            await db.commit()

            await db.refresh(m1)
            await db.refresh(m2)

            # --- TWEETS ---
            t1 = Tweet(
                user_id=u2.id,
                tweet_data="Всем доброго утра! Вот фото нашего офиса.",
                media=[m1],
            )
            t2 = Tweet(
                user_id=u3.id,
                tweet_data="Релиз сегодня в 18:00. Готовы?",
                media=[m2],
            )
            t3 = Tweet(
                user_id=u2.id,
                tweet_data="Короткая заметка: обновил документацию.",
            )

            db.add_all([t1, t2, t3])
            await db.commit()

            await db.refresh(t1)
            await db.refresh(t2)
            await db.refresh(t3)

            # --- LIKES ---
            like1 = Like(user_id=u1.id, tweet_id=t1.id)
            like2 = Like(user_id=u1.id, tweet_id=t2.id)

            db.add_all([like1, like2])
            await db.commit()

            print("Seed Success.")

        except IntegrityError as e:
            await db.rollback()
            print("Integrity error:", e)


# async def main():
#     await create_db_models()
#     await seed()


# if __name__ == "__main__":
#     asyncio.run(main())
