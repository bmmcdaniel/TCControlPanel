"""
Tests for seasons file, watches file, and 4D encounter array features.

Verifies:
- Seasons file loading (seasons_list, seasons_data, encounter_modification)
- Watches file loading (watches_list, watches_key_list, dynamic replacement of OVERLAND_WATCHES)
- Encounters YAML season key parsing (dict, "All 100%", {All: 100%}, missing)
- 4D encounter array construction and dimensions
- Season encounter_modification applied to encounter_chance
- Per-encounter season percentages (Winter: 0% exclusion, weighted selection)
- Overland logic uses watches_list and passes season params
- Site mode unchanged (no season modification)
- Data validation catches mismatches
"""

import random
from unittest.mock import patch
import config
from data_loader import (
    load_all_data, load_seasons_file, load_watches_file,
    load_encounters_file, generate_encounter_by_zone_watch_and_season,
    validate_data
)
from models import Encounter
from utils import parse_percentage


# ============================================================================
# FIXTURE: Load all data once for tests that need real data
# ============================================================================

def _ensure_data_loaded():
    """Load all data if not already loaded."""
    if config.encounter_by_zone_watch_and_season is None:
        assert load_all_data(), "load_all_data() must succeed"


# ============================================================================
# 1. SEASONS FILE LOADING
# ============================================================================

class TestSeasonsFile:
    """Tests for load_seasons_file() and seasons data."""

    def test_seasons_list_populated(self):
        _ensure_data_loaded()
        assert config.seasons_list == ['Spring', 'Summer', 'Autumn', 'Winter']

    def test_seasons_data_populated(self):
        _ensure_data_loaded()
        assert len(config.seasons_data) == 4
        for season in ['Spring', 'Summer', 'Autumn', 'Winter']:
            assert season in config.seasons_data

    def test_encounter_modification_values(self):
        _ensure_data_loaded()
        assert config.seasons_data['Spring']['encounter_modification'] == '85%'
        assert config.seasons_data['Summer']['encounter_modification'] == '100%'
        assert config.seasons_data['Autumn']['encounter_modification'] == '85%'
        assert config.seasons_data['Winter']['encounter_modification'] == '40%'

    def test_encounter_modification_parseable(self):
        """All encounter_modification values must parse to valid floats."""
        _ensure_data_loaded()
        for season, data in config.seasons_data.items():
            pct = parse_percentage(data['encounter_modification'])
            assert 0.0 <= pct <= 1.0, f"{season} encounter_modification out of range: {pct}"

    def test_seasons_not_from_excel(self):
        """Seasons must come from YAML, not Excel headers."""
        _ensure_data_loaded()
        # Seasons should be loaded before weather Excel in load_all_data
        # Verify seasons_list has the YAML values
        assert 'Spring' in config.seasons_list
        assert 'Winter' in config.seasons_list


# ============================================================================
# 2. WATCHES FILE LOADING
# ============================================================================

class TestWatchesFile:
    """Tests for load_watches_file() and dynamic watch lists."""

    def test_watches_list_populated(self):
        _ensure_data_loaded()
        expected = ['Dawn', 'Morning', 'Afternoon', 'Dusk', 'Early Night', 'Late Night']
        assert config.watches_list == expected

    def test_watches_key_list_lowercase(self):
        _ensure_data_loaded()
        expected = ['dawn', 'morning', 'afternoon', 'dusk', 'early night', 'late night']
        assert config.watches_key_list == expected

    def test_watches_key_list_matches_watches_list(self):
        _ensure_data_loaded()
        assert len(config.watches_list) == len(config.watches_key_list)
        for display, key in zip(config.watches_list, config.watches_key_list):
            assert key == display.lower()

    def test_no_hardcoded_overland_watches(self):
        """OVERLAND_WATCHES constant should no longer exist in config."""
        assert not hasattr(config, 'OVERLAND_WATCHES'), \
            "config.OVERLAND_WATCHES should be removed"

    def test_watches_list_has_six_entries(self):
        _ensure_data_loaded()
        assert len(config.watches_list) == 6


# ============================================================================
# 3. ENCOUNTERS YAML SEASON PARSING
# ============================================================================

