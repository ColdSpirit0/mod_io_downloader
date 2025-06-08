from unreal_ini_parser import IniParser, KeyNotFoundException


class GameConfigParser(IniParser):
    @property
    def mod_ids(self):
        try:
            return self.get_values("/Script/Mordhau.MordhauGameSession", "Mods", int)
        except KeyNotFoundException:
            return []
