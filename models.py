"""
models.py - Data classes for Torchcrawl GM Control Panel

Classes:
- Encounter: Represents a single encounter occurrence with name, time, sparks, description, and habitat
- Weather: Represents weather conditions with name and effects list
- Timer: Represents a countdown timer with name and remaining duration

Functions: None
"""

from typing import Optional, List, Dict
import random
import xarray as xr


class Encounter:
    """Represents a single encounter occurrence."""
    
    def __init__(self) -> None:
        """Initialize an empty encounter (represents 'no encounter')."""
        self.name: Optional[str] = None
        self.time: Optional[str] = None
        self.sparks: List[str] = []
        self.description: Optional[str] = None
        self.habitat: Optional[str] = None
    
    def generate_overland_encounter(
        self,
        zone: str,
        overlay: Optional[str],
        watch: str,
        encounters_data: Dict,
        encounter_by_zone_and_watch: xr.DataArray,
        zones_data: Dict
    ) -> None:
        """
        Generate an overland encounter for a specific watch period.
        
        Algorithm:
        1. Determine active zone (50% chance overlay if provided)
        2. Get encounter_chance for active zone
        3. Roll to see if encounter occurs
        4. If encounter occurs, select based on weighted probabilities
        5. Populate encounter details
        
        Args:
            zone: Base overland zone
            overlay: Overlay zone or None
            watch: Time of day watch period
            encounters_data: Dictionary of encounter details
            encounter_by_zone_and_watch: 3D xarray [Encounter, Zone, Watch]
            zones_data: Dictionary of zone information
        """
        from utils import weighted_random_choice, parse_percentage, verbose_print
        from logger import log_info
        
        # Step 1: Determine active zone (50/50 if overlay present)
        active_zone = zone
        if overlay is not None:
            if random.random() < 0.5:
                active_zone = overlay
                verbose_print(f"  Using overlay zone: {overlay}")
            else:
                verbose_print(f"  Using base zone: {zone}")
        
        # Step 2: Get encounter chance
        encounter_chance = parse_percentage(zones_data[active_zone]['encounter_chance'])
        
        # Step 3: Roll for encounter
        roll = random.random()
        verbose_print(f"  Encounter roll: {roll:.2f} vs threshold {encounter_chance:.2f}")
        
        if roll > encounter_chance:
            # No encounter
            self.name = None
            self.time = None
            self.sparks = []
            self.description = None
            self.habitat = None
            log_info(f"{watch} encounter: No encounter (rolled {roll:.2f} > {encounter_chance:.2f})")
            verbose_print(f"  Result: No encounter")
            return
        
        # Step 4-5: Select and populate encounter
        try:
            # Get weights for this zone and watch
            weights = {}
            for encounter_name in encounter_by_zone_and_watch.coords['Encounter'].values:
                weight = float(encounter_by_zone_and_watch.loc[encounter_name, active_zone, watch])
                if weight > 0:
                    weights[encounter_name] = weight
            
            if not weights:
                # No valid encounters for this zone/watch
                self.name = None
                self.time = None
                self.sparks = []
                self.description = None
                self.habitat = None
                log_info(f"{watch} encounter: No valid encounters for {active_zone}/{watch}")
                return
            
            # Select encounter
            selected_encounter = weighted_random_choice(weights)
            
            # Populate encounter details
            encounter_details = encounters_data[selected_encounter]
            self.name = selected_encounter
            self.time = watch
            self.sparks = encounter_details['sparks']  # ALL sparks
            self.description = encounter_details['description']
            self.habitat = encounter_details['habitat']
            
            log_info(f"{watch} encounter: {selected_encounter} (zone: {active_zone}, weight: {weights[selected_encounter]:.2f})")
            verbose_print(f"  Result: {selected_encounter}")
            
        except Exception as e:
            log_info(f"Error generating overland encounter: {e}")
            verbose_print(f"  Error: {e}")
            # Set to no encounter on error
            self.name = None
            self.time = None
            self.sparks = []
            self.description = None
            self.habitat = None
    
    def generate_site_encounter(
        self,
        zone: str,
        time_slot: str,
        encounters_data: Dict,
        encounter_by_zone: xr.DataArray,
        zones_data: Dict
    ) -> None:
        """
        Generate a site-based encounter for a specific time slot.
        
        Algorithm:
        1. Get encounter_chance for zone
        2. Roll to see if encounter occurs
        3. If encounter occurs, select based on zone weights (no watch modifier)
        4. Populate encounter details
        
        Args:
            zone: Site zone
            time_slot: Time slot label
            encounters_data: Dictionary of encounter details
            encounter_by_zone: 2D xarray [Encounter, Zone]
            zones_data: Dictionary of zone information
        """
        from utils import weighted_random_choice, parse_percentage, verbose_print
        from logger import log_info
        
        # Step 1: Get encounter chance
        encounter_chance = parse_percentage(zones_data[zone]['encounter_chance'])
        
        # Step 2: Roll for encounter
        roll = random.random()
        verbose_print(f"  Encounter roll for {time_slot}: {roll:.2f} vs threshold {encounter_chance:.2f}")
        
        if roll > encounter_chance:
            # No encounter
            self.name = None
            self.time = None
            self.sparks = []
            self.description = None
            self.habitat = None
            log_info(f"{time_slot} encounter: No encounter (rolled {roll:.2f} > {encounter_chance:.2f})")
            verbose_print(f"  Result: No encounter")
            return
        
        # Step 3-4: Select and populate encounter
        try:
            # Get weights for this zone (no watch modifier for site encounters)
            weights = {}
            for encounter_name in encounter_by_zone.coords['Encounter'].values:
                weight = float(encounter_by_zone.loc[encounter_name, zone])
                if weight > 0:
                    weights[encounter_name] = weight
            
            if not weights:
                # No valid encounters for this zone
                self.name = None
                self.time = None
                self.sparks = []
                self.description = None
                self.habitat = None
                log_info(f"{time_slot} encounter: No valid encounters for {zone}")
                return
            
            # Select encounter
            selected_encounter = weighted_random_choice(weights)
            
            # Populate encounter details
            encounter_details = encounters_data[selected_encounter]
            self.name = selected_encounter
            self.time = time_slot
            self.sparks = encounter_details['sparks']  # ALL sparks
            self.description = encounter_details['description']
            self.habitat = encounter_details['habitat']
            
            log_info(f"{time_slot} encounter: {selected_encounter} (zone: {zone}, weight: {weights[selected_encounter]:.2f})")
            verbose_print(f"  Result: {selected_encounter}")
            
        except Exception as e:
            log_info(f"Error generating site encounter: {e}")
            verbose_print(f"  Error: {e}")
            # Set to no encounter on error
            self.name = None
            self.time = None
            self.sparks = []
            self.description = None
            self.habitat = None
    
    def is_encounter(self) -> bool:
        """
        Check if this represents an actual encounter or 'no encounter'.
        
        Returns:
            True if an encounter was generated (name is not None), False otherwise
        """
        return self.name is not None
    
    def __str__(self) -> str:
        """String representation for display."""
        if not self.is_encounter():
            return "No Encounter"
        return f"{self.name} at {self.time}"


