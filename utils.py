"""
utils.py - Utility functions for Torchcrawl GM Control Panel

Functions:
- weighted_random_choice(weights: Dict[str, float]) -> str: Select random key based on weighted probabilities
- parse_percentage(percentage_str: str) -> float: Convert percentage string to float (0.0-1.0)
- verbose_print(message: str) -> None: Print to console if verbose mode enabled
- is_verbose() -> bool: Check if verbose mode is enabled
- format_time_display(minutes: int) -> str: Format time with hours/minutes if > 50
- get_calendar_date_string() -> str: Format current calendar date for display
- get_current_season() -> str: Get season from current calendar month
- advance_calendar_date(days: int) -> bool: Advance calendar date and save to file
- get_current_holiday() -> dict | None: Get holiday for current date if any
- get_moon_phase_info() -> dict | None: Get current moon phase name, icon, index
- get_moon_phase_for_day(lunar_day, cycle_length) -> dict: Get phase info for specific lunar day
- advance_lunar_day(days: int) -> bool: Advance lunar day and handle blood moon roll
- set_lunar_day_to_phase(phase_index: int) -> bool: Set lunar day to start of a phase
- adjust_lunar_day(delta: int) -> bool: Adjust lunar day by +/- delta
- initialize_lunar_day() -> bool: Randomize lunar day if not set

Classes: None
"""

from typing import Dict, Optional
import random
import math

# Global variable for verbose mode (set by command line argument)
_VERBOSE_MODE = False


def set_verbose_mode(verbose: bool) -> None:
    """
    Set the global verbose mode state.
    
    Args:
        verbose: True to enable verbose mode, False to disable
    """
    global _VERBOSE_MODE
    _VERBOSE_MODE = verbose


def is_verbose() -> bool:
    """
    Check if verbose mode is enabled.
    
    Returns:
        True if -v or --verbose command line argument was provided, False otherwise
    """
    return _VERBOSE_MODE


def verbose_print(message: str) -> None:
    """
    Print message to console only if verbose mode is enabled.
    
    Args:
        message: String to print
    
    Side effects:
        Prints to stdout if is_verbose() returns True
    
    Example:
        verbose_print("Generated weather: Heavy Rains")
        # Only prints if -v flag was used
    """
    if is_verbose():
        print(f"[VERBOSE] {message}")


def weighted_random_choice(weights: Dict[str, float]) -> str:
    """
    Select a random key from a dictionary based on weighted probabilities.
    
    Algorithm:
    1. Filter out entries with weight <= 0
    2. Calculate total weight (sum of all values)
    3. If total weight == 0: raise ValueError
    4. Generate random number between 0 and total_weight
    5. Iterate through weights, accumulating until random number reached
    6. Return selected key
    
    Args:
        weights: Dictionary mapping choices to weights (higher = more likely)
        Example: {"Ankheg": 1.2, "Bear": 0.5, "Traveler": 2.4}
    
    Returns:
        Selected key (string)
    
    Raises:
        ValueError: If all weights are 0 or dictionary is empty
    
    Example:
        weights = {"A": 70, "B": 20, "C": 10}
        # A has 70% chance, B has 20% chance, C has 10% chance
        result = weighted_random_choice(weights)
    """
    # Filter out zero/negative weights
    valid_weights = {k: v for k, v in weights.items() if v > 0}
    
    if not valid_weights:
        raise ValueError("No valid weights provided (all weights are 0 or negative)")
    
    # Calculate total weight
    total_weight = sum(valid_weights.values())
    
    if total_weight == 0:
        raise ValueError("Total weight is 0")
    
    # Generate random number
    rand_value = random.uniform(0, total_weight)
    
    # Select based on cumulative weights
    cumulative = 0
    for key, weight in valid_weights.items():
        cumulative += weight
        if rand_value <= cumulative:
            return key
    
    # Should never reach here, but return last key as fallback
    return list(valid_weights.keys())[-1]


