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

Classes: None
"""

from typing import Dict, Optional
import random

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
