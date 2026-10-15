from django.test import SimpleTestCase

from .views import calculate_weather_risk


class WeatherRiskTests(SimpleTestCase):
    def get_weather(self, wind=0, rain=0, snow=0):
        return {
            "wind_speed_mph": wind,
            "rain_inches_per_hour": rain,
            "snow_inches_per_hour": snow,
        }

    def test_low_wind_is_low_risk(self):
        result = calculate_weather_risk(self.get_weather(wind=20), 10000)
        self.assertEqual(result["risk_level"], "low")
        self.assertEqual(result["risk_score"], 0)
        self.assertFalse(result["no_travel"])

    def test_moderate_wind(self):
        result = calculate_weather_risk(self.get_weather(wind=30), 10000)
        self.assertEqual(result["risk_level"], "moderate")
        self.assertEqual(result["risk_score"], 1)

    def test_high_wind(self):
        result = calculate_weather_risk(self.get_weather(wind=40), 10000)
        self.assertEqual(result["risk_level"], "high")
        self.assertEqual(result["risk_score"], 2)

    def test_severe_wind(self):
        result = calculate_weather_risk(self.get_weather(wind=46), 10000)
        self.assertEqual(result["risk_level"], "severe")
        self.assertEqual(result["risk_score"], 3)

    def test_extreme_wind_means_no_travel(self):
        result = calculate_weather_risk(self.get_weather(wind=55), 10000)
        self.assertEqual(result["risk_level"], "no_travel")
        self.assertEqual(result["risk_score"], 4)
        self.assertTrue(result["no_travel"])

    def test_heavy_load_and_wind_means_no_travel(self):
        # 16,000 kg is approximately 35,274 lb.
        result = calculate_weather_risk(self.get_weather(wind=46), 16000)
        self.assertEqual(result["risk_level"], "no_travel")
        self.assertTrue(result["no_travel"])

    def test_heavy_load_causes_severe_wind_risk(self):
        # 19,000 kg is approximately 41,888 lb.
        result = calculate_weather_risk(self.get_weather(wind=40), 19000)
        self.assertEqual(result["risk_level"], "severe")
        self.assertFalse(result["no_travel"])

    def test_moderate_rain(self):
        result = calculate_weather_risk(self.get_weather(rain=0.15), 10000)
        self.assertEqual(result["risk_level"], "moderate")

    def test_high_rain(self):
        result = calculate_weather_risk(self.get_weather(rain=0.30), 10000)
        self.assertEqual(result["risk_level"], "high")

    def test_severe_rain(self):
        result = calculate_weather_risk(self.get_weather(rain=0.60), 10000)
        self.assertEqual(result["risk_level"], "severe")

    def test_extreme_rain_means_no_travel(self):
        result = calculate_weather_risk(self.get_weather(rain=1.10), 10000)
        self.assertEqual(result["risk_level"], "no_travel")
        self.assertTrue(result["no_travel"])

    def test_moderate_snow(self):
        result = calculate_weather_risk(self.get_weather(snow=0.6), 10000)
        self.assertEqual(result["risk_level"], "moderate")

    def test_high_snow(self):
        result = calculate_weather_risk(self.get_weather(snow=1.2), 10000)
        self.assertEqual(result["risk_level"], "high")

    def test_severe_snow(self):
        result = calculate_weather_risk(self.get_weather(snow=2.2), 10000)
        self.assertEqual(result["risk_level"], "severe")

    def test_extreme_snow_means_no_travel(self):
        result = calculate_weather_risk(self.get_weather(snow=3.1), 10000)
        self.assertEqual(result["risk_level"], "no_travel")
        self.assertTrue(result["no_travel"])

    
    def test_rain_at_exactly_one_inch_is_severe(self):
        result = calculate_weather_risk(self.get_weather(rain=1.00), 10000)
        self.assertEqual(result["risk_level"], "severe")
        self.assertFalse(result["no_travel"])

    def test_snow_at_exactly_three_inches_is_severe(self):
        result = calculate_weather_risk(self.get_weather(snow=3.00), 10000)
        self.assertEqual(result["risk_level"], "severe")
        self.assertFalse(result["no_travel"])

    def test_rain_above_one_inch_means_no_travel(self):
        result = calculate_weather_risk(self.get_weather(rain=1.01), 10000)
        self.assertEqual(result["risk_level"], "no_travel")
        self.assertTrue(result["no_travel"])

    def test_snow_above_three_inches_means_no_travel(self):
        result = calculate_weather_risk(self.get_weather(snow=3.01), 10000)
        self.assertEqual(result["risk_level"], "no_travel")
        self.assertTrue(result["no_travel"])

    def test_missing_weather_is_unknown(self):
        result = calculate_weather_risk(None, 10000)
        self.assertEqual(result["risk_level"], "unknown")
        self.assertIsNone(result["risk_score"])
        self.assertFalse(result["no_travel"])

    def test_low_combined_weather_scenario(self):
        weather = self.get_weather(
            wind=10,
            rain=0.05,
            snow=0.2,
        )
        result = calculate_weather_risk(weather, 10000)
        self.assertEqual(result["risk_level"], "low")

    def test_moderate_combined_weather_scenario(self):
        weather = self.get_weather(
            wind=28,
            rain=0.15,
            snow=0.7,
        )
        result = calculate_weather_risk(weather, 10000)
        self.assertEqual(result["risk_level"], "moderate")

    def test_high_combined_weather_scenario(self):
        weather = self.get_weather(
            wind=38,
            rain=0.30,
            snow=1.5,
        )
        result = calculate_weather_risk(weather, 10000)
        self.assertEqual(result["risk_level"], "high")

    def test_severe_combined_weather_scenario(self):
        weather = self.get_weather(
            wind=48,
            rain=0.60,
            snow=2.5,
        )
        result = calculate_weather_risk(weather, 10000)
        self.assertEqual(result["risk_level"], "severe")

    def test_no_travel_combined_weather_scenario(self):
        weather = self.get_weather(
            wind=56,
            rain=0.05,
            snow=0,
        )
        result = calculate_weather_risk(weather, 10000)
        self.assertEqual(result["risk_level"], "no_travel")
        self.assertTrue(result["no_travel"])
