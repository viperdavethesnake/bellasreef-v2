"""
Provides a static list of predefined, famous reef locations for use in 
LocationBased lighting behavior presets.
"""
from typing import List, Dict, TypedDict

class LocationPreset(TypedDict):
    name: str
    latitude: float
    longitude: float
    time_zone: str

# A static list of 10 popular and famous reef locations.
REEF_LOCATION_PRESETS: List[LocationPreset] = [
    {
        "name": "Great Barrier Reef, Australia",
        "latitude": -18.28,
        "longitude": 147.70,
        "time_zone": "Australia/Lindeman"
    },
    {
        "name": "Red Sea Reef, Egypt",
        "latitude": 27.27,
        "longitude": 33.88,
        "time_zone": "Africa/Cairo"
    },
    {
        "name": "Belize Barrier Reef, Belize",
        "latitude": 17.19,
        "longitude": -87.54,
        "time_zone": "America/Belize"
    },
    {
        "name": "Maldives Atolls, Maldives",
        "latitude": 3.20,
        "longitude": 73.22,
        "time_zone": "Indian/Maldives"
    },
    {
        "name": "Raja Ampat Islands, Indonesia",
        "latitude": -0.50,
        "longitude": 130.50,
        "time_zone": "Asia/Jayapura"
    },
    {
        "name": "Fiji Reefs, Fiji",
        "latitude": -18.14,
        "longitude": 179.41,
        "time_zone": "Pacific/Fiji"
    },
    {
        "name": "Bora Bora, French Polynesia",
        "latitude": -16.50,
        "longitude": -151.74,
        "time_zone": "Pacific/Tahiti"
    },
    {
        "name": "Cozumel Reefs, Mexico",
        "latitude": 20.35,
        "longitude": -87.03,
        "time_zone": "America/Cancun"
    },
    {
        "name": "Sipadan Island, Malaysia",
        "latitude": 4.11,
        "longitude": 118.62,
        "time_zone": "Asia/Kuala_Lumpur"
    },
    {
        "name": "Hawaiian Islands, USA",
        "latitude": 21.31,
        "longitude": -157.85,
        "time_zone": "Pacific/Honolulu"
    }
]

def get_all_presets() -> List[LocationPreset]:
    """Returns the static list of all reef location presets."""
    return REEF_LOCATION_PRESETS 