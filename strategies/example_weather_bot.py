from strategies.base import Strategy


class WeatherCheapYes(Strategy):
    NAME, THEME = "WeatherCheapYes", "WX"

    def decide(self, row):
        return row["close_px"] < 0.30
