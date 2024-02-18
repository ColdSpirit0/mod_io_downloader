from typing import List

from pydantic import BaseModel, Field, HttpUrl, RootModel


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
    mod_id: int = Field(alias="id")
    modfile: ModFileModel
    date_updated: int
    visible: int

    class Config:
        extra = "allow"
        populate_by_name = True


class InstalledModModel(BaseModel):
    date_updated: int
    mod_id: int
    modfile_id: int
    path: str


class InstalledModCollection(RootModel):
    root: List[InstalledModModel]


class ModsInfoModel(BaseModel):
    data: List[ModInfoModel]
