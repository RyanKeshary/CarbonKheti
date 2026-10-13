"""
NASA FIRMS Active Fire Intersector & Residue Burning Verification.
Detects post-harvest stubble burning by cross-referencing:
1. NASA FIRMS VIIRS / MODIS 375m active fire detections (lat, lon, brightness, acquisition date, confidence)
2. Enrolled plot geometry
3. Pre- and post-harvest date window
"""

from typing import List, Dict, Any, Optional
from shapely.geometry import shape, Point, Polygon
import math

class FireBurnDetector:
    def __init__(self, buffer_meters: float = 150.0):
        # Buffer around plot boundary to account for VIIRS pixel centroid footprint (375m)
        self.buffer_meters = buffer_meters

    def detect_fire_events(
        self,
        plot_geojson: Dict[str, Any],
        firms_fire_points: List[Dict[str, Any]],
        season_harvest_window_start: str,
        season_harvest_window_end: str
    ) -> Dict[str, Any]:
        """
        Intersects FIRMS active fire hotspots with plot boundary.
        
        firms_fire_points item format:
        {
            "latitude": 30.854,
            "longitude": 75.832,
            "acq_date": "2026-10-25",
            "confidence": "high",  # or "nominal" / numeric 0-100
            "bright_ti4": 345.2,   # Kelvin
            "satellite": "VIIRS-SNPP"
        }
        """
        if not firms_fire_points:
            return {
                "burn_detected": False,
                "fire_events_count": 0,
                "events": [],
                "status": "CLEAR_NO_BURNING_DETECTED"
            }

        poly = shape(plot_geojson)
        if not poly.is_valid:
            poly = poly.buffer(0)

        # Buffer polygon slightly in degrees (~0.0015 deg ~= 150m at equator)
        deg_buffer = self.buffer_meters / 111320.0
        buffered_poly = poly.buffer(deg_buffer)

        detected_events = []
        for fire in firms_fire_points:
            f_lat = fire.get("latitude")
            f_lon = fire.get("longitude")
            acq_date = fire.get("acq_date", "")

            if f_lat is None or f_lon is None:
                continue

            pt = Point(f_lon, f_lat)
            if buffered_poly.contains(pt):
                # Check date window if provided
                in_harvest_window = True
                if season_harvest_window_start and acq_date < season_harvest_window_start:
                    in_harvest_window = False
                if season_harvest_window_end and acq_date > season_harvest_window_end:
                    in_harvest_window = False

                detected_events.append({
                    "satellite": fire.get("satellite", "VIIRS"),
                    "acq_date": acq_date,
                    "confidence": fire.get("confidence"),
                    "brightness_kelvin": fire.get("bright_ti4"),
                    "fire_coordinates": [f_lat, f_lon],
                    "in_harvest_window": in_harvest_window
                })

        burn_detected = len(detected_events) > 0

        return {
            "burn_detected": burn_detected,
            "fire_events_count": len(detected_events),
            "events": detected_events,
            "status": "FLAGGED_POTENTIAL_STUBBLE_BURN" if burn_detected else "CLEAR",
            "auditor_action_required": burn_detected,
            "citation": "NASA Fire Information for Resource Management System (FIRMS) VIIRS 375m Near Real-Time Active Fire Product"
        }