class Weather:
    """Represents weather conditions for a day."""
    
    def __init__(self) -> None:
        """Initialize empty weather."""
        self.name: Optional[str] = None
        self.effects: List[str] = []
    
    def generate_weather(
        self,
        season: str,
        previous_weather: Optional['Weather'],
        weather_by_season: xr.DataArray,
        weathers_data: Dict
    ) -> None:
        """
        Generate weather for the current day.
        
        Algorithm:
        1. Get probability weights for season
        2. Roll weighted random selection
        3. Handle "No Change" (re-roll on Day 1, keep previous otherwise)
        4. Look up weather details and populate
        
        Args:
            season: Current season
            previous_weather: Weather object from previous day, or None for Day 1
            weather_by_season: 2D xarray [Weather, Season]
            weathers_data: Dictionary of weather details
        """
        from utils import weighted_random_choice, verbose_print
        from logger import log_info
        
        max_attempts = 100  # Prevent infinite loop
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            
            # Step 1-2: Get weights and select weather
            weights = {}
            for weather_name in weather_by_season.coords['Weather'].values:
                weight = float(weather_by_season.loc[weather_name, season])
                if weight > 0:
                    weights[weather_name] = weight
            
            if not weights:
                log_info(f"No valid weather types for season {season}")
                self.name = "Clear"
                self.effects = []
                return
            
            selected_weather = weighted_random_choice(weights)
            
            # Step 3: Handle "No Change"
            if selected_weather == "No Change":
                if previous_weather is None:
                    # Day 1: Re-roll until we get actual weather
                    verbose_print(f"  Weather roll attempt {attempt}: 'No Change' on Day 1, re-rolling...")
                    continue
                else:
                    # Keep previous weather
                    self.name = previous_weather.name
                    self.effects = previous_weather.effects
                    log_info(f"Weather: No Change (keeping {self.name})")
                    verbose_print(f"  Weather: No Change (keeping {self.name})")
                    return
            
            # Step 4: Look up and populate weather details
            weather_info = weathers_data.get(selected_weather, {'effects': []})
            self.name = selected_weather
            self.effects = weather_info['effects']
            
            log_info(f"Weather: {self.name} (effects: {', '.join(self.effects) if self.effects else 'none'})")
            verbose_print(f"  Weather: {self.name}")
            if self.effects:
                verbose_print(f"    Effects: {', '.join(self.effects)}")
            return
        
        # Fallback if we somehow hit max attempts
        log_info(f"Weather generation hit max attempts, defaulting to Clear")
        self.name = "Clear"
        self.effects = []
    
    def __str__(self) -> str:
        """String representation for display."""
        if self.name is None:
            return "No weather generated"
        if not self.effects:
            return self.name
        return f"{self.name} ({', '.join(self.effects)})"


class Timer:
    """Represents a countdown timer in Site Mode."""
    
    def __init__(self, name: str = "", remaining_duration: int = 60) -> None:
        """
        Initialize a timer.
        
        Args:
            name: Description of what the timer tracks
            remaining_duration: Starting duration in minutes (default 60)
        """
        self.name: str = name
        self.remaining_duration: int = remaining_duration  # Allow negative values
    
    def decrement_timer(self, amount: int = 10) -> str:
        """
        Decrease timer by specified amount.
        
        Args:
            amount: Minutes to subtract (default 10 for standard turn)
        
        Returns:
            "active" if remaining_duration >= 0
            "expired" if remaining_duration < 0
        """
        from logger import log_info
        from utils import verbose_print
        
        self.remaining_duration -= amount  # Allow going negative
        
        if self.remaining_duration >= 0:
            verbose_print(f"  Timer '{self.name}': {self.remaining_duration} minutes remaining")
            return "active"
        else:
            log_info(f"Timer expired: {self.name}")
            verbose_print(f"  Timer '{self.name}': EXPIRED (negative)")
            return "expired"
    
    def is_expired(self) -> bool:
        """Check if timer has gone negative (< 0)."""
        return self.remaining_duration < 0
    
    def __str__(self) -> str:
        """String representation for display."""
        if self.is_expired():
            return f"⚠️ EXPIRED: {self.name}"
        elif 0 <= self.remaining_duration < 10:
            return f"Current: {self.name}"
        else:
            return f"{self.remaining_duration} minutes: {self.name}"
