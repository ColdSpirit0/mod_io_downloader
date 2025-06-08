import zipfile
import requests
from tqdm import tqdm
from .app_config import AppConfig
from .models import ModInfoModel, ModsInfoModel


from termcolor import colored


import shutil
import tempfile
from pathlib import Path


def get_mod_info(mod_id, api_key):
    url = f"https://api.mod.io/v1/games/169/mods/{mod_id}?api_key={api_key}"
    response = requests.get(url)
    mod_info = ModInfoModel.model_validate_json(response.text)
    return mod_info, response.text


def download_mod_file(url, destination):
    with requests.get(url, stream=True) as r:
        with open(destination, 'wb') as f:
            pbar = tqdm(
                total=int(r.headers['Content-Length']), unit='B', unit_scale=True)
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))
            pbar.close()


def unpack_zip_file(zip_file, destination):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(destination)


def download_mods(mods_local_path: Path, mods_to_download: list[ModInfoModel], config: AppConfig):
    with tempfile.TemporaryDirectory() as t:
        # download and unpack in temp dir
        for idx, mod_info in enumerate(mods_to_download):
            print(colored(
                f"► ({idx + 1}/{len(mods_to_download)}) Downloading mod {mod_info.mod_id}: {mod_info.name}",
                "green"))

            tmp_dir = Path(t)
            tmp_mod_dir = tmp_dir / str(mod_info.mod_id)
            mod_zip_path = tmp_dir / f'modfile_{mod_info.mod_id}.zip'

            tmp_mod_dir.mkdir()
            download_mod_file(mod_info.modfile.download.binary_url, mod_zip_path)
            unpack_zip_file(mod_zip_path, tmp_mod_dir)
            mod_zip_path.unlink()

            # write modio.json
            # dont care about file content, it needed for the plugin
            tmp_modio_json = tmp_mod_dir / 'modio.json'
            _, mod_info_text = get_mod_info(mod_info.mod_id, config.api_key)
            tmp_modio_json.write_text(mod_info_text, encoding="utf-8")

            # remove mods dir from .modio dir
            # move downloaded mod dir from tmp to .modio dir
            mod_local_path = mods_local_path / str(mod_info.mod_id)
            tmp_mod_dir = tmp_dir / str(mod_info.mod_id)

            if mod_local_path.exists():
                shutil.rmtree(mod_local_path)
            shutil.move(tmp_mod_dir, mod_local_path)


def get_mods_info(mod_ids: list[int], api_key: str):

    ids = ",".join(map(str, mod_ids))
    url = f"https://api.mod.io/v1/games/169/mods?id-in={ids}&api_key={api_key}"
    response = requests.get(url)

    return ModsInfoModel.model_validate_json(response.text), response.text
