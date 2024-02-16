from termcolor import colored
import requests
import json
import tempfile
import zipfile
from tqdm import tqdm
from pathlib import Path
import shutil

from .models import ConfigModel, InstalledModModel, ModInfoModel, InstalledModCollection



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


def main():
    config = ConfigModel.model_validate_json(Path("config.json").read_text())

    installed_mods = []

    mods_total = len(config.mod_ids)

    # TODO
    # https://api.mod.io/v1/games/169/mods?id-in={comma_separated_mod_ids}&api_key={api_key}

    for idx, mod_id in enumerate(config.mod_ids):
        print(colored(f"► ({idx + 1}/{mods_total}) Downloading mod with ID {mod_id}...", "green"))
        mod_info, mod_info_text = get_mod_info(mod_id, config.api_key)

        # Extracting relevant information
        print(f"Name: {mod_info.name}")

        mod_dir = Path.cwd() / '.modio' / 'mods' / str(mod_id)
        mod_dir.mkdir(parents=True, exist_ok=True)

        mod_json_path = mod_dir / 'modio.json'
        date_updated = mod_info.date_updated
        modfile_id = mod_info.modfile.id
        download_url = mod_info.modfile.download.binary_url
        modio_dir = config.root / '.modio' / 'mods' / str(mod_id)

        # register mod as installed
        installed_mod = InstalledModModel(
            date_updated=date_updated,
            mod_id=mod_id,
            modfile_id=modfile_id,
            path=modio_dir.as_posix()
        )
        installed_mods.append(installed_mod)

        # check if {mod_id}/modio.json exists
        if mod_json_path.is_file():
            print("Found modio.json, checking file hash...")
            modio_json = ModInfoModel.model_validate_json(
                mod_json_path.read_text())

            # skip downloading if file hash matches
            if modio_json.modfile.filehash.md5 == mod_info.modfile.filehash.md5:
                print("Skipping download")
                continue
            else:
                # delete mod
                shutil.rmtree(mod_dir)

        # download and unpack
        with tempfile.TemporaryDirectory() as tmp_dir:
            mod_file_path = Path(tmp_dir) / f'modfile_{modfile_id}.zip'
            download_mod_file(download_url, mod_file_path)
            unpack_zip_file(mod_file_path, mod_dir)

            mod_info_json = json.loads(mod_info_text)
            mod_json_path.write_text(
                json.dumps(mod_info_json, indent=4))

    installed_mods_collection = InstalledModCollection(root=installed_mods)
    installed_mods_path = Path.cwd() / '.modio' / 'installed_mods.json'

    installed_mods_path.write_text(
        installed_mods_collection.model_dump_json(indent=4))


if __name__ == "__main__":
    main()