class TestEncounterSeasonParsing:
    """Tests for season key parsing in load_encounters_file()."""

    def test_dict_format_parsed(self):
        """Season dict like {Spring: 100%, Summer: 80%} should parse correctly."""
        _ensure_data_loaded()
        # Air Elemental has {Spring: 100%, Summer: 80%, Autumn: 100%, Winter: 80%}
        season = config.encounters_data['Air Elemental']['season']
        assert isinstance(season, dict)
        assert season['Spring'] == 1.0
        assert season['Summer'] == 0.8
        assert season['Autumn'] == 1.0
        assert season['Winter'] == 0.8

    def test_all_string_format_parsed(self):
        """Season 'All 100%' should expand to all seasons at 100%."""
        _ensure_data_loaded()
        # Atacorn has "All 100%"
        season = config.encounters_data['Atacorn']['season']
        assert isinstance(season, dict)
        for s in config.seasons_list:
            assert season[s] == 1.0, f"Atacorn should be 100% in {s}"

    def test_all_dict_format_parsed(self):
        """Season {All: 100%} should expand to all seasons at 100%."""
        _ensure_data_loaded()
        # Weathervane Effigy has {All: 100%}
        season = config.encounters_data['Weathervane Effigy']['season']
        assert isinstance(season, dict)
        for s in config.seasons_list:
            assert season[s] == 1.0, f"Weathervane Effigy should be 100% in {s}"

    def test_winter_zero_percent(self):
        """Ankheg has Winter: 0% - should parse to 0.0."""
        _ensure_data_loaded()
        season = config.encounters_data['Ankheg']['season']
        assert season['Winter'] == 0.0

    def test_season_dict_has_all_seasons(self):
        """Dict-format seasons should have entries for all seasons in seasons_list."""
        _ensure_data_loaded()
        season = config.encounters_data['Ankheg']['season']
        for s in config.seasons_list:
            assert s in season, f"Missing season '{s}' in Ankheg season dict"

    def test_season_stored_as_dict_not_string(self):
        """Season field in encounters_data should always be a dict, never a string."""
        _ensure_data_loaded()
        for name, data in config.encounters_data.items():
            assert isinstance(data['season'], dict), \
                f"Encounter '{name}' season should be dict, got {type(data['season'])}"


# ============================================================================
# 4. 4D ENCOUNTER ARRAY
# ============================================================================