def parse_percentage(percentage_str: str) -> float:
    """
    Convert percentage string to float.
    
    Algorithm:
    1. Strip whitespace
    2. Remove "%" symbol if present
    3. Convert to float
    4. Divide by 100 to get decimal (15% -> 0.15)
    5. Clamp to range [0.0, 1.0]
    
    Args:
        percentage_str: String like "15%", "15", " 15 %", "0%", "100%"
    
    Returns:
        Float between 0.0 and 1.0
    
    Raises:
        ValueError: If string cannot be parsed as number
    
    Examples:
        parse_percentage("15%") -> 0.15
        parse_percentage("100%") -> 1.0
        parse_percentage("0") -> 0.0
    """
    # Strip whitespace
    cleaned = percentage_str.strip()
    
    # Remove % symbol if present
    if cleaned.endswith('%'):
        cleaned = cleaned[:-1].strip()
    
    # Convert to float
    try:
        value = float(cleaned)
    except ValueError:
        raise ValueError(f"Cannot parse '{percentage_str}' as a percentage")
    
    # Convert to decimal and clamp
    decimal_value = value / 100.0
    return max(0.0, min(1.0, decimal_value))


def format_time_display(minutes: int) -> str:
    """
    Format time display for Site mode.
    
    If minutes <= 50: Return "X minutes"
    If minutes > 50: Return "X minutes (H hours M minutes)"
    
    Args:
        minutes: Total minutes elapsed
    
    Returns:
        Formatted time string
    
    Examples:
        format_time_display(20) -> "20 minutes"
        format_time_display(50) -> "50 minutes"
        format_time_display(60) -> "60 minutes (1 hour 0 minutes)"
        format_time_display(130) -> "130 minutes (2 hours 10 minutes)"
        format_time_display(220) -> "220 minutes (3 hours 40 minutes)"
    """
    if minutes <= 50:
        return f"{minutes} minutes"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    return f"{minutes} minutes ({hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''})"


# ============================================================================
# CALENDAR UTILITY FUNCTIONS
# ============================================================================

def get_calendar_date_string() -> str:
    """
    Format the current calendar date for display.

    Returns:
        - "Deepwinter 15 (Winter)" if calendar active with date set
        - "No date set - set date via Calendar tab" if calendar active but no date
        - "" (empty string) if no calendar loaded

    Example:
        date_str = get_calendar_date_string()
        # Returns: "Deepwinter 15 (Winter)"
    """
    import config  # Lazy import to avoid circular dependency

    # No calendar loaded
    if not config.calendar_data:
        return ""

    # Calendar loaded but no date set
    current_date = config.calendar_data.get('current_date')
    if not current_date:
        return "No date set - set date via Calendar tab"

    # Get month and day
    month_idx = current_date.get('month', 1)
    day = current_date.get('day', 1)

    # Get month info
    months = config.calendar_data.get('months', [])
    if month_idx < 1 or month_idx > len(months):
        return "Invalid date"

    month_info = months[month_idx - 1]
    month_name = month_info.get('name', 'Unknown')
    season = month_info.get('season', 'Unknown')

    return f"{month_name} {day} ({season})"


def get_current_season() -> str:
    """
    Get the season from the current calendar month.

    Returns:
        - Season name (e.g., "Winter", "Spring") if calendar active with date
        - "" (empty string) if no calendar or no date set

    Example:
        season = get_current_season()
        # Returns: "Winter"
    """
    import config  # Lazy import to avoid circular dependency

    # No calendar loaded
    if not config.calendar_data:
        return ""

    # No date set
    current_date = config.calendar_data.get('current_date')
    if not current_date:
        return ""

    # Get month index
    month_idx = current_date.get('month', 1)

    # Get month info
    months = config.calendar_data.get('months', [])
    if month_idx < 1 or month_idx > len(months):
        return ""

    month_info = months[month_idx - 1]
    return month_info.get('season', '')


