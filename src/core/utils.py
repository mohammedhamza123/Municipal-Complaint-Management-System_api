"""
Utility functions
"""
import hashlib
from typing import Optional


def generate_area_hash(
    latitude: float,
    longitude: float,
    precision: int = 3
) -> str:
    """
    Generate a hash for a geographic area to prevent duplicate issues.
    
    The precision controls how large the "same area" is:
      - precision=3 → ~111m radius (good for municipal complaints)
      - precision=4 → ~11m radius
      - precision=5 → ~1.1m radius
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        precision: Number of decimal places (default: 3 → ~111m)
    
    Returns:
        SHA256 hash of the rounded coordinates
    """
    # Round coordinates to specified precision
    lat_rounded = round(latitude, precision)
    lon_rounded = round(longitude, precision)
    
    # Create hash string
    area_string = f"{lat_rounded},{lon_rounded}"
    
    # Generate SHA256 hash
    area_hash = hashlib.sha256(area_string.encode()).hexdigest()
    
    return area_hash


def calculate_priority(complaints_count: int) -> int:
    """
    Calculate issue priority based on number of complaints.
    
    Priority levels:
      1 = Low      (1-2 complaints)
      2 = Medium   (3-5 complaints)
      3 = High     (6-10 complaints)
      4 = Critical (11+ complaints)
    
    Args:
        complaints_count: Number of complaints linked to the issue
    
    Returns:
        Priority level (1-4)
    """
    if complaints_count >= 11:
        return 4  # Critical
    elif complaints_count >= 6:
        return 3  # High
    elif complaints_count >= 3:
        return 2  # Medium
    else:
        return 1  # Low
