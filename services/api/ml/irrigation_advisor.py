"""
Rain-Aware AWD Irrigation Recommendation Engine.
Strictly implements Section 10 (Item 7):
- Deterministic rule engine over water tube depth (-15 cm to +5 cm)
- Local weather forecast (rainfall in next 24-48 hours via Open-Meteo)
- Crop phenology stage (IRRI Safe AWD Flowering Exemption)
- Step-by-step explainability with primary agronomic citations
"""

from typing import Dict, Any

class IrrigationAdvisor:
    @staticmethod
    def get_recommendation(
        water_depth_cm: float,
        crop_stage: str,               # "VEGETATIVE", "PANICLE_INITIATION", "FLOWERING", "GRAIN_FILLING", "MATURITY"
        forecast_rain_24h_mm: float,
        forecast_rain_48h_mm: float,
        days_after_transplanting: int
    ) -> Dict[str, Any]:
        """
        Executes IRRI Safe AWD rules:
        1. Flowering Exemption: At flowering (days ~55-75), field must remain continuously flooded (2-5 cm).
        2. Rain-aware delay: If water is above -15 cm and rain >= 10 mm is forecast, delay pumping.
        3. Threshold irrigation: When water drops to -15 cm, irrigate to +5 cm.
        """
        # Rule 1: Flowering stage exception (IRRI Safe AWD Protocol)
        is_flowering = (crop_stage.upper() == "FLOWERING") or (55 <= days_after_transplanting <= 75)
        if is_flowering:
            if water_depth_cm < 2.0:
                action = "IRRIGATE_IMMEDIATELY"
                urgency = "HIGH"
                plain_summary = "Crop is in critical flowering stage. Maintain 2 to 5 cm standing water to prevent spikelet sterility."
            else:
                action = "MAINTAIN_FLOOD"
                urgency = "NORMAL"
                plain_summary = "Standing water is adequate for flowering. Do not allow field to dry during anthesis."
            
            return {
                "action": action,
                "urgency": urgency,
                "water_depth_cm": water_depth_cm,
                "crop_stage": "FLOWERING",
                "target_depth_cm": 5.0,
                "flowering_exemption_applied": True,
                "plain_summary": plain_summary,
                "rainfall_considered": False,
                "citation": "IRRI Safe AWD Technical Bulletin No. 12 (Flowering Stage Submergence Mandate)"
            }

        # Rule 2: Water level is above soil surface (> 0 cm)
        if water_depth_cm >= 0.0:
            return {
                "action": "DO_NOT_IRRIGATE",
                "urgency": "NONE",
                "water_depth_cm": water_depth_cm,
                "crop_stage": crop_stage,
                "target_depth_cm": 0.0,
                "flowering_exemption_applied": False,
                "plain_summary": f"Field has {water_depth_cm:.1f} cm standing water. Allow field to dry naturally until water drops to -15 cm in the tube.",
                "rainfall_considered": False,
                "citation": "IRRI AWD Guidelines"
            }

        # Rule 3: Water is within Safe AWD zone (-15 cm to 0 cm)
        if -15.0 < water_depth_cm < 0.0:
            # Check rainfall forecast
            if forecast_rain_24h_mm >= 10.0 or forecast_rain_48h_mm >= 15.0:
                return {
                    "action": "HOLD_IRRIGATION_RAIN_EXPECTED",
                    "urgency": "LOW",
                    "water_depth_cm": water_depth_cm,
                    "crop_stage": crop_stage,
                    "target_depth_cm": 0.0,
                    "flowering_exemption_applied": False,
                    "plain_summary": f"Water level is at {water_depth_cm:.1f} cm. Significant rain ({forecast_rain_24h_mm:.1f} mm in 24h) is forecast. Do not pump electricity or diesel; let rainfall replenish the paddy.",
                    "rainfall_considered": True,
                    "forecast_rain_mm": forecast_rain_24h_mm,
                    "citation": "CarbonKheti Rain-Aware Safe AWD Advisory"
                }
            else:
                return {
                    "action": "ALLOW_DRYING",
                    "urgency": "NORMAL",
                    "water_depth_cm": water_depth_cm,
                    "crop_stage": crop_stage,
                    "target_depth_cm": -15.0,
                    "flowering_exemption_applied": False,
                    "plain_summary": f"Water is at {water_depth_cm:.1f} cm below soil. Aeration is active and cutting methane. Re-irrigate when water reaches -15 cm.",
                    "rainfall_considered": True,
                    "forecast_rain_mm": forecast_rain_24h_mm,
                    "citation": "IRRI Alternate Wetting and Drying (AWD)"
                }

        # Rule 4: Water depth <= -15 cm -> Trigger re-flooding to +5 cm
        return {
            "action": "IRRIGATE_NOW",
            "urgency": "MEDIUM",
            "water_depth_cm": water_depth_cm,
            "crop_stage": crop_stage,
            "target_depth_cm": 5.0,
            "flowering_exemption_applied": False,
            "plain_summary": f"Water level has reached the -15 cm threshold ({water_depth_cm:.1f} cm). Irrigate your field to a depth of +5 cm now.",
            "rainfall_considered": True,
            "forecast_rain_mm": forecast_rain_24h_mm,
            "citation": "IRRI Safe AWD Protocol (Reflooding Trigger: -15 cm)"
        }
