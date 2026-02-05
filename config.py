"""
config.py - Global variables and constants for Torchcrawl GM Control Panel

This module defines all global state variables used throughout the application.
Variables are initialized with default values and updated during application runtime.

Global Variables:
- Data file paths (datafile_file, encounters_file, etc.)
- Loaded data structures (zones_data, weathers_data, etc.)
- Lists of available options (overland_zones_list, seasons_list, etc.)
- User-selected values (selected_overland_zone, selected_site_zone, etc.)
- Generated state (generated_overland_days, generated_site_time, etc.)

Functions: None
Classes: None
"""

from typing import Optional, List, Dict
import xarray as xr
from models import Encounter, Weather, Timer


# ============================================================================
# DATA FILE PATHS
# ============================================================================

# Master configuration file
datafile_file: str = "Data/Test Data Files.yaml"

# Individual data file paths (loaded from datafile_file)
encounters_file: str = ""
zones_file: str = ""
weathers_file: str = ""
restinfo_file: str = ""
encounter_by_zone_file: str = ""
weather_by_season_file: str = ""


# ============================================================================
# DATA LOADED FROM FILES
# ============================================================================

# Lists of available options
overland_zones_list: List[str] = []        # Zones with type "Overland"
overland_overlay_list: List[str] = []      # Zones with type "Overlay"
site_zones_list: List[str] = []            # Zones with type "Site"
seasons_list: List[str] = []               # Extracted from weather_by_season column headers

# Structured data (dictionaries/nested structures from YAML)
zones_data: Dict[str, Dict] = {}           # Zone name -> {types: List[str], encounter_chance: str}
weathers_data: Dict[str, Dict] = {}        # Weather name -> {effects: List[str]}
encounters_data: Dict[str, Dict] = {}      # Encounter name -> {description, habitat, sparks, watch}
restinfo_data: Dict = {}                   # Rest check tables and modifiers

# xarray DataArrays (multi-dimensional labeled arrays)
encounter_by_zone: Optional[xr.DataArray] = None              # 2D: [Encounter, Zone]
encounter_by_zone_and_watch: Optional[xr.DataArray] = None    # 3D: [Encounter, Zone, Watch]
weather_by_season: Optional[xr.DataArray] = None              # 2D: [Weather, Season]

# Calendar data (optional feature)
calendar_file: str = ""                           # Path to calendar file (from datafile_file)
calendar_data: Optional[Dict] = None              # Full calendar structure from YAML (includes current_date)
calendar_month_lookup: Dict[str, int] = {}        # Month name -> 1-based index for quick lookups


# ============================================================================
# USER-SELECTED VALUES
# ============================================================================

# Overland mode selections
selected_overland_zone: str = ""       # Must be member of overland_zones_list
selected_overland_overlay: Optional[str] = None  # None or member of overland_overlay_list
selected_overland_season: str = ""     # Must be member of seasons_list

# Site mode selections
selected_site_zone: str = ""           # Must be member of site_zones_list


# ============================================================================
# GENERATED STATE VARIABLES
# ============================================================================

# Overland mode state
generated_overland_days: int = 0                              # Number of days elapsed
generated_overland_weather: Optional[Weather] = None          # Current weather
generated_overland_encounters: Dict[str, Encounter] = {}      # Watch -> Encounter mapping
generated_overland_rest_info: Optional[Dict] = None           # Rest information for current conditions

# Site mode state
generated_site_time: int = 0                                  # Minutes elapsed
generated_site_timers: List[Timer] = []                       # Active timers
generated_site_encounters: Dict[str, Encounter] = {}          # Time slot -> Encounter mapping


# ============================================================================
# CONSTANTS
# ============================================================================

# Watch periods for overland mode
OVERLAND_WATCHES: List[str] = [
    "Dawn",
    "Morning",
    "Afternoon",
    "Dusk",
    "Early Night",
    "Late Night"
]

# Time slots for site mode
SITE_TIME_SLOTS: List[str] = [
    "Current",
    "10 minutes",
    "20 minutes",
    "30 minutes",
    "40 minutes",
    "50 minutes"
]
