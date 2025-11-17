import pathlib
from typing import Annotated, Any, Dict

import uvicorn
from fastapi import Depends, FastAPI, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import async_get_db
from db.models import User
from db.utils import get_user_by_id
from schemas.user_sch import UserOutSchema
from utils.auth import authenticate_user

app = FastAPI()

# Путь к статике
ROOT_DIR = pathlib.Path(__file__).parent
STATIC_DIR = ROOT_DIR / "server" / "static"


# ------------ 1. ОТДАЧА СТАТИКИ ------------

# Все файлы из server/static доступны по /static/*
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ------------ 2. API (пример из задания) ------------


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
