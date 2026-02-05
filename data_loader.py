"""
data_loader.py - Data file loading and validation for Torchcrawl GM Control Panel

Functions:
- load_all_data() -> bool: Load all data files in proper sequence
- load_datafile_config() -> bool: Load master data files configuration
- load_zones_file() -> bool: Load zones and populate zone lists
- load_encounters_file() -> bool: Load encounter definitions
- load_weathers_file() -> bool: Load weather definitions
- load_restinfo_file() -> bool: Load rest information
- load_encounter_by_zone_excel() -> bool: Load encounter weights by zone from Excel
- load_weather_by_season_excel() -> bool: Load weather weights by season from Excel
- generate_encounter_by_zone_and_watch() -> xr.DataArray: Create 3D encounter array
- validate_data() -> List[str]: Validate all loaded data for consistency

Classes: None
"""

from typing import List
import yaml
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
    3. Load encounters_file
    4. Load weathers_file
    5. Load restinfo_file
    6. Load encounter_by_zone_file (Excel)
    7. Load weather_by_season_file (Excel)
    8. Derive seasons_list
    9. Generate encounter_by_zone_and_watch (3D array)
    10. Validate all data
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
    
    # Step 3: Load encounters
    if not load_encounters_file():
        log_error("Failed to load encounters file")
        return False
    
    # Step 4: Load weathers
    if not load_weathers_file():
        log_error("Failed to load weathers file")
        return False
    
    # Step 5: Load rest info
    if not load_restinfo_file():
        log_error("Failed to load rest info file")
        return False
    
    # Step 6: Load encounter by zone (Excel)
    if not load_encounter_by_zone_excel():
        log_error("Failed to load encounter by zone Excel file")
        return False
    
    # Step 7: Load weather by season (Excel)
    if not load_weather_by_season_excel():
        log_error("Failed to load weather by season Excel file")
        return False
    
    # Step 8: Derive seasons list (already done in load_weather_by_season_excel)
    
    # Step 9: Generate 3D encounter array
    verbose_print("Generating 3D encounter array...")
    config.encounter_by_zone_and_watch = generate_encounter_by_zone_and_watch()
    if config.encounter_by_zone_and_watch is None:
        log_error("Failed to generate 3D encounter array")
        return False
    log_info(f"Generated 3D encounter array with shape: {config.encounter_by_zone_and_watch.shape}")
    
    # Step 10: Validate data
    validation_errors = validate_data()
    if validation_errors:
        log_warning(f"Data validation found {len(validation_errors)} issues:")
        for error in validation_errors:
            log_warning(f"  - {error}")
        # Don't fail on validation warnings, just log them

    # Step 11: Load calendar (optional - always succeeds)
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
            config.encounters_data[name] = {
                'description': encounter['description'],
                'habitat': encounter['habitat'],
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
        
        # Extract seasons list from column headers
        config.seasons_list = list(df.columns)
        log_info(f"Extracted seasons: {config.seasons_list}")
        
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


def generate_encounter_by_zone_and_watch() -> xr.DataArray:
    """
    Create 3D encounter array [Encounter, Zone, Watch] from 2D array and watch percentages.
    
    Algorithm:
    1. Get list of watch periods
    2. Create empty 3D array
    3. For each encounter/zone/watch:
       Calculate: zone_weight * watch_percentage
    4. Return 3D xarray DataArray
    
    Returns:
        3D xarray DataArray or None if error
    """
    try:
        # Watch periods (map to lowercase keys in encounters data)
        watches = ["Dawn", "Morning", "Afternoon", "Dusk", "Early Night", "Late Night"]
        watch_keys = ["dawn", "morning", "afternoon", "dusk", "early night", "late night"]
        
        # Get dimensions
        encounters = list(config.encounter_by_zone.coords['Encounter'].values)
        zones = list(config.encounter_by_zone.coords['Zone'].values)
        
        # Create 3D array
        data_3d = []
        
        for encounter in encounters:
            encounter_data = []
            for zone in zones:
                zone_data = []
                for i, watch in enumerate(watches):
                    # Get zone weight
                    zone_weight = float(config.encounter_by_zone.loc[encounter, zone])
                    
                    # Get watch percentage
                    watch_key = watch_keys[i]
                    watch_pct_str = config.encounters_data[encounter]['watch'].get(watch_key, '0%')
                    watch_percentage = parse_percentage(watch_pct_str)
                    
                    # Calculate final weight
                    final_weight = zone_weight * watch_percentage
                    zone_data.append(final_weight)
                
                encounter_data.append(zone_data)
            data_3d.append(encounter_data)
        
        # Create xarray
        array_3d = xr.DataArray(
            data_3d,
            coords=[encounters, zones, watches],
            dims=['Encounter', 'Zone', 'Watch']
        )
        
        return array_3d
        
    except Exception as e:
        log_error(f"Error generating 3D encounter array: {e}")
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
        current_date = calendar.get('current_date')

        log_info(f"Loaded calendar: {num_months} months, {num_holidays} holidays, {days_per_week} days/week")
        if current_date:
            log_info(f"  Current date: month {current_date.get('month')}, day {current_date.get('day')}")
        else:
            log_info("  No current date set")

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

    This function updates the current_date in the calendar file, preserving
    all other calendar data (months, holidays, etc.).

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
        # Update in-memory calendar data
        config.calendar_data['current_date'] = {
            'month': month,
            'day': day
        }

        # Read the full file to preserve structure and comments
        with open(config.calendar_file, 'r', encoding='utf-8') as f:
            file_data = yaml.safe_load(f)

        # Update current_date in file data
        file_data['calendar']['current_date'] = {
            'month': month,
            'day': day
        }

        # Write back to file
        with open(config.calendar_file, 'w', encoding='utf-8') as f:
            yaml.dump(file_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        log_info(f"Saved calendar date: month {month}, day {day}")
        verbose_print(f"Calendar date saved: month {month}, day {day}")

        return True

    except Exception as e:
        log_error(f"Error saving calendar date: {e}")
        return False
