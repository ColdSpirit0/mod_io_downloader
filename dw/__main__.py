import requests
import json
import tempfile
import zipfile
from tqdm import tqdm
from pathlib import Path


def get_mod_info(mod_id, api_key):
    url = f"https://api.mod.io/v1/games/169/mods/{mod_id}?api_key={api_key}"
    print(url)
    response = requests.get(url)
    data = response.json()
    return data


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
    with open('config.json') as config_file:
        config_data = json.load(config_file)
        mod_ids = config_data['mod_ids']
        root = Path(config_data['root'])
        api_key = config_data['api_key']
        copy_path = config_data['copy_path']

    print(config_data, mod_ids, api_key)

    installed_mods = []

    for mod_id in mod_ids:
        print(f"> Downloading mod with ID {mod_id}...")
        mod_info = get_mod_info(mod_id, api_key)

        mod_dir = Path.cwd() / '.modio' / 'mods' / str(mod_id)
        mod_dir.mkdir(parents=True, exist_ok=True)

        mod_json_path = mod_dir / 'modio.json'
        with open(mod_json_path, 'w') as modio_json:
            json.dump(mod_info, modio_json)

        date_updated = mod_info.get('date_updated')
        modfile_id = mod_info.get('modfile', {}).get('id')
        download_url = mod_info.get('modfile', {}).get(
            'download', {}).get('binary_url')

        modio_dir = root / '.modio' / 'mods' / str(mod_id)
        with tempfile.TemporaryDirectory() as tmp_dir:
            mod_file_path = Path(tmp_dir) / f'modfile_{modfile_id}.zip'
            download_mod_file(download_url, mod_file_path)

            installed_mods.append({
                "date_updated": date_updated,
                "mod_id": mod_id,
                "modfile_id": modfile_id,
                "path": modio_dir.as_posix()
            })

            unpack_zip_file(mod_file_path, mod_dir)

    with open(Path.cwd() / '.modio' / 'installed_mods.json', 'w') as installed_mods_file:
        json.dump(installed_mods, installed_mods_file, indent=4)

if __name__ == "__main__":
    main()