def advance_calendar_date(days: int = 1) -> bool:
    """
    Advance the calendar date by the specified number of days.

    Handles month overflow (wraps to next month when days exceed month length).
    Wraps to month 1 when reaching the end of the calendar (no year tracking).
    Saves the new date to the calendar file.

    Args:
        days: Number of days to advance (default 1)

    Returns:
        True if successful, False if no calendar or save failed

    Example:
        # Advance by one day
        success = advance_calendar_date(1)

        # Advance by multiple days
        success = advance_calendar_date(7)
    """
    import config  # Lazy import to avoid circular dependency
    from data_loader import save_calendar_date

    # No calendar loaded
    if not config.calendar_data:
        return False

    # No date set - cannot advance
    current_date = config.calendar_data.get('current_date')
    if not current_date:
        return False

    # Get current position
    month = current_date.get('month', 1)
    day = current_date.get('day', 1)
    months = config.calendar_data.get('months', [])

    if not months:
        return False

    # Add days
    day += days

    # Handle overflow - advance months as needed
    while True:
        # Get days in current month
        if month < 1 or month > len(months):
            month = 1  # Safety wrap

        days_in_month = months[month - 1].get('days', 30)

        if day <= days_in_month:
            break  # Day is valid for current month

        # Overflow to next month
        day -= days_in_month
        month += 1

        # Wrap to month 1 if past last month (no year tracking)
        if month > len(months):
            month = 1

    # Save new date
    return save_calendar_date(month, day)


def get_current_holiday() -> Optional[Dict]:
    """
    Get the holiday for the current date, if any.

    Returns:
        - Holiday dict with keys: name, description, month, day
        - None if no calendar, no date set, or current date is not a holiday

    Example:
        holiday = get_current_holiday()
        if holiday:
            print(f"Today is {holiday['name']}")
            print(f"  {holiday['description']}")
    """
    import config  # Lazy import to avoid circular dependency

    # No calendar loaded
    if not config.calendar_data:
        return None

    # No date set
    current_date = config.calendar_data.get('current_date')
    if not current_date:
        return None

    # Get current month name and day
    month_idx = current_date.get('month', 1)
    day = current_date.get('day', 1)

    months = config.calendar_data.get('months', [])
    if month_idx < 1 or month_idx > len(months):
        return None

    month_name = months[month_idx - 1].get('name', '')

    # Search holidays for matching date
    holidays = config.calendar_data.get('holidays', [])
    for holiday in holidays:
        if holiday.get('month') == month_name and holiday.get('day') == day:
            return holiday

    return None


# ============================================================================
# MOON PHASE UTILITY FUNCTIONS
# ============================================================================

# Moon phases in order (index 0-7)
MOON_PHASES = [
    {"name": "New Moon", "icon": "🌑"},
    {"name": "Waxing Crescent", "icon": "🌒"},
    {"name": "First Quarter", "icon": "🌓"},
    {"name": "Waxing Gibbous", "icon": "🌔"},
    {"name": "Full Moon", "icon": "🌕"},
    {"name": "Waning Gibbous", "icon": "🌖"},
    {"name": "Last Quarter", "icon": "🌗"},
    {"name": "Waning Crescent", "icon": "🌘"},
]

FULL_MOON_PHASE_INDEX = 4  # Index of Full Moon in MOON_PHASES


def get_moon_phase_for_day(lunar_day: int, cycle_length: int) -> Dict:
    """
    Get moon phase info for a specific lunar day.

    Args:
        lunar_day: Current day in lunar cycle (1 to cycle_length)
        cycle_length: Total days in lunar cycle

    Returns:
        Dict with keys: name, icon, phase_index, is_full_moon

    Example:
        phase = get_moon_phase_for_day(14, 27)
        # Returns: {"name": "Full Moon", "icon": "🌕", "phase_index": 4, "is_full_moon": True}
    """
    if lunar_day < 1:
        lunar_day = 1
    if lunar_day > cycle_length:
        lunar_day = cycle_length

    # Calculate which phase (0-7) based on position in cycle
    # Each phase spans cycle_length / 8 days
    days_per_phase = cycle_length / 8.0
    phase_index = int((lunar_day - 1) / days_per_phase)

    # Clamp to valid range
    if phase_index > 7:
        phase_index = 7

    phase = MOON_PHASES[phase_index]
    return {
        "name": phase["name"],
        "icon": phase["icon"],
        "phase_index": phase_index,
        "is_full_moon": phase_index == FULL_MOON_PHASE_INDEX
    }


