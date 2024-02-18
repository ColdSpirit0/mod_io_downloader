from unreal_ini_parser import IniParser
from unreal_ini_parser.exceptions import KeyNotFoundException


class GameConfigParser(IniParser):
    @property
    def mod_ids(self):
        try:
            return self.get_values("/Script/Mordhau.MordhauGameSession", "Mods")
        except KeyNotFoundException:
            return []
