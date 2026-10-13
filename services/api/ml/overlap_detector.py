"""
Plot Geometry Overlap & Double-Counting Safeguard
Uses Shapely for 2D polygon intersection and PostGIS compatibility.
Enforces the one-plot-one-project rule and detects duplicate claims.
"""

from typing import List, Dict, Any, Optional, Tuple
from shapely.geometry import shape, Polygon
from shapely.ops import transform
import pyproj

# Tolerance threshold: overlapping area greater than 5% or 0.05 ha triggers conflict
OVERLAP_AREA_THRESHOLD_HA = 0.02
OVERLAP_FRACTION_THRESHOLD = 0.05

def calculate_polygon_area_ha(geojson_geometry: Dict[str, Any]) -> float:
    """
    Computes accurate geodesic surface area in hectares of a GeoJSON polygon.
    Projects from EPSG:4326 to equal-area projection (EPSG:6933 or UTM).
    """
    geom = shape(geojson_geometry)
    if not isinstance(geom, Polygon):
        raise ValueError("Geometry must be a Polygon")

    # Use pyproj to project to Cylindrical Equal Area (EPSG:6933)
    project_to_equal_area = pyproj.Transformer.from_crs(
        "EPSG:4326", "EPSG:6933", always_xy=True
    ).transform

    from shapely import transform as shp_transform
    projected_geom = shp_transform(geom, project_to_equal_area, interleaved=False)
    area_m2 = projected_geom.area
    area_ha = area_m2 / 10000.0
    return round(area_ha, 4)

def check_plot_overlap_conflicts(
    candidate_geojson: Dict[str, Any],
    candidate_plot_id: str,
    enrolled_plots: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Checks if a candidate plot boundary intersects or duplicates any existing enrolled plot.
    
    enrolled_plots format:
    [
        {"plot_id": "P-101", "geojson": {...}, "farmer_id": "F-01", "season": "Kharif 2026"}
    ]
    """
    candidate_poly = shape(candidate_geojson)
    if not candidate_poly.is_valid:
        # Attempt repair with buffer(0)
        candidate_poly = candidate_poly.buffer(0)
        if not candidate_poly.is_valid:
            return {
                "has_conflict": True,
                "reason": "INVALID_GEOMETRY",
                "details": "Candidate polygon coordinates form self-intersecting or invalid boundary."
            }

    candidate_area_ha = calculate_polygon_area_ha(candidate_geojson)

    conflicts = []
    for existing in enrolled_plots:
        if existing["plot_id"] == candidate_plot_id:
            continue
        
        existing_poly = shape(existing["geojson"])
        if not existing_poly.is_valid:
            existing_poly = existing_poly.buffer(0)

        if candidate_poly.intersects(existing_poly):
            intersection = candidate_poly.intersection(existing_poly)
            # Project intersection to measure area
            project_to_equal_area = pyproj.Transformer.from_crs(
                "EPSG:4326", "EPSG:6933", always_xy=True
            ).transform
            from shapely import transform as shp_transform
            proj_intersection = shp_transform(intersection, project_to_equal_area, interleaved=False)
            overlap_area_ha = proj_intersection.area / 10000.0
            
            overlap_pct = (overlap_area_ha / max(candidate_area_ha, 0.0001)) * 100.0

            if overlap_area_ha >= OVERLAP_AREA_THRESHOLD_HA or overlap_pct >= (OVERLAP_FRACTION_THRESHOLD * 100):
                conflicts.append({
                    "conflicting_plot_id": existing["plot_id"],
                    "conflicting_farmer_id": existing.get("farmer_id"),
                    "season": existing.get("season"),
                    "overlap_area_ha": round(overlap_area_ha, 4),
                    "overlap_pct_of_candidate": round(overlap_pct, 2)
                })

    has_conflict = len(conflicts) > 0
    return {
        "candidate_plot_id": candidate_plot_id,
        "candidate_area_ha": candidate_area_ha,
        "has_conflict": has_conflict,
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "status": "REJECTED_OVERLAP" if has_conflict else "CLEARED"
    }
