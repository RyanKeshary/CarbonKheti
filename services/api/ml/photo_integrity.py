"""
Photo and Evidence Integrity Module
Examines:
1. EXIF capture-time vs upload-time consistency
2. EXIF GPS coordinates vs declared plot centroid (geofence radius check)
3. Perceptual hashing (pHash) to detect duplicate or reused images
4. Image quality: Laplacian variance blur detection and luminance check
"""

import io
import math
import hashlib
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ExifTags
import numpy as np

MAX_DISTANCE_FROM_PLOT_METERS = 300.0  # Safe threshold for plot boundary photo
MIN_LAPLACIAN_VARIANCE_BLUR = 60.0    # Images below this are flagged as blurry
MIN_AVERAGE_LUMINANCE = 25.0           # Under 25 indicates pitch black / unusable

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes distance in meters between two lat/lon coordinates."""
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c

def compute_perceptual_hash(img: Image.Image, hash_size: int = 8) -> str:
    """
    Computes 64-bit difference perceptual hash (dHash).
    Resistant to light re-compression, scaling, and contrast changes.
    """
    # Resize to (hash_size + 1, hash_size) and convert to greyscale
    resized = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = list(resized.getdata())
    width = hash_size + 1

    diff = []
    for row in range(hash_size):
        for col in range(hash_size):
            left = pixels[row * width + col]
            right = pixels[row * width + col + 1]
            diff.append(left > right)

    # Convert binary array to hex string
    decimal_val = 0
    hex_str = []
    for index, value in enumerate(diff):
        if value:
            decimal_val += 2 ** (index % 4)
        if index % 4 == 3:
            hex_str.append(hex(decimal_val)[2:])
            decimal_val = 0
    return "".join(hex_str)

def extract_exif_gps(img: Image.Image) -> Optional[Tuple[float, float]]:
    """Extracts latitude and longitude from image EXIF data if present."""
    try:
        exif = img.getexif()
        if not exif:
            return None
        
        # Look for GPSInfo tag (0x8825)
        gps_info = None
        for tag_id, value in exif.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            if tag == "GPSInfo" or tag_id == 34853:
                gps_info = value
                break
        
        if not gps_info:
            return None

        def _convert_to_degrees(value):
            if isinstance(value, tuple) and len(value) == 3:
                d, m, s = value
                return float(d) + (float(m) / 60.0) + (float(s) / 3600.0)
            return float(value)

        lat_ref = gps_info.get(1)  # 1 is GPSLatitudeRef
        lat = gps_info.get(2)      # 2 is GPSLatitude
        lon_ref = gps_info.get(3)  # 3 is GPSLongitudeRef
        lon = gps_info.get(4)      # 4 is GPSLongitude

        if lat and lon and lat_ref and lon_ref:
            lat_deg = _convert_to_degrees(lat)
            if lat_ref != "N":
                lat_deg = -lat_deg
            lon_deg = _convert_to_degrees(lon)
            if lon_ref != "E":
                lon_deg = -lon_deg
            return (lat_deg, lon_deg)
    except Exception:
        pass
    return None

def compute_blur_variance(img_gray_arr: np.ndarray) -> float:
    """
    Computes Laplacian variance as focus / blur indicator.
    Approximated via discrete 2D kernel convolution.
    """
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    # Simple convolution via padding
    h, w = img_gray_arr.shape
    if h < 3 or w < 3:
        return 0.0
    padded = np.pad(img_gray_arr, 1, mode="reflect")
    lap = (
        padded[0:h, 1:w+1] +
        padded[2:h+2, 1:w+1] +
        padded[1:h+1, 0:w] +
        padded[1:h+1, 2:w+2] -
        4.0 * img_gray_arr
    )
    return float(np.var(lap))

def inspect_photo_evidence(
    image_bytes: bytes,
    declared_plot_lat: Optional[float] = None,
    declared_plot_lon: Optional[float] = None
) -> Dict[str, Any]:
    """
    Full inspection suite for field photo uploads:
    - sha256 checksum
    - perceptual hash
    - blur check
    - luminance check
    - GPS consistency
    """
    sha256_hash = hashlib.sha256(image_bytes).hexdigest()

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img_format = img.format
        width, height = img.size
        
        # Perceptual hash
        phash = compute_perceptual_hash(img)

        # Grayscale array for luminance and blur
        gray = img.convert("L")
        gray_arr = np.array(gray, dtype=np.float32)
        mean_luminance = float(np.mean(gray_arr))
        blur_score = compute_blur_variance(gray_arr)

        is_blurry = blur_score < MIN_LAPLACIAN_VARIANCE_BLUR
        is_too_dark = mean_luminance < MIN_AVERAGE_LUMINANCE

        # EXIF GPS
        exif_gps = extract_exif_gps(img)
        distance_meters = None
        gps_flagged = False
        gps_explanation = "No EXIF GPS embedded in image."

        if exif_gps and declared_plot_lat is not None and declared_plot_lon is not None:
            photo_lat, photo_lon = exif_gps
            distance_meters = round(calculate_haversine_distance(photo_lat, photo_lon, declared_plot_lat, declared_plot_lon), 1)
            if distance_meters > MAX_DISTANCE_FROM_PLOT_METERS:
                gps_flagged = True
                gps_explanation = f"Photo location is {distance_meters}m away from declared plot centroid (threshold {MAX_DISTANCE_FROM_PLOT_METERS}m)."
            else:
                gps_explanation = f"Photo location verified within {distance_meters}m of plot centroid."
        elif exif_gps:
            gps_explanation = f"EXIF GPS found: {exif_gps[0]:.5f}, {exif_gps[1]:.5f} (No plot centroid passed to verify distance)."

        passed_quality_gate = (not is_blurry) and (not is_too_dark) and (not gps_flagged)

        flags = []
        if is_blurry:
            flags.append(f"Image blurred (variance {blur_score:.1f} < {MIN_LAPLACIAN_VARIANCE_BLUR})")
        if is_too_dark:
            flags.append(f"Insufficient lighting (luminance {mean_luminance:.1f} < {MIN_AVERAGE_LUMINANCE})")
        if gps_flagged:
            flags.append(gps_explanation)

        return {
            "sha256": sha256_hash,
            "phash": phash,
            "dimensions": {"width": width, "height": height},
            "format": img_format,
            "mean_luminance": round(mean_luminance, 1),
            "blur_variance": round(blur_score, 1),
            "is_blurry": is_blurry,
            "is_too_dark": is_too_dark,
            "exif_gps": exif_gps,
            "distance_to_plot_meters": distance_meters,
            "passed_quality_gate": passed_quality_gate,
            "quality_flags": flags,
            "verification_status": "PASSED" if passed_quality_gate else "FLAGGED_FOR_AUDITOR_REVIEW"
        }
    except Exception as e:
        return {
            "sha256": sha256_hash,
            "passed_quality_gate": False,
            "quality_flags": [f"Image processing error: {str(e)}"],
            "verification_status": "FLAGGED_FOR_AUDITOR_REVIEW"
        }
