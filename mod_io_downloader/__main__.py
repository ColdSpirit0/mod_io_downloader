import platform
from termcolor import colored
import requests
import tempfile
import zipfile
from tqdm import tqdm
from pathlib import Path
import shutil

from .config_parser import ConfigParser
from .game_config_parser import GameConfigParser
from .models import InstalledModCollection, InstalledModModel, ModInfoModel, ModsInfoModel


def get_mod_info(mod_id, api_key):
    url = f"https://api.mod.io/v1/games/169/mods/{mod_id}?api_key={api_key}"
    print("url:", url)
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


def get_mods_info(mod_ids: list[int], api_key: str):

    ids = ",".join(map(str, mod_ids))
    url = f"https://api.mod.io/v1/games/169/mods?id-in={ids}&api_key={api_key}"
    response = requests.get(url)

    return ModsInfoModel.model_validate_json(response.text)


def get_game_config_path(config: ConfigParser):
    config_path = config.root / "Mordhau" / "Saved" / "Config/" / f"{platform.system()}Server"
    if config_path.is_dir():
        game_ini_path = config_path / "Game.ini"
        if game_ini_path.is_file():
            return game_ini_path

    raise FileNotFoundError("Game.ini not found in path: " + str(config_path))


def main():
    config = ConfigParser()
    config.read(Path("config.ini"))

    game_config_path = get_game_config_path(config)
    game_config = GameConfigParser()
    game_config.read(game_config_path)

    modio_local_path = config.root / "Mordhau" / "Content" / ".modio"
    mods_local_path = modio_local_path / "mods"

    installed_mods_info: list[ModInfoModel] = []

    if len(game_config.mod_ids) == 0:
        print(colored("Game.ini does not contain any 'Mods' keys, nothing to download", "yellow"))
        return

    # iterate over local directories and get all needed and installed mods info
    for mod_info in game_config.mod_ids:
        modio_json_path = mods_local_path / str(mod_info) / "modio.json"
        if modio_json_path.is_file():
            modio_text = modio_json_path.read_text()
            mod_info = ModInfoModel.model_validate_json(modio_text)
            installed_mods_info.append(mod_info)


    # get all needed mods info from server
    needed_mods_info = get_mods_info(game_config.mod_ids, config.api_key)

    # if mod is not installed or hash changed, add it to download list
    mods_to_download: list[ModInfoModel] = []
    for needed_mod in needed_mods_info.data:
        # try to search for installed mod with same id
        installed_mod = None
        for mod_info in installed_mods_info:
            if mod_info.mod_id == needed_mod.mod_id:
                installed_mod = mod_info

        # if mod not found, add to download list
        if installed_mod is None:
            mods_to_download.append(needed_mod)
            continue

        # if hash changed, add to download list
        if needed_mod.modfile.filehash.md5 != installed_mod.modfile.filehash.md5:
            mods_to_download.append(needed_mod)
            continue

    if len(mods_to_download) == 0:
        print(colored("All mods are up to date", "green"))
        return
    else:
        print("Mods to download:")
        print(*[f"{mod.mod_id}: {mod.name}" for mod in mods_to_download], sep="\n")

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
            tmp_modio_json = tmp_mod_dir / 'modio.json'
            tmp_modio_json.write_text(mod_info.model_dump_json(indent=4), encoding="utf-8")


        # remove mods dirs from .modio dir
        # move new mods dirs from tmp to .modio dir
        for mod_info in mods_to_download:
            mod_local_path = mods_local_path / str(mod_info.mod_id)
            tmp_mod_dir = tmp_dir / str(mod_info.mod_id)

            if mod_local_path.exists():
                shutil.rmtree(mod_local_path)
            shutil.move(tmp_mod_dir, mod_local_path)


    # wirite installed_mods.json
    installed_mods = []
    for mod_info in installed_mods_info:
        date_updated = mod_info.date_updated
        modfile_id = mod_info.modfile.id
        modio_dir = config.root / '.modio' / 'mods' / str(mod_info.mod_id)
        # register mod as installed
        installed_mod = InstalledModModel(
            date_updated=date_updated,
            mod_id=mod_info.mod_id,
            modfile_id=modfile_id,
            path=modio_dir.as_posix()
        )
        installed_mods.append(installed_mod)

    installed_mods_path = modio_local_path / "installed_mods.json"
    installed_mods_path.write_text(
        InstalledModCollection(root=installed_mods)
        .model_dump_json(indent=4),
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()
