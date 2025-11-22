import io

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_upload_media(client: AsyncClient, db_session: AsyncSession):

    # Создадим фиктивный файл в памяти
    file_content = b"Hello world"
    file = ("test.txt", io.BytesIO(file_content), "text/plain")

    # Отправляем POST-запрос к роуту /medias
    response = await client.post(
        "/medias",
        files={"file": file},
        headers={"api-key": "test"},  # используем API ключ существующего юзера
    )

    # Проверяем статус
    assert response.status_code == 201

    # Проверяем структуру ответа
    data = response.json()
    assert "media_id" in data
    assert "result" in data
    assert data["result"] is True
