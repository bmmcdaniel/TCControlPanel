"""
data_loader.py - Data file loading and validation for Torchcrawl GM Control Panel

Functions:
- load_all_data() -> bool: Load all data files in proper sequence
- load_datafile_config() -> bool: Load master data files configuration
- load_zones_file() -> bool: Load zones and populate zone lists
- load_seasons_file() -> bool: Load seasons and encounter modification percentages
- load_watches_file() -> bool: Load watch periods dynamically
- load_encounters_file() -> bool: Load encounter definitions
- load_weathers_file() -> bool: Load weather definitions
- load_restinfo_file() -> bool: Load rest information
- load_encounter_by_zone_excel() -> bool: Load encounter weights by zone from Excel
- load_weather_by_season_excel() -> bool: Load weather weights by season from Excel
- generate_encounter_by_zone_watch_and_season() -> xr.DataArray: Create 4D encounter array
- validate_data() -> List[str]: Validate all loaded data for consistency
- save_calendar_date(month, day) -> bool: Save current date to calendar YAML
- save_lunar_data(lunar_day, is_blood_moon) -> bool: Save lunar data to calendar YAML

Classes: None
"""

from typing import List
import yaml
import numpy as np
import pandas as pd
import xarray as xr
import config
from utils import parse_percentage, verbose_print
from logger import log_info, log_error, log_warning


def load_all_data() -> bool:
    """
    Load all data files in proper sequence.

    Returns:
        True if all files loaded successfully, False if any failures

    Algorithm:
    1. Load datafile_file to get paths
    2. Load zones_file
    3. Load seasons_file (before encounters and weather Excel)
    4. Load watches_file (before encounters)
    5. Load encounters_file
    6. Load weathers_file
    7. Load restinfo_file
    8. Load encounter_by_zone_file (Excel)
    9. Load weather_by_season_file (Excel)
    10. Generate encounter_by_zone_watch_and_season (4D array)
    11. Validate all data
    12. Load calendar (optional)
    """
    verbose_print("Loading all data files...")

    # Step 1: Load master config
    if not load_datafile_config():
        log_error("Failed to load master data file configuration")
        return False

    # Step 2: Load zones (must be first to populate zone lists)
    if not load_zones_file():
        log_error("Failed to load zones file")
        return False

    # Step 3: Load seasons (before encounters, before weather Excel)
    if not load_seasons_file():
        log_error("Failed to load seasons file")
        return False

    # Step 4: Load watches (before encounters)
    if not load_watches_file():
        log_error("Failed to load watches file")
        return False

    # Step 5: Load encounters
    if not load_encounters_file():
        log_error("Failed to load encounters file")
        return False

    # Step 6: Load weathers
    if not load_weathers_file():
        log_error("Failed to load weathers file")
        return False

    # Step 7: Load rest info
    if not load_restinfo_file():
        log_error("Failed to load rest info file")
        return False

    # Step 8: Load encounter by zone (Excel)
    if not load_encounter_by_zone_excel():
        log_error("Failed to load encounter by zone Excel file")
        return False

    # Step 9: Load weather by season (Excel)
    if not load_weather_by_season_excel():
        log_error("Failed to load weather by season Excel file")
        return False

    # Step 10: Generate 4D encounter array
    verbose_print("Generating 4D encounter array...")
    config.encounter_by_zone_watch_and_season = generate_encounter_by_zone_watch_and_season()
    if config.encounter_by_zone_watch_and_season is None:
        log_error("Failed to generate 4D encounter array")
        return False
    log_info(f"Generated 4D encounter array with shape: {config.encounter_by_zone_watch_and_season.shape}")

    # Step 11: Validate data
    validation_errors = validate_data()
    if validation_errors:
        log_warning(f"Data validation found {len(validation_errors)} issues:")
        for error in validation_errors:
            log_warning(f"  - {error}")
        # Don't fail on validation warnings, just log them

    # Step 12: Load calendar (optional - always succeeds)
    load_calendar_file()

    log_info("All data files loaded successfully")
    verbose_print("All data files loaded successfully")
    return True


