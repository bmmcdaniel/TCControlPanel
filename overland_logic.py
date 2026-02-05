"""
overland_logic.py - Overland mode encounter and weather generation

Functions:
- overland_reset() -> None: Resets all overland state variables
- overland_new_day() -> None: Advances day counter and generates new content
- overland_regenerate_day() -> None: Regenerates current day's content
- generate_overland_weather() -> Weather: Creates weather instance for current day
- generate_overland_encounters() -> Dict[str, Encounter]: Creates encounters for all watches
- generate_overland_rest_info() -> Dict: Generates rest information
- regenerate_individual_weather() -> Weather: Regenerates only weather using current season
- regenerate_individual_overland_encounter(watch: str) -> Encounter: Regenerates single encounter

Classes: None
"""

from typing import Dict
import config
from models import Weather, Encounter
from logger import log_info
from utils import verbose_print


def overland_reset() -> None:
    """
    Reset all overland state variables to initial values.
    
    Algorithm:
    1. Set generated_overland_days = 0
    2. Set generated_overland_weather = None
    3. Set generated_overland_encounters = {} (empty)
    4. Set generated_overland_rest_info = None
    """
    config.generated_overland_days = 0
    config.generated_overland_weather = None
    config.generated_overland_encounters = {}
    config.generated_overland_rest_info = None
    
    log_info("Overland mode reset")
    verbose_print("Overland mode reset to Day 0")


def overland_new_day() -> None:
    """
    Advance to next day and generate all new content.
    
    Algorithm:
    1. Increment generated_overland_days by 1
    2. Generate weather
    3. Generate encounters for all watches
    4. Generate rest info
    """
    config.generated_overland_days += 1
    
    log_info(f"Overland: Advanced to Day {config.generated_overland_days}")
    verbose_print(f"=== New Day: Day {config.generated_overland_days} ===")
    
    # Generate all content
    generate_overland_weather()
    generate_overland_encounters()
    generate_overland_rest_info()
    
    verbose_print(f"=== Day {config.generated_overland_days} complete ===")


def overland_regenerate_day() -> None:
    """
    Regenerate current day's content without advancing day counter.
    
    Algorithm:
    1. Do NOT change generated_overland_days
    2. Generate weather
    3. Generate encounters for all watches
    4. Generate rest info
    """
    log_info(f"Overland: Regenerating Day {config.generated_overland_days}")
    verbose_print(f"=== Regenerating Day {config.generated_overland_days} ===")
    
    # Regenerate all content
    generate_overland_weather()
    generate_overland_encounters()
    generate_overland_rest_info()
    
    verbose_print(f"=== Day {config.generated_overland_days} regeneration complete ===")


def generate_overland_weather() -> Weather:
    """
    Generate weather for the current day.
    
    Algorithm:
    1. Get previous weather
    2. Create new Weather instance
    3. Call weather.generate_weather()
    4. Set generated_overland_weather
    5. Return weather instance
    
    Returns:
        Generated Weather object
    """
    verbose_print("Generating weather...")
    
    # Get previous weather
    previous_weather = config.generated_overland_weather
    
    # Create new weather instance
    weather = Weather()
    
    # Generate weather
    weather.generate_weather(
        season=config.selected_overland_season,
        previous_weather=previous_weather,
        weather_by_season=config.weather_by_season,
        weathers_data=config.weathers_data
    )
    
    # Update global state
    config.generated_overland_weather = weather
    
    return weather


def generate_overland_encounters() -> Dict[str, Encounter]:
    """
    Generate encounters for all six watches of the day.
    
    Algorithm:
    1. Define watch list
    2. Create empty encounters dictionary
    3. For each watch, generate encounter
    4. Set generated_overland_encounters
    5. Return encounters dictionary
    
    Returns:
        Dictionary mapping watch names to Encounter objects
    """
    verbose_print("Generating encounters...")
    
    encounters = {}
    
    for watch in config.OVERLAND_WATCHES:
        verbose_print(f"  {watch}:")
        
        # Create new encounter instance
        encounter = Encounter()
        
        # Generate encounter
        encounter.generate_overland_encounter(
            zone=config.selected_overland_zone,
            overlay=config.selected_overland_overlay,
            watch=watch,
            encounters_data=config.encounters_data,
            encounter_by_zone_and_watch=config.encounter_by_zone_and_watch,
            zones_data=config.zones_data
        )
        
        encounters[watch] = encounter
    
    # Update global state
    config.generated_overland_encounters = encounters
    
    return encounters


