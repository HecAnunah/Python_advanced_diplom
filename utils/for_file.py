from pathlib import Path

from aiofiles import open
from fastapi import UploadFile

from utils.setting import MEDIA_PATH


async def check_or_get_filename(path: Path) -> Path:
    """
    Adds a numerical suffix to the filename if a file with the same name
    already exists.
    :param path: The path to check and modify.
    :return: The modified path with a numerical suffix.
    """
    original_path = path
    counter = 0

    while path.exists():
        counter += 1
        filename = f"{original_path.stem} ({counter}){original_path.suffix}"
        path = original_path.with_name(filename)
    return path


async def save_uploaded_file(uploaded_file: UploadFile) -> str:
    """
    Загружает файл и возвращает относительный путь

    :param uploaded_file: Объект FastAPI UploadFile,
    представляющий загруженный файл. :return: Относительный путь к сохраненному файлу.

    :raises: Любые исключения, которые могут возникнуть во время загрузки и хранения файлов.
    """

    MEDIA_PATH.mkdir(parents=True, exist_ok=True)

    file_path: Path = MEDIA_PATH
    if uploaded_file.filename is not None:
        file_path = MEDIA_PATH / uploaded_file.filename
    filename = await check_or_get_filename(path=file_path)
    img_path = f"{filename.stem}{filename.suffix}"
    content = uploaded_file.file.read()
    async with open(filename, "wb") as file:
        await file.write(content)
    return img_path