def load_datafile_config() -> bool:
    """
    Load master data files configuration.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        verbose_print(f"Loading master config from {config.datafile_file}")
        with open(config.datafile_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        files = data.get('files', {})
        config.encounters_file = files.get('encounters_file', '')
        config.zones_file = files.get('zones_file', '')
        config.weathers_file = files.get('weathers_file', '')
        config.restinfo_file = files.get('restinfo_file', '')
        config.seasons_file = files.get('seasons_file', '')
        config.watches_file = files.get('watches_file', '')
        config.encounter_by_zone_file = files.get('encounter_by_zone_file', '')
        config.weather_by_season_file = files.get('weather_by_season_file', '')
        config.calendar_file = files.get('calendar_file', '')

        log_info(f"Loaded master config from {config.datafile_file}")
        return True
        
    except Exception as e:
        log_error(f"Error loading master config: {e}")
        return False


def load_zones_file() -> bool:
    """
    Load zones and populate zone lists.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        verbose_print(f"Loading zones from {config.zones_file}")
        with open(config.zones_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        zones = data.get('zones', [])
        config.zones_data = {}
        config.overland_zones_list = []
        config.overland_overlay_list = []
        config.site_zones_list = []
        
        for zone in zones:
            name = zone['name']
            types = zone['types']
            encounter_chance = zone['encounter_chance']
            
            config.zones_data[name] = {
                'types': types,
                'encounter_chance': encounter_chance
            }
            
            if 'Overland' in types:
                config.overland_zones_list.append(name)
            if 'Overlay' in types:
                config.overland_overlay_list.append(name)
            if 'Site' in types:
                config.site_zones_list.append(name)
        
        log_info(f"Loaded {len(config.zones_data)} zones")
        log_info(f"  Overland zones: {len(config.overland_zones_list)}")
        log_info(f"  Overlay zones: {len(config.overland_overlay_list)}")
        log_info(f"  Site zones: {len(config.site_zones_list)}")
        
        return True
        
    except Exception as e:
        log_error(f"Error loading zones file: {e}")
        return False


def load_seasons_file() -> bool:
    """
    Load seasons and encounter modification percentages from YAML.

    Returns:
        True if successful, False otherwise
    """
    try:
        verbose_print(f"Loading seasons from {config.seasons_file}")
        with open(config.seasons_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        seasons = data.get('seasons', [])
        config.seasons_list = []
        config.seasons_data = {}

        for season in seasons:
            name = season['name']
            config.seasons_list.append(name)
            config.seasons_data[name] = {
                'encounter_modification': season.get('encounter_modification', '100%')
            }

        log_info(f"Loaded {len(config.seasons_list)} seasons")

        return True

    except Exception as e:
        log_error(f"Error loading seasons file: {e}")
        return False


def load_watches_file() -> bool:
    """
    Load watch periods from YAML.

    Returns:
        True if successful, False otherwise
    """
    try:
        verbose_print(f"Loading watches from {config.watches_file}")
        with open(config.watches_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        watches = data.get('watches', [])
        config.watches_list = []
        config.watches_key_list = []

        for watch in watches:
            name = watch['name']
            config.watches_list.append(name)
            config.watches_key_list.append(name.lower())

        log_info(f"Loaded {len(config.watches_list)} watches")

        return True

    except Exception as e:
        log_error(f"Error loading watches file: {e}")
        return False


def load_encounters_file() -> bool:
    """
    Load encounter definitions.

    Returns:
        True if successful, False otherwise
    """
    try:
        verbose_print(f"Loading encounters from {config.encounters_file}")
        with open(config.encounters_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        encounters = data.get('encounters', [])
        config.encounters_data = {}
        
        for encounter in encounters:
            name = encounter['name']

            # Parse season key into normalized dict: {season_name: float}
            raw_season = encounter.get('season')
            if raw_season is None:
                # Missing/null -> all seasons at 100%
                season_dict = {s: 1.0 for s in config.seasons_list}
            elif isinstance(raw_season, str):
                # String format like "All 100%" or "All X%"
                parts = raw_season.split()
                if len(parts) >= 2 and parts[0].lower() == 'all':
                    pct = parse_percentage(parts[1])
                    season_dict = {s: pct for s in config.seasons_list}
                else:
                    # Unknown string format, default to 100%
                    season_dict = {s: 1.0 for s in config.seasons_list}
            elif isinstance(raw_season, dict):
                # Check for {All: X%} shorthand
                if 'All' in raw_season and len(raw_season) == 1:
                    pct = parse_percentage(str(raw_season['All']))
                    season_dict = {s: pct for s in config.seasons_list}
                else:
                    # Dict format like {Spring: 100%, Summer: 80%, ...}
                    season_dict = {k: parse_percentage(str(v)) for k, v in raw_season.items()}
            else:
                season_dict = {s: 1.0 for s in config.seasons_list}

            config.encounters_data[name] = {
                'description': encounter['description'],
                'habitat': encounter['habitat'],
                'habitat_notes': encounter.get('habitat_notes'),
                'season': season_dict,
                'sparks': encounter['sparks'],
                'watch': encounter['watch']
            }
        
        log_info(f"Loaded {len(config.encounters_data)} encounters")
        
        return True
        
    except Exception as e:
        log_error(f"Error loading encounters file: {e}")
        return False


def load_weathers_file() -> bool:
    """
    Load weather definitions.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        verbose_print(f"Loading weathers from {config.weathers_file}")
        with open(config.weathers_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        weathers = data.get('weathers', [])
        config.weathers_data = {}
        
        for weather in weathers:
            name = weather['name']
            config.weathers_data[name] = {
                'effects': weather['effects']
            }
        
        log_info(f"Loaded {len(config.weathers_data)} weather types")
        
        return True
        
    except Exception as e:
        log_error(f"Error loading weathers file: {e}")
        return False


def load_restinfo_file() -> bool:
    """
    Load rest information.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        verbose_print(f"Loading rest info from {config.restinfo_file}")
        with open(config.restinfo_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        config.restinfo_data = data.get('rest_checks', {})
        
        log_info(f"Loaded rest information")
        
        return True
        
    except Exception as e:
        log_error(f"Error loading rest info file: {e}")
        return False


def load_encounter_by_zone_excel() -> bool:
    """
    Load encounter weights by zone from Excel.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        verbose_print(f"Loading encounter by zone from {config.encounter_by_zone_file}")
        
        # Read Excel file
        df = pd.read_excel(config.encounter_by_zone_file, index_col=0)
        
        # Replace NaN with 0
        df = df.fillna(0)
        
        # Convert to xarray
        config.encounter_by_zone = xr.DataArray(
            df.values,
            coords=[df.index, df.columns],
            dims=['Encounter', 'Zone']
        )
        
        log_info(f"Loaded encounter by zone: {config.encounter_by_zone.shape}")
        
        return True
        
    except Exception as e:
        log_error(f"Error loading encounter by zone Excel: {e}")
        return False


def load_weather_by_season_excel() -> bool:
    """
    Load weather weights by season from Excel.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        verbose_print(f"Loading weather by season from {config.weather_by_season_file}")
        
        # Read Excel file
        df = pd.read_excel(config.weather_by_season_file, index_col=0)
        
        # Replace NaN with 0
        df = df.fillna(0)

        # Validate Excel columns match seasons_list from YAML
        excel_seasons = list(df.columns)
        if set(excel_seasons) != set(config.seasons_list):
            log_warning(f"Weather Excel seasons {excel_seasons} don't match seasons file {config.seasons_list}")

        # Convert to xarray
        config.weather_by_season = xr.DataArray(
            df.values,
            coords=[df.index, df.columns],
            dims=['Weather', 'Season']
        )
        
        log_info(f"Loaded weather by season: {config.weather_by_season.shape}")
        
        return True
        
    except Exception as e:
        log_error(f"Error loading weather by season Excel: {e}")
        return False


def generate_encounter_by_zone_watch_and_season() -> xr.DataArray:
    """
    Create 4D encounter array [Encounter, Zone, Watch, Season] from zone weights,
    watch percentages, and season percentages.

    Encounter list comes from encounters YAML (not Excel). Encounters that exist
    in YAML but not in the Excel zone weights get a zone_weight of 0.

    Algorithm:
    1. Pre-compute 2D zone_weight, watch_pct, and season_pct arrays
    2. Broadcast-multiply: zone_weight[:,:,None,None] * watch_pct[:,None,:,None] * season_pct[:,None,None,:]
    3. Return 4D xarray DataArray

    Returns:
        4D xarray DataArray or None if error
    """
    try:
        encounters = list(config.encounters_data.keys())
        zones = list(config.encounter_by_zone.coords['Zone'].values)
        watches = config.watches_list
        watch_keys = config.watches_key_list
        seasons = config.seasons_list
        excel_encounters = set(config.encounter_by_zone.coords['Encounter'].values)

        n_enc = len(encounters)
        n_zones = len(zones)
        n_watches = len(watches)
        n_seasons = len(seasons)

        # Pre-compute zone weights: [Encounter, Zone]
        zone_weights = np.zeros((n_enc, n_zones))
        for i, enc in enumerate(encounters):
            if enc in excel_encounters:
                for j, zone in enumerate(zones):
                    zone_weights[i, j] = float(config.encounter_by_zone.loc[enc, zone])

        # Pre-compute watch percentages: [Encounter, Watch]
        watch_pcts = np.zeros((n_enc, n_watches))
        for i, enc in enumerate(encounters):
            watch_dict = config.encounters_data[enc]['watch']
            for j, wk in enumerate(watch_keys):
                watch_pcts[i, j] = parse_percentage(watch_dict.get(wk, '0%'))

        # Pre-compute season percentages: [Encounter, Season]
        season_pcts = np.zeros((n_enc, n_seasons))
        for i, enc in enumerate(encounters):
            season_dict = config.encounters_data[enc]['season']
            for j, season in enumerate(seasons):
                season_pcts[i, j] = season_dict.get(season, 0.0)

        # Broadcast multiply to 4D: [Encounter, Zone, Watch, Season]
        data_4d = (zone_weights[:, :, None, None]
                   * watch_pcts[:, None, :, None]
                   * season_pcts[:, None, None, :])

        # Create xarray
        array_4d = xr.DataArray(
            data_4d,
            coords=[encounters, zones, watches, seasons],
            dims=['Encounter', 'Zone', 'Watch', 'Season']
        )

        return array_4d

    except Exception as e:
        log_error(f"Error generating 4D encounter array: {e}")
        return None


def validate_data() -> List[str]:
    """
    Validate all loaded data for consistency and completeness.

    Returns:
        List of validation error messages (empty if all valid)
    """
    errors = []

    # Check encounters referenced in encounter_by_zone exist in encounters_data
    for encounter in config.encounter_by_zone.coords['Encounter'].values:
        if encounter not in config.encounters_data:
            errors.append(f"Encounter '{encounter}' in encounter_by_zone not found in encounters_data")

    # Check zones referenced in encounter_by_zone exist in zones_data
    for zone in config.encounter_by_zone.coords['Zone'].values:
        if zone not in config.zones_data:
            errors.append(f"Zone '{zone}' in encounter_by_zone not found in zones_data")

    # Check weather types exist (except "No Change")
    for weather in config.weather_by_season.coords['Weather'].values:
        if weather != "No Change" and weather not in config.weathers_data:
            errors.append(f"Weather '{weather}' in weather_by_season not found in weathers_data")

    # Check seasons in rest_DCs match seasons_list
    rest_dcs = config.restinfo_data.get('rest_DCs', {})
    for season in rest_dcs.keys():
        if season not in config.seasons_list:
            errors.append(f"Season '{season}' in rest_DCs not found in seasons_list")

    # Check weather Excel columns match or are subset of seasons_list
    if config.weather_by_season is not None:
        excel_seasons = list(config.weather_by_season.coords['Season'].values)
        for season in excel_seasons:
            if season not in config.seasons_list:
                errors.append(f"Season '{season}' in weather Excel not found in seasons_list")

    # Check encounter season dict keys against seasons_list
    for encounter_name, encounter_data in config.encounters_data.items():
        season_dict = encounter_data.get('season', {})
        if isinstance(season_dict, dict):
            for season in season_dict:
                if season not in config.seasons_list:
                    errors.append(f"Season '{season}' in encounter '{encounter_name}' not found in seasons_list")

    # Check encounter watch dict keys against watches_key_list
    for encounter_name, encounter_data in config.encounters_data.items():
        watch_dict = encounter_data.get('watch', {})
        if isinstance(watch_dict, dict):
            for watch_key in watch_dict:
                if watch_key not in config.watches_key_list:
                    errors.append(f"Watch '{watch_key}' in encounter '{encounter_name}' not found in watches_key_list")

    return errors


def load_calendar_file() -> bool:
    """
    Load calendar data from YAML file (optional feature).

    This function always returns True because the calendar is optional.
    If the file doesn't exist, is blank, or has no months, the application
    runs without calendar functionality.

    Returns:
        True always (calendar is optional, missing file is not an error)
    """
    # Reset calendar data
    config.calendar_data = None
    config.calendar_month_lookup = {}

    # Check if calendar file path is configured
    if not config.calendar_file:
        verbose_print("No calendar file configured - running without calendar")
        log_info("No calendar file configured - running without calendar")
        return True

    try:
        verbose_print(f"Loading calendar from {config.calendar_file}")

        with open(config.calendar_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Check if file is blank or has no calendar data
        if not data or 'calendar' not in data:
            verbose_print("Calendar file is blank or missing 'calendar' key - running without calendar")
            log_info("Calendar file is blank or missing 'calendar' key - running without calendar")
            return True

        calendar = data['calendar']

        # Check if calendar has months (required for calendar to be active)
        months = calendar.get('months', [])
        if not months:
            verbose_print("Calendar has no months defined - running without calendar")
            log_info("Calendar has no months defined - running without calendar")
            return True

        # Calendar is valid - store it
        config.calendar_data = calendar

        # Build month lookup dictionary (name -> 1-based index)
        config.calendar_month_lookup = {}
        for i, month in enumerate(months, 1):
            month_name = month.get('name', '')
            if month_name:
                config.calendar_month_lookup[month_name] = i

        # Log success
        num_months = len(months)
        num_holidays = len(calendar.get('holidays', []))
        days_per_week = calendar.get('days_per_week', 6)
        current = calendar.get('current')

        log_info(f"Loaded calendar: {num_months} months, {num_holidays} holidays, {days_per_week} days/week")
        if current:
            log_info(f"  Current date: month {current.get('calendar_month')}, day {current.get('calendar_day')}")
            if current.get('lunar_day'):
                log_info(f"  Lunar day: {current.get('lunar_day')}, blood moon: {current.get('is_blood_moon', False)}")
        else:
            log_info("  No current state set")

        verbose_print(f"Calendar loaded: {num_months} months, {num_holidays} holidays")

        return True

    except FileNotFoundError:
        verbose_print(f"Calendar file not found: {config.calendar_file} - running without calendar")
        log_info(f"Calendar file not found: {config.calendar_file} - running without calendar")
        return True

    except Exception as e:
        log_warning(f"Error loading calendar file: {e} - running without calendar")
        verbose_print(f"Error loading calendar file: {e} - running without calendar")
        return True


def save_calendar_date(month: int, day: int) -> bool:
    """
    Save current date to the calendar YAML file.

    This function updates current.calendar_month and current.calendar_day in
    the calendar file, preserving all other calendar data.

    Args:
        month: 1-based month index (1 to number of months)
        day: 1-based day of month (1 to days in that month)

    Returns:
        True if successful, False otherwise
    """
    if not config.calendar_file or not config.calendar_data:
        log_warning("Cannot save calendar date - no calendar loaded")
        return False

    try:
        # Ensure 'current' dict exists in memory
        if 'current' not in config.calendar_data:
            config.calendar_data['current'] = {}

        # Update in-memory calendar data
        config.calendar_data['current']['calendar_month'] = month
        config.calendar_data['current']['calendar_day'] = day

        # Read the full file to preserve structure and comments
        with open(config.calendar_file, 'r', encoding='utf-8') as f:
            file_data = yaml.safe_load(f)

        # Ensure 'current' dict exists in file data
        if 'current' not in file_data['calendar']:
            file_data['calendar']['current'] = {}

        # Update current in file data
        file_data['calendar']['current']['calendar_month'] = month
        file_data['calendar']['current']['calendar_day'] = day

        # Write back to file
        with open(config.calendar_file, 'w', encoding='utf-8') as f:
            yaml.dump(file_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        log_info(f"Saved calendar date: month {month}, day {day}")
        verbose_print(f"Calendar date saved: month {month}, day {day}")

        return True

    except Exception as e:
        log_error(f"Error saving calendar date: {e}")
        return False


def save_lunar_data(lunar_day: int, is_blood_moon: bool) -> bool:
    """
    Save lunar day and blood moon status to the calendar YAML file.

    This function updates current.lunar_day and current.is_blood_moon in
    the calendar file, preserving all other calendar data.

    Args:
        lunar_day: Current day in lunar cycle (1 to lunar_cycle_length)
        is_blood_moon: Whether current full moon is a blood moon

    Returns:
        True if successful, False otherwise
    """
    if not config.calendar_file or not config.calendar_data:
        log_warning("Cannot save lunar data - no calendar loaded")
        return False

    try:
        # Ensure 'current' dict exists in memory
        if 'current' not in config.calendar_data:
            config.calendar_data['current'] = {}

        # Update in-memory calendar data
        config.calendar_data['current']['lunar_day'] = lunar_day
        config.calendar_data['current']['is_blood_moon'] = is_blood_moon

        # Read the full file to preserve structure and comments
        with open(config.calendar_file, 'r', encoding='utf-8') as f:
            file_data = yaml.safe_load(f)

        # Ensure 'current' dict exists in file data
        if 'current' not in file_data['calendar']:
            file_data['calendar']['current'] = {}

        # Update lunar data in file data
        file_data['calendar']['current']['lunar_day'] = lunar_day
        file_data['calendar']['current']['is_blood_moon'] = is_blood_moon

        # Write back to file
        with open(config.calendar_file, 'w', encoding='utf-8') as f:
            yaml.dump(file_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        log_info(f"Saved lunar data: day {lunar_day}, blood_moon {is_blood_moon}")
        verbose_print(f"Lunar data saved: day {lunar_day}, blood_moon {is_blood_moon}")

        return True

    except Exception as e:
        log_error(f"Error saving lunar data: {e}")
        return False
