"""
forage_logic.py - Forage mode encounter generation

Functions:
- generate_forage_encounter() -> Encounter: Generates a forage encounter for current zone/overlay/season
- regenerate_forage_encounter() -> Encounter: Regenerates the current forage encounter

Classes: None
"""

import config
from models import Encounter
from logger import log_info
from utils import verbose_print


def generate_forage_encounter() -> Encounter:
    """
    Generate a forage encounter using current zone/overlay/season.

    Algorithm:
    1. Create new Encounter instance
    2. Call encounter.generate_forage_encounter() with current selections
    3. Store in config.generated_forage_encounter
    4. Return encounter instance

    Returns:
        Generated Encounter object (always has an encounter, never None name)
    """
    verbose_print("=== Generating Forage Encounter ===")

    encounter = Encounter()

    encounter.generate_forage_encounter(
        zone=config.selected_overland_zone,
        overlay=config.selected_overland_overlay,
        season=config.selected_overland_season,
        encounters_data=config.encounters_data,
        encounter_by_zone_watch_and_season=config.encounter_by_zone_watch_and_season,
        zones_data=config.zones_data,
        seasons_data=config.seasons_data
    )

    config.generated_forage_encounter = encounter

    verbose_print("=== Forage encounter generation complete ===")

    return encounter


def regenerate_forage_encounter() -> Encounter:
    """
    Regenerate the forage encounter using current selections.

    This function is called when user clicks the regenerate button.

    Returns:
        Regenerated Encounter object
    """
    log_info("Forage: Regenerating encounter")
    return generate_forage_encounter()