class TestFourDimensionalArray:
    """Tests for the 4D encounter array."""

    def test_array_exists(self):
        _ensure_data_loaded()
        assert config.encounter_by_zone_watch_and_season is not None

    def test_array_has_four_dimensions(self):
        _ensure_data_loaded()
        assert len(config.encounter_by_zone_watch_and_season.dims) == 4

    def test_array_dimension_names(self):
        _ensure_data_loaded()
        dims = config.encounter_by_zone_watch_and_season.dims
        assert dims == ('Encounter', 'Zone', 'Watch', 'Season')

    def test_array_encounter_dimension_from_yaml(self):
        """Encounter dimension should come from encounters YAML, not Excel."""
        _ensure_data_loaded()
        array_encounters = list(config.encounter_by_zone_watch_and_season.coords['Encounter'].values)
        yaml_encounters = list(config.encounters_data.keys())
        assert array_encounters == yaml_encounters

    def test_array_watch_dimension_from_watches_file(self):
        _ensure_data_loaded()
        array_watches = list(config.encounter_by_zone_watch_and_season.coords['Watch'].values)
        assert array_watches == config.watches_list

    def test_array_season_dimension_from_seasons_file(self):
        _ensure_data_loaded()
        array_seasons = list(config.encounter_by_zone_watch_and_season.coords['Season'].values)
        assert array_seasons == config.seasons_list

    def test_array_shape(self):
        """Shape should be (N_encounters, N_zones, 6_watches, 4_seasons)."""
        _ensure_data_loaded()
        shape = config.encounter_by_zone_watch_and_season.shape
        assert shape[0] == len(config.encounters_data)  # encounters from YAML
        assert shape[2] == 6  # watches
        assert shape[3] == 4  # seasons

    def test_ankheg_winter_weight_zero(self):
        """Ankheg with Winter: 0% should have weight 0 in all zones/watches for Winter."""
        _ensure_data_loaded()
        arr = config.encounter_by_zone_watch_and_season
        for zone in arr.coords['Zone'].values:
            for watch in arr.coords['Watch'].values:
                weight = float(arr.loc['Ankheg', zone, watch, 'Winter'])
                assert weight == 0.0, \
                    f"Ankheg should have 0 weight in Winter for {zone}/{watch}, got {weight}"

    def test_weight_formula(self):
        """Verify weight = zone_weight * watch_pct * season_pct for a known encounter."""
        _ensure_data_loaded()
        # Use Aurochs in Meadows/Morning/Summer as test case
        # Aurochs: watch morning=15%, season Summer=100%
        zone_weight = float(config.encounter_by_zone.loc['Aurochs', 'Meadows'])
        watch_pct = parse_percentage(config.encounters_data['Aurochs']['watch'].get('morning', '0%'))
        season_pct = config.encounters_data['Aurochs']['season']['Summer']
        expected = zone_weight * watch_pct * season_pct

        actual = float(config.encounter_by_zone_watch_and_season.loc['Aurochs', 'Meadows', 'Morning', 'Summer'])
        assert abs(actual - expected) < 1e-10, f"Expected {expected}, got {actual}"

    def test_encounter_in_yaml_not_excel_gets_zero(self):
        """Encounters in YAML but not in Excel zone weights should have weight 0."""
        _ensure_data_loaded()
        excel_encounters = set(config.encounter_by_zone.coords['Encounter'].values)
        yaml_encounters = set(config.encounters_data.keys())
        yaml_only = yaml_encounters - excel_encounters

        if yaml_only:
            test_enc = list(yaml_only)[0]
            arr = config.encounter_by_zone_watch_and_season
            for zone in arr.coords['Zone'].values:
                for watch in arr.coords['Watch'].values:
                    for season in arr.coords['Season'].values:
                        weight = float(arr.loc[test_enc, zone, watch, season])
                        assert weight == 0.0, \
                            f"'{test_enc}' (YAML-only) should have 0 weight, got {weight}"

    def test_old_3d_array_removed(self):
        """The old encounter_by_zone_and_watch variable should not exist."""
        assert not hasattr(config, 'encounter_by_zone_and_watch'), \
            "config.encounter_by_zone_and_watch should be removed (renamed to 4D)"


# ============================================================================
# 5. SEASON ENCOUNTER MODIFICATION
# ============================================================================

