import tkinter as tk
from sim_rf_map.weather_model import WeatherConditions
from .tooltip import Tooltip


class WeatherGUI:
    """Small panel for entering weather conditions."""

    def __init__(self, parent: tk.Frame) -> None:
        self.weather = WeatherConditions()
        self.frame = tk.LabelFrame(parent, text="Weather Conditions")
        self.frame.pack(padx=5, pady=5, fill="x")

        self.temp_var = tk.DoubleVar(value=20.0)
        self.humidity_var = tk.DoubleVar(value=50.0)
        self.precip_var = tk.StringVar(value="None")
        self.cloud_var = tk.StringVar(value="None")

        self._build_ui()

    def _build_ui(self) -> None:
        tk.Label(self.frame, text="Temp (°C)").grid(row=0, column=0, sticky="w")
        temp_entry = tk.Entry(self.frame, textvariable=self.temp_var, width=6)
        temp_entry.grid(row=0, column=1)
        Tooltip(
            temp_entry,
            "Air temperature in Celsius. This affects atmospheric attenuation "
            "and the speed of radio propagation in the model."
        )

        tk.Label(self.frame, text="Humidity (%)").grid(row=1, column=0, sticky="w")
        hum_entry = tk.Entry(self.frame, textvariable=self.humidity_var, width=6)
        hum_entry.grid(row=1, column=1)
        Tooltip(
            hum_entry,
            "Relative humidity as a percentage. High humidity can introduce "
            "additional signal absorption effects."
        )

        tk.Label(self.frame, text="Precipitation").grid(row=2, column=0, sticky="w")
        precip_menu = tk.OptionMenu(self.frame, self.precip_var, "None", "Light", "Medium", "Heavy")
        precip_menu.grid(row=2, column=1)
        Tooltip(
            precip_menu,
            "Level of precipitation such as none, light or heavy rain. Higher "
            "levels generally increase signal loss."
        )

        tk.Label(self.frame, text="Cloud Cover").grid(row=3, column=0, sticky="w")
        cloud_menu = tk.OptionMenu(self.frame, self.cloud_var, "None", "Light", "Medium", "Heavy")
        cloud_menu.grid(row=3, column=1)
        Tooltip(
            cloud_menu,
            "Amount of cloud cover present. Dense cloud layers can influence "
            "certain propagation scenarios."
        )

    def get_weather(self) -> WeatherConditions:
        """Return the current weather settings as a WeatherConditions object."""
        return WeatherConditions(
            temperature_c=self.temp_var.get(),
            humidity_percent=self.humidity_var.get(),
            precipitation_level=self.precip_var.get(),
            cloud_cover_level=self.cloud_var.get(),
        )
