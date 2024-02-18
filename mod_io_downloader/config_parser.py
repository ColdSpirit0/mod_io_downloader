from unreal_ini_parser import IniParser
from pathlib import Path


class ConfigParser(IniParser):
    @property
    def root(self):
        return self.get_value("default", "root", Path)

    @property
    def api_key(self):
        return self.get_value("default", "api_key")