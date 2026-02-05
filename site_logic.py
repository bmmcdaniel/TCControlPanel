"""
site_logic.py - Site mode encounter generation and timer management

Functions:
- site_reset() -> None: Resets all site state variables
- site_new_turn() -> None: Advances turn by 10 minutes and updates state
- site_regenerate_turn() -> None: Regenerates current turn's encounters
- generate_site_encounters(include_current: bool = False) -> Dict[str, Encounter]: Creates encounters for all time slots
- site_add_timer(name: str, duration: int = 60) -> None: Creates and adds new timer
- site_delete_timer(timer_index: int) -> None: Removes timer from list
- regenerate_individual_site_encounter(time_slot: str) -> Encounter: Regenerates single encounter

Classes: None
"""

from typing import Dict
import config
from models import Encounter, Timer
from logger import log_info, log_error
from utils import verbose_print


def site_reset() -> None:
    """
    Reset all site state variables to initial values.
    
    Algorithm:
    1. Set generated_site_time = 0
    2. Set generated_site_timers = [] (empty)
    3. Clear expansion states
    4. Generate initial encounters (Current empty, next 5 generated)
    """
    from nicegui import app
    
    config.generated_site_time = 0
    config.generated_site_timers = []
    
    # Clear expansion states
    app.storage.user['site_expansions'] = {}
    
    # Generate initial encounters (Current is empty, next 5 are generated)
    generate_site_encounters(include_current=False)
    
    log_info("Site mode reset")
    verbose_print("Site mode reset to 0 minutes")


def site_new_turn() -> None:
    """
    Advance to next turn (10 minutes) and update all site state.
    
    Algorithm:
    1. Increment generated_site_time by 10
    2. Update timers (decrement and remove expired)
    3. Advance encounters (shift up one slot)
    4. Shift expansion states along with encounters
    5. Generate new 50 minutes encounter
    """
    from nicegui import app
    
    config.generated_site_time += 10
    
    log_info(f"Site: Advanced to {config.generated_site_time} minutes")
    verbose_print(f"=== New Turn: {config.generated_site_time} minutes ===")
    
    # Step 2: Update timers
    verbose_print("Updating timers...")
    
    for timer in config.generated_site_timers:
        timer.decrement_timer(10)
    
    # Remove timers that have gone negative
    # Keep timers that are 0 or positive
    config.generated_site_timers = [t for t in config.generated_site_timers if t.remaining_duration >= 0]
    
    # Step 3: Shift expansion states before shifting encounters
    # Get current expansion states
    old_expansions = app.storage.user.get('site_expansions', {})
    new_expansions = {}
    
    # Shift expansion states along with encounters
    # If "20 minutes" was expanded, "10 minutes" should be expanded after shift
    new_expansions["Current"] = old_expansions.get("10 minutes", False)
    new_expansions["10 minutes"] = old_expansions.get("20 minutes", False)
    new_expansions["20 minutes"] = old_expansions.get("30 minutes", False)
    new_expansions["30 minutes"] = old_expansions.get("40 minutes", False)
    new_expansions["40 minutes"] = old_expansions.get("50 minutes", False)
    new_expansions["50 minutes"] = False  # New encounter, not expanded
    
    # Save shifted expansion states
    app.storage.user['site_expansions'] = new_expansions
    
    # Step 4: Advance encounters
    verbose_print("Advancing encounters...")
    
    # Shift encounters up
    old_encounters = config.generated_site_encounters.copy()
    new_encounters = {}
    
    # Current becomes what was at 10 minutes
    new_encounters["Current"] = old_encounters.get("10 minutes", Encounter())
    new_encounters["10 minutes"] = old_encounters.get("20 minutes", Encounter())
    new_encounters["20 minutes"] = old_encounters.get("30 minutes", Encounter())
    new_encounters["30 minutes"] = old_encounters.get("40 minutes", Encounter())
    new_encounters["40 minutes"] = old_encounters.get("50 minutes", Encounter())
    
    # Generate new 50 minutes encounter
    verbose_print("  Generating new 50 minutes encounter:")
    new_50_encounter = Encounter()
    new_50_encounter.generate_site_encounter(
        zone=config.selected_site_zone,
        time_slot="50 minutes",
        encounters_data=config.encounters_data,
        encounter_by_zone=config.encounter_by_zone,
        zones_data=config.zones_data
    )
    new_encounters["50 minutes"] = new_50_encounter
    
    # Update global state
    config.generated_site_encounters = new_encounters
    
    verbose_print(f"=== Turn {config.generated_site_time} minutes complete ===")


