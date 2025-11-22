import pathlib
from contextlib import asynccontextmanager
from typing import Annotated, Any, Dict, Union

import uvicorn
from aiofiles import os as aiofiles_os
from fastapi import Depends, FastAPI, HTTPException, UploadFile, status
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import async_get_db, engine
from db.init_db import create_all_if_not_exists, seed
from db.models import Like, Media, Tweet, User
from db.utils import (
    associate_media_with_tweet,
    check_follow_user_ability,
    get_all_following_tweets,
    get_all_tweets,
    get_like_by_id,
    get_media_by_tweet_id,
    get_tweet_by_id,
    get_user_by_id,
)
from schemas.base_sch import DefaultSchema
from schemas.media_sch import MediaUpload
from schemas.tweet_sch import TweetCreate, TweetIn, TweetOut
from schemas.user_sch import UserOutSchema
from utils.authorize import authenticate_user
from utils.exceptions import (
    custom_http_exception_handler,
    response_validation_exception_handler,
    validation_exception_handler,
)
from utils.for_file import save_uploaded_file
from utils.setting import MEDIA_PATH


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all_if_not_exists()
    await seed()
    yield
    if engine is not None:
        await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, custom_http_exception_handler)
app.add_exception_handler(
    ResponseValidationError, response_validation_exception_handler
)

# Путь к статике
ROOT_DIR = pathlib.Path(__file__).parent
STATIC_DIR = ROOT_DIR / "server" / "static"


# ------------ 1. ОТДАЧА СТАТИКИ ------------

# Все файлы из server/static доступны по /static/*
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ------------ 2. API user------------


@app.get("/api/users/me", status_code=status.HTTP_200_OK)
async def get_info_about_me(
    current_user: Annotated[
        UserOutSchema, "User model obtained from the api key"
    ] = Depends(authenticate_user),
):
    user = dict()
    user["id"] = current_user.id
    user["name"] = current_user.username
    all_followers = list()
    followers = current_user.followers
    for follower in followers:
        follower_user = dict()
        follower_user["id"] = follower.id
        follower_user["name"] = follower.username
        all_followers.append(follower_user)
    user["followers"] = all_followers
    all_followings = list()
    followings = current_user.following
    for following in followings:
        following_user = dict()
        following_user["id"] = following.id
        following_user["name"] = following.username
        all_followings.append(following_user)
    user["followings"] = all_followings
    answer: Dict[str, Any] = dict()
    answer["user"] = user
    answer["result"] = True
    return JSONResponse(content=answer, status_code=200)


@app.get("/api/users/{user_id}", status_code=status.HTTP_200_OK)
async def get_users_info_by_id(
    user_id: int,
    session: AsyncSession = Depends(async_get_db),
    current_user: Annotated[User, "User model obtained from the api key"] = Depends(
        authenticate_user
    ),
):
    user_ = await get_user_by_id(user_id=user_id, session=session)
    user = dict()
    user["id"] = user_.id
    user["name"] = user_.username
    all_followers = list()
    followers = user_.followers
    for follower in followers:
        follower_user = dict()
        follower_user["id"] = follower.id
        follower_user["name"] = follower.username
        all_followers.append(follower_user)
    user["followers"] = all_followers
    all_followings = list()
    followings = user_.following
    for following in followings:
        following_user = dict()
        following_user["id"] = following.id
        following_user["name"] = following.username
        all_followings.append(following_user)
    user["followings"] = all_followings
    answer: Dict[str, Any] = dict()
    answer["result"] = True
    answer["user"] = user
    return JSONResponse(content=answer, status_code=200)


@app.post(
    "/users/{user_id}/follow",
    status_code=status.HTTP_201_CREATED,
    response_model=DefaultSchema,
)
async def follow_user(
    user_id: int,
    current_user: Annotated[User, "User model obtained from the api key"] = Depends(
        authenticate_user
    ),
    session: AsyncSession = Depends(async_get_db),
):

    user_to_follow = await get_user_by_id(user_id, session)
    following_ability = await check_follow_user_ability(current_user, user_to_follow)
    if following_ability:
        user_to_follow.followers.append(current_user)
        await session.commit()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already follow that user!",
        )
    return {"result": True}


@app.delete(
    "/users/{user_id}/follow",
    status_code=status.HTTP_200_OK,
    response_model=DefaultSchema,
)
async def unsubscribe_from_user(
    user_id: int,
    current_user: Annotated[User, "User model obtained from the api key"] = Depends(
        authenticate_user
    ),
    session: AsyncSession = Depends(async_get_db),
):
    follower_deleted = await get_user_by_id(user_id, session)

    if follower_deleted not in current_user.following:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not following this user.",
        )

    current_user.following.remove(follower_deleted)
    await session.commit()
    return {"result": True}


# ------------ 2. Tweet------------


@app.post(
    "/api/tweets",
    status_code=status.HTTP_201_CREATED,
    response_model=Union[TweetIn, TweetCreate],
)
async def create_tweet(
    tweet_in: TweetIn,
    current_user: Annotated[User, "User model obtained from the api key"] = Depends(
        authenticate_user
    ),
    session: AsyncSession = Depends(async_get_db),
):
    new_tweet = Tweet(
        user_id=current_user.id,
        tweet_data=tweet_in.tweet_data,
    )
    session.add(new_tweet)
    await session.flush()
    tweet_media_ids = tweet_in.tweet_media_ids

    if tweet_media_ids:
        await associate_media_with_tweet(
            session=session, media_ids=tweet_media_ids, tweet=new_tweet
        )

    await session.commit()

    return {"result": True, "tweet_id": new_tweet.id}


