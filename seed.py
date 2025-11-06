from sqlalchemy.exc import IntegrityError

from database import Follow, Like, Media, SessionLocal, Tweet, User, create_all


def seed():
    create_all()
    session = SessionLocal()
    try:
        # Создаём пользователей (api_key — любая строка, frontend подставит её в header)
        u1 = User(name="Иван Петров", api_key="key_ivan_1")
        u2 = User(name="Мария Смирнова", api_key="key_masha_2")
        u3 = User(name="Олег Ковалёв", api_key="key_oleg_3")

        session.add_all([u1, u2, u3])
        session.commit()

        # Подписки: Иван подписан на Марию и Олега; Мария подписана на Олега
        session.execute(
            Follow.__table__.insert(),
            [
                {"follower_id": u1.id, "following_id": u2.id},
                {"follower_id": u1.id, "following_id": u3.id},
                {"follower_id": u2.id, "following_id": u3.id},
            ],
        )
        session.commit()

        # Медиа
        m1 = Media(
            filename="cat.jpg", storage_path="/uploads/cat.jpg", mime_type="image/jpeg"
        )
        m2 = Media(
            filename="diagram.png",
            storage_path="/uploads/diagram.png",
            mime_type="image/png",
        )
        session.add_all([m1, m2])
        session.commit()

        # Твиты
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
        session.add_all([t1, t2, t3])
        session.commit()

        # Лайки: Иван лайкает твит Олега и первый твит Марии
        like1 = Like(user_id=u1.id, tweet_id=t1.id)
        like2 = Like(user_id=u1.id, tweet_id=t2.id)
        session.add_all([like1, like2])

        # Обновляем like_count (можно делать программно при добавлении/удалении лайка)
        t1.like_count = session.query(Like).filter(Like.tweet_id == t1.id).count()
        t2.like_count = session.query(Like).filter(Like.tweet_id == t2.id).count()

        session.commit()

        print("Seed done. Users:", session.query(User).count())
        print(
            "Tweets:",
            session.query(Tweet).count(),
            "Medias:",
            session.query(Media).count(),
        )

    except IntegrityError as e:
        session.rollback()
        print("Integrity error:", e)
    finally:
        session.close()


if __name__ == "__main__":
    seed()
