class Strategy:
    NAME = "Base"
    THEME = "WX"

    def decide(self, row: dict) -> bool:
        raise NotImplementedError