class TestSeasonEncounterModification:
    """Tests for encounter_modification applied to encounter_chance."""

    def test_summer_100_percent_no_change(self):
        """Summer at 100% should not modify encounter_chance."""
        _ensure_data_loaded()
        zone_chance = parse_percentage(config.zones_data['Mountains']['encounter_chance'])
        season_mod = parse_percentage(config.seasons_data['Summer']['encounter_modification'])
        effective = zone_chance * season_mod
        assert effective == zone_chance

    def test_winter_40_percent_reduces_chance(self):
        """Winter at 40% should reduce encounter_chance to 40% of base."""
        _ensure_data_loaded()
        zone_chance = parse_percentage(config.zones_data['Mountains']['encounter_chance'])
        season_mod = parse_percentage(config.seasons_data['Winter']['encounter_modification'])
        effective = zone_chance * season_mod
        expected = zone_chance * 0.4
        assert abs(effective - expected) < 1e-10

    def test_mountains_winter_7_2_percent(self):
        """Mountains (18%) in Winter (40%) should give ~7.2% effective chance."""
        _ensure_data_loaded()
        zone_chance = parse_percentage(config.zones_data['Mountains']['encounter_chance'])
        season_mod = parse_percentage(config.seasons_data['Winter']['encounter_modification'])
        effective = zone_chance * season_mod
        assert abs(effective - 0.072) < 1e-10, f"Expected 0.072, got {effective}"

    def test_encounter_modification_applied_in_generate(self):
        """generate_overland_encounter should use season-modified encounter_chance."""
        _ensure_data_loaded()

        # With random.random() returning 0.075 (above 7.2%), Winter Mountains
        # should produce no encounter
        enc = Encounter()
        with patch('random.random', return_value=0.075):
            enc.generate_overland_encounter(
                zone='Mountains',
                overlay=None,
                watch='Morning',
                season='Winter',
                encounters_data=config.encounters_data,
                encounter_by_zone_watch_and_season=config.encounter_by_zone_watch_and_season,
                zones_data=config.zones_data,
                seasons_data=config.seasons_data
            )
        assert enc.name is None, "Roll 0.075 > 0.072 should produce no encounter in Winter Mountains"

    def test_encounter_modification_summer_allows_encounter(self):
        """Summer 100% on Mountains 18%: roll 0.05 should allow encounter."""
        _ensure_data_loaded()

        enc = Encounter()
        with patch('random.random', return_value=0.05):
            enc.generate_overland_encounter(
                zone='Mountains',
                overlay=None,
                watch='Morning',
                season='Summer',
                encounters_data=config.encounters_data,
                encounter_by_zone_watch_and_season=config.encounter_by_zone_watch_and_season,
                zones_data=config.zones_data,
                seasons_data=config.seasons_data
            )
        # 0.05 <= 0.18 so encounter should occur (if there are valid encounters)
        # Mountains should have at least one encounter with weight > 0 in Morning/Summer
        arr = config.encounter_by_zone_watch_and_season
        has_encounters = any(
            float(arr.loc[e, 'Mountains', 'Morning', 'Summer']) > 0
            for e in arr.coords['Encounter'].values
        )
        if has_encounters:
            assert enc.name is not None, "Roll 0.05 <= 0.18 should produce encounter in Summer Mountains"


# ============================================================================
# 6. WINTER ANKHEG EXCLUSION
# ============================================================================

class TestWinterAnkhegExclusion:
    """Ankheg (Winter: 0%) should never appear in Winter."""

    def test_ankheg_never_selected_in_winter(self):
        """Run many encounter generations in Winter Meadows; Ankheg must never appear."""
        _ensure_data_loaded()

        # Use Meadows since Ankheg lives there
        for _ in range(200):
            enc = Encounter()
            enc.generate_overland_encounter(
                zone='Meadows',
                overlay=None,
                watch='Morning',
                season='Winter',
                encounters_data=config.encounters_data,
                encounter_by_zone_watch_and_season=config.encounter_by_zone_watch_and_season,
                zones_data=config.zones_data,
                seasons_data=config.seasons_data
            )
            assert enc.name != 'Ankheg', "Ankheg must never appear in Winter (Winter: 0%)"


# ============================================================================
# 7. OVERLAND LOGIC INTEGRATION
# ============================================================================

class TestOverlandLogicIntegration:
    """Tests that overland_logic.py correctly uses watches_list and season params."""

    def test_overland_encounters_use_watches_list(self):
        """generate_overland_encounters should use config.watches_list."""
        _ensure_data_loaded()
        from overland_logic import generate_overland_encounters

        config.selected_overland_zone = config.overland_zones_list[0]
        config.selected_overland_season = 'Summer'
        encounters = generate_overland_encounters()

        # Keys should be the watch names from watches_list
        assert set(encounters.keys()) == set(config.watches_list)

    def test_overland_new_day_generates_all_watches(self):
        """overland_new_day should generate encounters for all watches."""
        _ensure_data_loaded()
        from overland_logic import overland_new_day

        config.selected_overland_zone = config.overland_zones_list[0]
        config.selected_overland_season = 'Summer'
        overland_new_day()

        assert len(config.generated_overland_encounters) == len(config.watches_list)
        for watch in config.watches_list:
            assert watch in config.generated_overland_encounters

    def test_regenerate_individual_encounter(self):
        """regenerate_individual_overland_encounter should work with season params."""
        _ensure_data_loaded()
        from overland_logic import regenerate_individual_overland_encounter

        config.selected_overland_zone = config.overland_zones_list[0]
        config.selected_overland_season = 'Summer'

        enc = regenerate_individual_overland_encounter('Dawn')
        assert isinstance(enc, Encounter)
        assert config.generated_overland_encounters.get('Dawn') is enc