def get_moon_phase_info() -> Optional[Dict]:
    """
    Get the current moon phase info from calendar data.

    Returns:
        - Dict with keys: name, icon, phase_index, is_full_moon, is_blood_moon, lunar_day
        - None if no calendar loaded or no lunar data

    Example:
        phase = get_moon_phase_info()
        if phase:
            print(f"{phase['icon']} {phase['name']}")
    """
    import config  # Lazy import to avoid circular dependency

    # No calendar loaded
    if not config.calendar_data:
        return None

    # Get lunar data
    lunar_day = config.calendar_data.get('lunar_day')
    cycle_length = config.calendar_data.get('lunar_cycle_length', 27)

    # No lunar day set
    if lunar_day is None:
        return None

    # Get phase info
    phase_info = get_moon_phase_for_day(lunar_day, cycle_length)

    # Add blood moon status
    is_blood_moon = config.calendar_data.get('is_blood_moon', False)
    phase_info['is_blood_moon'] = is_blood_moon and phase_info['is_full_moon']
    phase_info['lunar_day'] = lunar_day

    # Override name if blood moon
    if phase_info['is_blood_moon']:
        phase_info['name'] = "Blood Moon"

    return phase_info


def get_phase_start_day(phase_index: int, cycle_length: int) -> int:
    """
    Get the starting lunar day for a given phase.

    Args:
        phase_index: Phase index (0-7)
        cycle_length: Total days in lunar cycle

    Returns:
        Starting lunar day for that phase (1-based)
    """
    days_per_phase = cycle_length / 8.0
    return math.ceil(phase_index * days_per_phase) + 1


def advance_lunar_day(days: int = 1) -> bool:
    """
    Advance the lunar day by the specified number of days.

    Handles cycle overflow (wraps to day 1 when reaching cycle_length).
    Checks for blood moon when entering full moon phase.
    Saves the new lunar day to the calendar file.

    Args:
        days: Number of days to advance (default 1)

    Returns:
        True if successful, False if no calendar or save failed

    Example:
        success = advance_lunar_day(1)
    """
    import config  # Lazy import to avoid circular dependency
    from data_loader import save_lunar_data

    # No calendar loaded
    if not config.calendar_data:
        return False

    # Get current lunar data
    lunar_day = config.calendar_data.get('lunar_day')
    cycle_length = config.calendar_data.get('lunar_cycle_length', 27)
    blood_moon_chance = config.calendar_data.get('blood_moon_chance', 10)
    is_blood_moon = config.calendar_data.get('is_blood_moon', False)

    # If lunar_day not set, initialize it
    if lunar_day is None:
        lunar_day = random.randint(1, cycle_length)

    # Get phase before advancing
    old_phase = get_moon_phase_for_day(lunar_day, cycle_length)

    # Advance lunar day
    lunar_day += days

    # Handle cycle overflow
    while lunar_day > cycle_length:
        lunar_day -= cycle_length

    # Get phase after advancing
    new_phase = get_moon_phase_for_day(lunar_day, cycle_length)

    # Check if we entered full moon phase
    if new_phase['is_full_moon'] and not old_phase['is_full_moon']:
        # Roll for blood moon
        roll = random.randint(1, 100)
        is_blood_moon = roll <= blood_moon_chance
        verbose_print(f"Entering Full Moon phase. Blood moon roll: {roll} <= {blood_moon_chance}? {is_blood_moon}")
    elif not new_phase['is_full_moon']:
        # Clear blood moon status when leaving full moon
        is_blood_moon = False

    # Save lunar data
    return save_lunar_data(lunar_day, is_blood_moon)