@app.delete(
    "/api/tweets/{tweet_id}",
    status_code=status.HTTP_200_OK,
    response_model=DefaultSchema,
)
async def delete_tweet(
    tweet_id: int,
    current_user: Annotated[User, "User model obtained from the api key"] = Depends(
        authenticate_user
    ),
    session: AsyncSession = Depends(async_get_db),
):
    tweet_to_delete = await get_tweet_by_id(tweet_id, session)
    if tweet_to_delete.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sorry, you can't delete tweets created by another user.",
        )
    media_to_delete = await get_media_by_tweet_id(tweet_id, session)
    for media in media_to_delete:
        path_to_delete = MEDIA_PATH / media.media_path
        await aiofiles_os.remove(path_to_delete)

    await session.delete(tweet_to_delete)
    await session.commit()
    return tweet_to_delete


@app.post(
    "/api/tweets/{tweet_id}/likes",
    status_code=status.HTTP_201_CREATED,
    response_model=DefaultSchema,
)
async def like_a_tweet(
    tweet_id: int,
    current_user: Annotated[User, "User model obtained from the api key"] = Depends(
        authenticate_user
    ),
    session: AsyncSession = Depends(async_get_db),
):
    tweet_to_like = await get_tweet_by_id(tweet_id=tweet_id, session=session)
    like = await get_like_by_id(
        session=session, tweet_id=tweet_id, user_id=current_user.id
    )
    if not like:
        if tweet_to_like.user_id != current_user.id:
            like_to_add = Like(user_id=current_user.id, tweet_id=tweet_to_like.id)
            session.add(like_to_add)
            await session.commit()

    return dict()


@app.delete(
    "/api/tweets/{tweet_id}/likes",
    status_code=status.HTTP_200_OK,
    response_model=DefaultSchema,
)
async def delete_like_from_tweet(
    tweet_id: int,
    current_user: Annotated[User, "User model obtained from the api key"] = Depends(
        authenticate_user
    ),
    session: AsyncSession = Depends(async_get_db),
):
    await session.commit()
    test_tweet = await get_tweet_by_id(tweet_id=tweet_id, session=session)
    like = await get_like_by_id(
        session, tweet_id=test_tweet.id, user_id=current_user.id
    )
    if like:
        await session.delete(like)
        await session.commit()
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You already do not like that tweet.",
        )

    return dict()


@app.get("/api/tweets", status_code=status.HTTP_200_OK)
async def get_tweets(
    current_user: Annotated[User, "User model obtained from the api key"] = Depends(
        authenticate_user
    ),
    session: AsyncSession = Depends(async_get_db),
):
    all_tweets = await get_all_tweets(session=session)
    all_following_tweets = []
    if all_tweets is None:
        all_tweets = "No tweets found"
    else:
        for tweet in all_tweets:
            single_tweet = dict()
            single_tweet["id"] = tweet.id
            single_tweet["content"] = tweet.tweet_data
            single_tweet_media = []
            for media in tweet.media:
                single_tweet_media.append(media.media_path)
            single_tweet["attachments"] = single_tweet_media
            single_tweet_author = dict()

            single_tweet_author["id"] = tweet.user_id
            tweet_author = await get_user_by_id(tweet.user_id, session)
            single_tweet_author["name"] = tweet_author.username
            single_tweet["author"] = single_tweet_author

            single_tweet_likes = []
            for like in tweet.likes:
                single_like = dict()
                single_like["user_id"] = like.user_id
                tweet_author = await get_user_by_id(like.user_id, session)
                single_like["name"] = tweet_author.username
                single_tweet_likes.append(single_like)
            single_tweet["likes"] = single_tweet_likes

            all_following_tweets.append(single_tweet)
        all_tweets = all_following_tweets
    answer = dict()
    answer["result"] = True
    answer["tweets"] = all_tweets
    return JSONResponse(content=answer, status_code=200)


@app.get(
    "/api/tweets/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=TweetOut,
)
async def get_following_tweets(
    user_id: int,
    current_user: Annotated[User, "User model obtained from the api key"] = Depends(
        authenticate_user
    ),
    session: AsyncSession = Depends(async_get_db),
):
    all_tweets = await get_all_following_tweets(session=session, current_user=user_id)

    return {"tweets": all_tweets}


# ------------ 3. Media ------------


@app.post(
    "/api/medias", status_code=status.HTTP_201_CREATED, response_model=MediaUpload
)
async def upload_media(
    file: UploadFile,
    user: Annotated[User, "User model obtained from the api key"] = Depends(
        authenticate_user
    ),
    session: AsyncSession = Depends(async_get_db),
):
    try:
        file = await save_uploaded_file(file)
        new_media = Media(media_path=file)
        session.add(new_media)
        await session.commit()

        return new_media
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ------------ 4. SPA CATCH-ALL ------------
# ДОЛЖЕН идти ПОСЛЕ app.mount("/static")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # catch-all отдаёт SPA index.html только если путь **не начинается с /static или /api**
    if full_path.startswith(("server", "static")):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