def site_regenerate_turn() -> None:
    """
    Regenerate current turn's encounters without advancing time or timers.
    
    Algorithm:
    1. Do NOT change generated_site_time
    2. Do NOT change generated_site_timers
    3. Regenerate all 6 encounter slots (including Current)
    """
    log_info(f"Site: Regenerating turn at {config.generated_site_time} minutes")
    verbose_print(f"=== Regenerating Turn: {config.generated_site_time} minutes ===")
    
    # Regenerate all encounters (including Current this time)
    generate_site_encounters(include_current=True)
    
    verbose_print(f"=== Turn regeneration complete ===")


def generate_site_encounters(include_current: bool = False) -> Dict[str, Encounter]:
    """
    Generate encounters for current turn and next 5 turns.
    
    Algorithm:
    1. Define time slots
    2. Create empty encounters dictionary
    3. For each time slot:
       - If Current and include_current=False: create empty encounter
       - Otherwise: generate encounter
    4. Set generated_site_encounters
    5. Return encounters dictionary
    
    Args:
        include_current: If True, generate encounter for "Current" slot
                        If False, leave "Current" as empty (used on initial reset)
    
    Returns:
        Dictionary mapping time slot names to Encounter objects
    """
    verbose_print("Generating site encounters...")
    
    encounters = {}
    
    for time_slot in config.SITE_TIME_SLOTS:
        if time_slot == "Current" and not include_current:
            # Leave Current empty on initial reset
            encounters["Current"] = Encounter()
            verbose_print(f"  Current: (empty)")
        else:
            verbose_print(f"  {time_slot}:")
            
            # Create new encounter instance
            encounter = Encounter()
            
            # Generate encounter
            encounter.generate_site_encounter(
                zone=config.selected_site_zone,
                time_slot=time_slot,
                encounters_data=config.encounters_data,
                encounter_by_zone=config.encounter_by_zone,
                zones_data=config.zones_data
            )
            
            encounters[time_slot] = encounter
    
    # Update global state
    config.generated_site_encounters = encounters
    
    return encounters


def site_add_timer(name: str, duration: int = 60) -> None:
    """
    Create and add a new timer to the active timers list.
    
    Algorithm:
    1. Validate duration >= 0
    2. Create new Timer instance
    3. Append to generated_site_timers
    4. Sort timers by remaining_duration (shortest first)
    
    Args:
        name: Description of what timer tracks
        duration: Starting duration in minutes (default 60)
    """
    # Validate duration
    if duration < 0:
        duration = 0
    
    # Create timer
    timer = Timer(name=name, remaining_duration=duration)
    
    # Add to list
    config.generated_site_timers.append(timer)
    
    # Sort by remaining duration (shortest first)
    config.generated_site_timers.sort(key=lambda t: t.remaining_duration)
    
    log_info(f"Timer added: {name} ({duration} minutes)")
    verbose_print(f"Timer added: {name} ({duration} minutes)")


def site_delete_timer(timer_index: int) -> None:
    """
    Manually remove a timer from the active timers list.
    
    Algorithm:
    1. Validate timer_index
    2. Get timer name for logging
    3. Remove timer from list
    4. Log deletion
    
    Args:
        timer_index: Index of timer in generated_site_timers list
    """
    # Validate index
    if timer_index < 0 or timer_index >= len(config.generated_site_timers):
        log_error(f"Invalid timer index: {timer_index}")
        return
    
    # Get timer name
    timer = config.generated_site_timers[timer_index]
    timer_name = timer.name
    
    # Remove timer
    del config.generated_site_timers[timer_index]
    
    log_info(f"Timer deleted: {timer_name}")
    verbose_print(f"Timer deleted: {timer_name}")


def regenerate_individual_site_encounter(time_slot: str) -> Encounter:
    """
    Regenerate a single encounter for a specific time slot.
    
    This function is called when user clicks [R] button next to an encounter.
    
    Algorithm:
    1. Create new Encounter instance
    2. Call encounter.generate_site_encounter() with CURRENT zone
    3. Update generated_site_encounters[time_slot]
    4. Return encounter instance
    
    Args:
        time_slot: The time slot to regenerate (e.g., "Current", "10 minutes")
    
    Returns:
        Regenerated Encounter object
    """
    log_info(f"Site: Regenerating {time_slot} encounter")
    verbose_print(f"=== Regenerating {time_slot} Encounter ===")
    
    # Create new encounter instance
    encounter = Encounter()
    
    # Generate encounter using CURRENT zone selection
    encounter.generate_site_encounter(
        zone=config.selected_site_zone,  # Use current zone
        time_slot=time_slot,
        encounters_data=config.encounters_data,
        encounter_by_zone=config.encounter_by_zone,
        zones_data=config.zones_data
    )
    
    # Update global state
    config.generated_site_encounters[time_slot] = encounter
    
    verbose_print(f"=== {time_slot} encounter regeneration complete ===")
    
    return encounter
