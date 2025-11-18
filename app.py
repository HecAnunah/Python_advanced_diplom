import pathlib
from typing import Annotated, Any, Dict

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import async_get_db
from db.models import User
from db.utils import check_follow_user_ability, get_user_by_id
from schemas.base_sch import DefaultSchema
from schemas.user_sch import UserOutSchema
from utils.auth import authenticate_user

app = FastAPI()

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
    user["name"] = current_user.name
    all_followers = list()
    # followers = current_user.followers
    # for follower in followers:
    #     follower_user = dict()
    #     follower_user["id"] = follower.id
    #     follower_user["name"] = follower.name
    #     all_followers.append(follower_user)
    user["followers"] = all_followers
    all_followings = list()
    followings = current_user.following
    for following in followings:
        following_user = dict()
        following_user["id"] = following.id
        following_user["name"] = following.name
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
    user["name"] = user_.name
    all_followers = list()
    # followers = user_.followers
    # for follower in followers:
    #     follower_user = dict()
    #     follower_user["id"] = follower.id
    #     follower_user["name"] = follower.username
    #     all_followers.append(follower_user)
    user["followers"] = all_followers
    all_followings = list()
    followings = user_.following
    for following in followings:
        following_user = dict()
        following_user["id"] = following.id
        following_user["name"] = following.name
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


# ------------ 3. SPA CATCH-ALL ------------
# ДОЛЖЕН идти ПОСЛЕ app.mount("/static")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # catch-all отдаёт SPA index.html только если путь **не начинается с /static или /api**
    if full_path.startswith(("server", "static")):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