def generate_overland_rest_info() -> Dict:
    """
    Generate rest check information for current conditions.
    
    Algorithm:
    1. Get rest_DCs for current season
    2. Get weather_modifiers list
    3. Filter weather_modifiers based on current weather effects
    4. Get situational_modifiers (unfiltered)
    5. Create rest_info dictionary
    6. Set generated_overland_rest_info
    7. Return rest_info
    
    Returns:
        Dictionary containing rest check information
    """
    verbose_print("Generating rest info...")
    
    # Get rest DCs for current season
    rest_dcs = config.restinfo_data.get('rest_DCs', {}).get(config.selected_overland_season, [])
    
    # Get all weather modifiers
    all_weather_modifiers = config.restinfo_data.get('weather_modifiers', [])
    
    # Filter weather modifiers based on current weather effects
    filtered_weather_modifiers = []
    if config.generated_overland_weather and config.generated_overland_weather.effects:
        current_effects = config.generated_overland_weather.effects
        for modifier in all_weather_modifiers:
            if modifier['effect'] in current_effects:
                filtered_weather_modifiers.append(modifier)
    
    # Get situational modifiers (unfiltered)
    situational_modifiers = config.restinfo_data.get('situational_modifiers', [])
    
    # Create rest info dictionary
    rest_info = {
        'rest_dcs': rest_dcs,
        'weather_modifiers': filtered_weather_modifiers,
        'situational_modifiers': situational_modifiers
    }
    
    # Update global state
    config.generated_overland_rest_info = rest_info
    
    log_info(f"Generated rest info: {len(rest_dcs)} DCs, {len(filtered_weather_modifiers)} weather modifiers, {len(situational_modifiers)} situational modifiers")
    
    return rest_info


def regenerate_individual_weather() -> Weather:
    """
    Regenerate only the weather using CURRENT season selection.
    
    This function is called when user clicks [R] button next to weather.
    Unlike regenerate_day, this only regenerates weather (not encounters).
    
    Algorithm:
    1. Get previous weather (for "No Change" logic)
    2. Create new Weather instance
    3. Call weather.generate_weather() with CURRENT season
    4. Set generated_overland_weather
    5. Regenerate rest info (depends on weather)
    6. Return weather instance
    
    Returns:
        Regenerated Weather object
    """
    log_info("Overland: Regenerating individual weather")
    verbose_print("=== Regenerating Weather ===")
    
    # Get previous weather
    previous_weather = config.generated_overland_weather
    
    # Create new weather instance
    weather = Weather()
    
    # Generate weather using CURRENT season selection
    weather.generate_weather(
        season=config.selected_overland_season,  # Use current season
        previous_weather=previous_weather,
        weather_by_season=config.weather_by_season,
        weathers_data=config.weathers_data
    )
    
    # Update global state
    config.generated_overland_weather = weather
    
    # Regenerate rest info (weather affects modifiers)
    generate_overland_rest_info()
    
    verbose_print("=== Weather regeneration complete ===")
    
    return weather


def regenerate_individual_overland_encounter(watch: str) -> Encounter:
    """
    Regenerate a single encounter for a specific watch period.
    
    This function is called when user clicks [R] button next to an encounter.
    
    Algorithm:
    1. Create new Encounter instance
    2. Call encounter.generate_overland_encounter() with CURRENT zone/overlay
    3. Update generated_overland_encounters[watch]
    4. Return encounter instance
    
    Args:
        watch: The watch to regenerate (e.g., "Dawn", "Morning")
    
    Returns:
        Regenerated Encounter object
    """
    log_info(f"Overland: Regenerating {watch} encounter")
    verbose_print(f"=== Regenerating {watch} Encounter ===")
    
    # Create new encounter instance
    encounter = Encounter()
    
    # Generate encounter using CURRENT zone/overlay selections
    encounter.generate_overland_encounter(
        zone=config.selected_overland_zone,      # Use current zone
        overlay=config.selected_overland_overlay, # Use current overlay
        watch=watch,
        encounters_data=config.encounters_data,
        encounter_by_zone_and_watch=config.encounter_by_zone_and_watch,
        zones_data=config.zones_data
    )
    
    # Update global state
    config.generated_overland_encounters[watch] = encounter
    
    verbose_print(f"=== {watch} encounter regeneration complete ===")
    
    return encounter
