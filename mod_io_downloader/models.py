from typing import List
from pathlib import Path

from pydantic import BaseModel, HttpUrl, RootModel


class ConfigModel(BaseModel):
    mod_ids: List[int]
    root: Path
    api_key: str
    copy_path: Path | None


class FileHashModel(BaseModel):
    md5: str


class DownloadModel(BaseModel):
    binary_url: HttpUrl


class ModFileModel(BaseModel):
    id: int
    filehash: FileHashModel
    download: DownloadModel


class ModInfoModel(BaseModel):
    name: str
    modfile: ModFileModel
    date_updated: int


class InstalledModModel(BaseModel):
    date_updated: int
    mod_id: int
    modfile_id: int
    path: str


class InstalledModCollection(RootModel):
    root: List[InstalledModModel]
