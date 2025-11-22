import pytest
from httpx import AsyncClient

from db.models import User

from .conftest import unauthorized_structure_response

pytestmark = pytest.mark.asyncio


class TestUserAPI:
    @classmethod
    def setup_class(cls):
        cls.base_url = "/users/{}/follow"
        cls.expected_response = {"result": True}
        cls.error_response = {
            "result": False,
            "error_type": "Bad Request",
            "error_message": "",
        }

    async def test_get_info_about_me_unauthorized(self, invalid_client: AsyncClient):
        response = await invalid_client.get("/users/me")
        assert response.status_code in (401, 403)
        data = response.json()
        assert data == {
            "result": False,
            "error_type": "Unauthorized",
            "error_message": "API key authentication failed",
        }

    async def test_get_users_info_by_id_success(self, client: AsyncClient, db_session):
        user = await db_session.get(User, 2)
        response = await client.get(f"/users/{user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        assert data["user"]["id"] == user.id
        assert data["user"]["name"] == user.username

    async def test_get_user_information(self, client: AsyncClient):
        if hasattr(self, "base_url"):
            url = self.base_url.replace("/follow", "")
            response = await client.get(url.format(1))
            data = response.json()
            assert response.status_code == 200
            assert data["result"] is True

    @pytest.mark.asyncio
    async def test_get_me_information(self, client: AsyncClient):
        if hasattr(self, "base_url"):
            url = self.base_url.replace("{}/follow", "me")
            response = await client.get(url)
            data = response.json()
            assert response.status_code == 200
            assert data["result"] is True

    @pytest.mark.asyncio
    @pytest.mark.parametrize("unauthorized", ["/users/me", "/users/2"])
    async def test_get_wrong_auth(self, invalid_client: AsyncClient, unauthorized: str):
        response = await invalid_client.get(unauthorized)
        assert response.status_code == 401
        assert response.json() == unauthorized_structure_response
