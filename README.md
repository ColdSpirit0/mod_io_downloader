# Mod.io downloader (for Mordhau server)

Downloads mods faster than mod.io plugin.

## System requirements

1. Python 3.12+
1. Installed and configured Mordhau Dedicated Server

## Installation

1. Install package:
    ```bash
    pip install mod_io_downloader
    ```
1. Find api key - it can be found in `.../Mordhau Dedicated Server/Mordhau/Content/.modio/log.txt`
1. Run `python -m mod_io_downloader <api_key>` in the server directory - all mods from Game.ini should be downloaded or updated
1. You can create batch script in the server directory. This will download mods and start server.

    Example of `start.bat`:
    ```bat
    python -m mod_io_downloader <api_key>

    @REM exit if something goes wrong
    if %errorlevel% neq 0 (
        pause
        exit /b %errorlevel%
    )

    timeout 5
    start MordhauServer.exe FFA_ThePit -log -Port=7777 -QueryPort=27015 -BeaconPort=15000
    ```