# ============================================================================
# 8. SITE MODE UNCHANGED
# ============================================================================

class TestSiteModeUnchanged:
    """Site mode should not be affected by season changes."""

    def test_site_encounter_no_season_param(self):
        """Site encounter generation should not require season."""
        _ensure_data_loaded()
        enc = Encounter()
        # generate_site_encounter should still work without season
        enc.generate_site_encounter(
            zone=config.site_zones_list[0] if config.site_zones_list else config.overland_zones_list[0],
            time_slot='Current',
            encounters_data=config.encounters_data,
            encounter_by_zone=config.encounter_by_zone,
            zones_data=config.zones_data
        )
        # Should complete without error - either encounter or no encounter


# ============================================================================
# 9. DATA VALIDATION
# ============================================================================

class TestDataValidation:
    """Tests for validate_data() catching issues."""

    def test_validation_runs_without_crash(self):
        _ensure_data_loaded()
        errors = validate_data()
        assert isinstance(errors, list)

    def test_no_season_key_errors(self):
        """No encounter should have invalid season keys after parsing."""
        _ensure_data_loaded()
        errors = validate_data()
        season_errors = [e for e in errors if "Season" in e and "encounter" in e.lower()]
        assert len(season_errors) == 0, f"Season validation errors: {season_errors}"

    def test_no_watch_key_errors(self):
        """No encounter should have invalid watch keys."""
        _ensure_data_loaded()
        errors = validate_data()
        watch_errors = [e for e in errors if "Watch" in e]
        assert len(watch_errors) == 0, f"Watch validation errors: {watch_errors}"

    def test_rest_dc_seasons_valid(self):
        """Rest DC season keys should match seasons_list."""
        _ensure_data_loaded()
        errors = validate_data()
        rest_errors = [e for e in errors if "rest_DCs" in e]
        assert len(rest_errors) == 0, f"Rest DC season errors: {rest_errors}"


# ============================================================================
# 10. LOAD SEQUENCE ORDER
# ============================================================================

class TestLoadSequence:
    """Tests that data loading happens in correct order."""

    def test_full_load_succeeds(self):
        """load_all_data() should return True."""
        # Reset state
        config.encounter_by_zone_watch_and_season = None
        config.seasons_list = []
        config.watches_list = []

        success = load_all_data()
        assert success is True

    def test_seasons_loaded_before_encounters(self):
        """After load, encounters should reference seasons from seasons_list."""
        _ensure_data_loaded()
        # If seasons were loaded before encounters, the encounter season dicts
        # should use season names from seasons_list
        for name, data in config.encounters_data.items():
            for key in data['season'].keys():
                assert key in config.seasons_list, \
                    f"Encounter '{name}' has season key '{key}' not in seasons_list"

    def test_config_file_paths_set(self):
        """seasons_file and watches_file should be populated."""
        _ensure_data_loaded()
        assert config.seasons_file != ""
        assert config.watches_file != ""


# ============================================================================
# 11. EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Edge case tests."""

    def test_all_weights_non_negative(self):
        """No weight in 4D array should be negative."""
        _ensure_data_loaded()
        arr = config.encounter_by_zone_watch_and_season
        assert (arr >= 0).all(), "All weights must be >= 0"

    def test_season_percentages_in_range(self):
        """All per-encounter season percentages should be between 0.0 and 1.0."""
        _ensure_data_loaded()
        for name, data in config.encounters_data.items():
            for season, pct in data['season'].items():
                assert 0.0 <= pct <= 1.0, \
                    f"Encounter '{name}' season '{season}' pct {pct} out of range"

    def test_overlay_zone_with_season(self):
        """Overlay zone logic should still work with season modification."""
        _ensure_data_loaded()

        if not config.overland_overlay_list:
            return  # Skip if no overlays

        enc = Encounter()
        enc.generate_overland_encounter(
            zone=config.overland_zones_list[0],
            overlay=config.overland_overlay_list[0],
            watch='Morning',
            season='Summer',
            encounters_data=config.encounters_data,
            encounter_by_zone_watch_and_season=config.encounter_by_zone_watch_and_season,
            zones_data=config.zones_data,
            seasons_data=config.seasons_data
        )
        # Should complete without error