def set_lunar_day_to_phase(phase_index: int) -> bool:
    """
    Set the lunar day to the start of a specific phase.

    Args:
        phase_index: Phase index (0-7)

    Returns:
        True if successful, False if no calendar or save failed

    Example:
        # Set to Full Moon (phase index 4)
        success = set_lunar_day_to_phase(4)
    """
    import config  # Lazy import to avoid circular dependency
    from data_loader import save_lunar_data

    # No calendar loaded
    if not config.calendar_data:
        return False

    # Validate phase index
    if phase_index < 0 or phase_index > 7:
        return False

    cycle_length = config.calendar_data.get('lunar_cycle_length', 27)
    blood_moon_chance = config.calendar_data.get('blood_moon_chance', 10)

    # Calculate starting day for this phase
    lunar_day = get_phase_start_day(phase_index, cycle_length)

    # Check if setting to full moon - roll for blood moon
    is_blood_moon = False
    if phase_index == FULL_MOON_PHASE_INDEX:
        roll = random.randint(1, 100)
        is_blood_moon = roll <= blood_moon_chance
        verbose_print(f"Setting to Full Moon. Blood moon roll: {roll} <= {blood_moon_chance}? {is_blood_moon}")

    # Save lunar data
    return save_lunar_data(lunar_day, is_blood_moon)


def adjust_lunar_day(delta: int) -> bool:
    """
    Adjust the lunar day by a delta (positive or negative).

    Handles wrapping at cycle boundaries.

    Args:
        delta: Amount to adjust (+1 or -1 typically)

    Returns:
        True if successful, False if no calendar or save failed

    Example:
        adjust_lunar_day(1)   # Advance by 1
        adjust_lunar_day(-1)  # Go back by 1
    """
    import config  # Lazy import to avoid circular dependency
    from data_loader import save_lunar_data

    # No calendar loaded
    if not config.calendar_data:
        return False

    # Get current lunar data
    lunar_day = config.calendar_data.get('lunar_day')
    cycle_length = config.calendar_data.get('lunar_cycle_length', 27)
    blood_moon_chance = config.calendar_data.get('blood_moon_chance', 10)
    is_blood_moon = config.calendar_data.get('is_blood_moon', False)

    # If lunar_day not set, initialize to 1
    if lunar_day is None:
        lunar_day = 1

    # Get phase before adjusting
    old_phase = get_moon_phase_for_day(lunar_day, cycle_length)

    # Adjust lunar day
    lunar_day += delta

    # Handle wrapping
    if lunar_day < 1:
        lunar_day = cycle_length + lunar_day  # Wrap backwards
    elif lunar_day > cycle_length:
        lunar_day = lunar_day - cycle_length  # Wrap forwards

    # Get phase after adjusting
    new_phase = get_moon_phase_for_day(lunar_day, cycle_length)

    # Check if we entered full moon phase
    if new_phase['is_full_moon'] and not old_phase['is_full_moon']:
        # Roll for blood moon
        roll = random.randint(1, 100)
        is_blood_moon = roll <= blood_moon_chance
        verbose_print(f"Entering Full Moon phase. Blood moon roll: {roll} <= {blood_moon_chance}? {is_blood_moon}")
    elif not new_phase['is_full_moon']:
        # Clear blood moon status when leaving full moon
        is_blood_moon = False

    # Save lunar data
    return save_lunar_data(lunar_day, is_blood_moon)


def initialize_lunar_day() -> bool:
    """
    Initialize lunar day to a random value if not already set.

    Returns:
        True if initialized or already set, False if no calendar or save failed

    Example:
        initialize_lunar_day()  # Sets random lunar day if null
    """
    import config  # Lazy import to avoid circular dependency
    from data_loader import save_lunar_data

    # No calendar loaded
    if not config.calendar_data:
        return False

    # Check if already set
    lunar_day = config.calendar_data.get('lunar_day')
    if lunar_day is not None:
        return True  # Already initialized

    # Randomize lunar day
    cycle_length = config.calendar_data.get('lunar_cycle_length', 27)
    blood_moon_chance = config.calendar_data.get('blood_moon_chance', 10)

    lunar_day = random.randint(1, cycle_length)

    # Check if we landed on full moon - roll for blood moon
    phase = get_moon_phase_for_day(lunar_day, cycle_length)
    is_blood_moon = False
    if phase['is_full_moon']:
        roll = random.randint(1, 100)
        is_blood_moon = roll <= blood_moon_chance
        verbose_print(f"Initialized to Full Moon. Blood moon roll: {roll} <= {blood_moon_chance}? {is_blood_moon}")

    verbose_print(f"Initialized lunar day to {lunar_day} ({phase['name']})")

    # Save lunar data
    return save_lunar_data(lunar_day, is_blood_moon)
