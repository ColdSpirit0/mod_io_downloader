import platform
import click
from termcolor import colored
from pathlib import Path

from .app_config import AppConfig
from .mod_io import download_mods, get_mods_info
from .game_config_parser import GameConfigParser
from .models import ModInfoModel


def get_game_config_path(config: AppConfig):
    config_path = config.game_root / "Mordhau" / "Saved" / "Config/" / f"{platform.system()}Server"
    if config_path.is_dir():
        game_ini_path = config_path / "Game.ini"
        if game_ini_path.is_file():
            return game_ini_path

    raise FileNotFoundError("Game.ini not found in path: " + str(config_path))


@click.command()
@click.argument("api_key")
@click.argument("game_root", type=click.Path(exists=True, dir_okay=True, path_type=Path), default=Path.cwd())
def main(api_key: str, game_root: Path):
    print("Game root: " + str(game_root.resolve()))
    config = AppConfig(api_key, game_root)

    game_config_path = get_game_config_path(config)
    game_config = GameConfigParser()
    game_config.read(game_config_path)

    modio_local_path = config.game_root / "Mordhau" / "Content" / ".modio"
    mods_local_path = modio_local_path / "mods"

    installed_mods_info: list[ModInfoModel] = []

    if len(game_config.mod_ids) == 0:
        print(colored("Game.ini does not contain any 'Mods' keys, nothing to download", "yellow"))
        return

    # iterate over local directories and get all needed and installed mods info
    for mod_info in game_config.mod_ids:
        modio_json_path = mods_local_path / str(mod_info) / "modio.json"
        if modio_json_path.is_file():
            try:
                modio_text = modio_json_path.read_text(encoding="utf-8")
                mod_info = ModInfoModel.model_validate_json(modio_text)
                installed_mods_info.append(mod_info)
            except Exception:
                print(colored(f"Failed to parse {modio_json_path}", "red"))
                raise

    # get mods info from server
    remote_mods_info, remote_mods_info_text = get_mods_info(game_config.mod_ids, config.api_key)
    # Path("out.json").write_text(needed_mods_info_text, encoding="utf-8")

    # check all requested mods are visible, show error instead
    remote_mod_ids = [m.mod_id for m in remote_mods_info.data]
    hidden_mods = [m for m in game_config.mod_ids if m not in remote_mod_ids]

    if len(hidden_mods) > 0:
        print(colored("Mods are hidden:", "red"))
        for m in hidden_mods:
            print(f"{m}")
        print(colored("Remove them from config, they can break your server", "red"))
        exit(1)

    # if mod is not installed or hash changed, add it to download list
    mods_to_download: list[ModInfoModel] = []
    for remote_mod in remote_mods_info.data:
        # try to search for installed mod with same id
        installed_mod = None
        for mod_info in installed_mods_info:
            if mod_info.mod_id == remote_mod.mod_id:
                installed_mod = mod_info

        # if mod not found, add to download list
        if installed_mod is None:
            mods_to_download.append(remote_mod)
            continue

        # if hash changed, add to download list
        if remote_mod.modfile.filehash.md5 != installed_mod.modfile.filehash.md5:
            mods_to_download.append(remote_mod)
            continue

    mods_local_path.mkdir(parents=True, exist_ok=True)

    if len(mods_to_download) == 0:
        print(colored("All mods are up to date", "green"))
    else:
        print("Mods to download:")
        print(*[f"{mod.mod_id}: {mod.name}" for mod in mods_to_download], sep="\n")
        download_mods(mods_local_path, mods_to_download, config)


if __name__ == "__main__":
    main()