# ============================================================================
# 12. SITE ENCOUNTER SEASON KEY FIX
# ============================================================================

class TestSiteEncounterSeasonKey:
    """Tests that site encounters correctly read the 'season' key (not 'seasons')."""

    def test_site_encounter_gets_season_dict(self):
        """Site encounter should populate self.seasons with a dict, not 'Any'."""
        _ensure_data_loaded()
        from unittest.mock import patch

        # Force an encounter to occur by making the roll very low
        enc = Encounter()
        with patch('random.random', return_value=0.001):
            enc.generate_site_encounter(
                zone=config.site_zones_list[0] if config.site_zones_list else config.overland_zones_list[0],
                time_slot='Current',
                encounters_data=config.encounters_data,
                encounter_by_zone=config.encounter_by_zone,
                zones_data=config.zones_data
            )

        if enc.is_encounter():
            assert isinstance(enc.seasons, dict), \
                f"Site encounter seasons should be dict, got {type(enc.seasons)}: {enc.seasons}"

    def test_site_encounter_season_matches_overland(self):
        """Site and overland encounters for same creature should have same season data."""
        _ensure_data_loaded()
        from unittest.mock import patch

        # Generate a site encounter
        enc_site = Encounter()
        with patch('random.random', return_value=0.001):
            enc_site.generate_site_encounter(
                zone=config.site_zones_list[0] if config.site_zones_list else config.overland_zones_list[0],
                time_slot='Current',
                encounters_data=config.encounters_data,
                encounter_by_zone=config.encounter_by_zone,
                zones_data=config.zones_data
            )

        if enc_site.is_encounter():
            # The seasons field should match what's in encounters_data
            expected = config.encounters_data[enc_site.name]['season']
            assert enc_site.seasons == expected, \
                f"Site encounter '{enc_site.name}' seasons mismatch: {enc_site.seasons} != {expected}"


# ============================================================================
# 13. WEATHER VALIDATION FIX
# ============================================================================

class TestWeatherValidation:
    """Tests that all weather types in Excel exist in weathers YAML."""

    def test_no_weather_validation_errors(self):
        """All weather types in Excel should exist in weathers_data."""
        _ensure_data_loaded()
        errors = validate_data()
        weather_errors = [e for e in errors if "weather_by_season not found in weathers_data" in e]
        assert len(weather_errors) == 0, f"Weather validation errors: {weather_errors}"

    def test_solid_fog_exists(self):
        _ensure_data_loaded()
        assert 'Solid Fog' in config.weathers_data

    def test_gentle_rains_rainbows_exists(self):
        _ensure_data_loaded()
        assert 'Gentle Rains, then Rainbows' in config.weathers_data

    def test_thunderstorm_air_elementals_exists(self):
        _ensure_data_loaded()
        assert 'Thunderstorm, followed by Air Elementals' in config.weathers_data

    def test_solid_fog_effects(self):
        _ensure_data_loaded()
        effects = config.weathers_data['Solid Fog']['effects']
        assert 'Poor Visibility' in effects
        assert 'Difficult Travel' in effects

    def test_gentle_rains_rainbows_effects(self):
        _ensure_data_loaded()
        effects = config.weathers_data['Gentle Rains, then Rainbows']['effects']
        assert 'Light Precipitation' in effects

    def test_thunderstorm_air_elementals_effects(self):
        _ensure_data_loaded()
        effects = config.weathers_data['Thunderstorm, followed by Air Elementals']['effects']
        assert 'Heavy Precipitation' in effects
        assert 'Poor Visibility' in effects
        assert 'Difficult Travel' in effects

    def test_zero_validation_errors_total(self):
        """After all fixes, validate_data should return zero errors."""
        _ensure_data_loaded()
        errors = validate_data()
        assert len(errors) == 0, f"Expected 0 validation errors, got {len(errors)}: {errors}"
