#!/usr/bin/env python3
"""
Torchcrawl GM Control Panel - NiceGUI Version

A web-based application for Game Masters. Migrated from Streamlit to NiceGUI for perfect spacing control.

Usage:
    python app.py
    python app.py --verbose
"""

import argparse
import sys
from nicegui import ui, app

# Import core modules
import config
from logger import setup_logging, log_info, log_error
from utils import (
    set_verbose_mode, verbose_print, format_time_display, parse_percentage,
    get_calendar_date_string, get_current_season, advance_calendar_date, get_current_holiday,
    get_moon_phase_info, advance_lunar_day, set_lunar_day_to_phase, adjust_lunar_day,
    initialize_lunar_day, MOON_PHASES
)
from data_loader import load_all_data, save_calendar_date
from overland_logic import (
    overland_reset, overland_new_day, overland_regenerate_day,
    regenerate_individual_weather, regenerate_individual_overland_encounter
)
from site_logic import (
    site_reset, site_new_turn, site_regenerate_turn,
    site_add_timer, site_delete_timer, regenerate_individual_site_encounter
)
from models import Encounter


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Torchcrawl GM Control Panel')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    return parser.parse_args()


def reset_expansion_states(mode: str = "all"):
    """Reset encounter expansion states."""
    if mode == "all" or mode == "overland":
        app.storage.user['overland_expansions'] = {}

    if mode == "all" or mode == "site":
        app.storage.user['site_expansions'] = {}


def render_encounter(encounter: Encounter, label: str, mode: str, refresh_func):
    """Render a single encounter with expansion control."""
    has_encounter = encounter.is_encounter()
    
    # Add indentation to encounters (under section heading)
    with ui.row().classes('w-full items-start gap-0 mt-0 mb-0 ml-4'):
        if has_encounter:
            # Emphasize based on mode:
            # Overland: emphasize all encounter names
            # Site: only emphasize if "Current"
            should_emphasize = (mode == "overland") or (mode == "site" and label == "Current")
            
            if should_emphasize:
                display_text = f'{label}: <span class="emphasis">{encounter.name}</span>'
            else:
                display_text = f'{label}: {encounter.name}'
            
            # Regenerate button callback
            def regen():
                if mode == "overland":
                    regenerate_individual_overland_encounter(label)
                else:
                    regenerate_individual_site_encounter(label)
                refresh_func.refresh()
            
            # Structure: column for encounter, button on same line as name
            # CRITICAL: gap-0 removes spacing between name and details!
            with ui.column().classes('w-full mt-0 mb-0 gap-0').style('gap: 0 !important;'):
                # Name and button on same row (created FIRST so it appears on top)
                with ui.row().classes('w-full items-start gap-0 mt-0 mb-0'):
                    # Clickable name to expand/collapse
                    name_label = ui.html(f'<span style="cursor: pointer;">{display_text}</span>', sanitize=False).classes('mt-0 mb-0')
                    
                    # Regenerate button
                    ui.button('🔄', on_click=regen).props('flat dense')
                
                # Expandable content container (created SECOND so it appears below)
                # Remove all padding, margins, and gap for ultra-tight spacing
                details_container = ui.column().classes('mt-0 mb-0 gap-0').style('padding: 0 !important; margin: 0 !important; gap: 0 !important;')
                
                # Check if this encounter should be initially expanded (persisted in storage)
                storage_key = f'{mode}_expansions'
                expansions = app.storage.user.get(storage_key, {})
                details_container.visible = expansions.get(label, False)

                # Toggle function - saves state so it persists across refreshes
                def toggle_expand():
                    details_container.visible = not details_container.visible
                    expansions = app.storage.user.get(storage_key, {})
                    expansions[label] = details_container.visible
                    app.storage.user[storage_key] = expansions
                
                # Attach click handler to name
                name_label.on('click', toggle_expand)
                
                # Content inside expandable container
                with details_container:
                    # Description - ultra-tight spacing, indented, no padding/margin
                    if encounter.description:
                        ui.html(f'''
                            <div style="margin: 0; padding: 0; margin-left: 2em; line-height: 1.2;">
                                Description: {encounter.description}
                            </div>
                        ''', sanitize=False).classes('mt-0')
                    
                    # Sparks - numbered, ultra-tight spacing, minimal margin after last one
                    if encounter.sparks:
                        for i, spark in enumerate(encounter.sparks, 1):
                            bottom_margin = "0.3em" if i == len(encounter.sparks) else "0"
                            ui.html(f'''
                                <div style="margin: 0; padding: 0; margin-left: 2em; margin-bottom: {bottom_margin}; line-height: 1.2;">
                                    {i}. {spark}
                                </div>
                            ''', sanitize=False).classes('mt-0')
        else:
            # No encounter - use expansion for vertical alignment, not emphasized
            with ui.expansion(f'{label}: No Encounter', icon='expand_more').classes('mt-0 mb-0').props('disable').style('margin-left: 0 !important; padding-left: 0 !important;'):
                pass  # Empty expansion
            
            def regen_no_enc():
                if mode == "overland":
                    regenerate_individual_overland_encounter(label)
                else:
                    regenerate_individual_site_encounter(label)
                refresh_func.refresh()
            
            ui.button('🔄', on_click=regen_no_enc).props('flat dense')


def open_weather_dialog():
    """Open the weather selector as a popup dialog."""
    with ui.dialog() as dialog, ui.card():
        weather_dialog_content(dialog)
    dialog.open()


def weather_dialog_content(dialog):
    """Render weather selector inside a dialog."""
    season = config.selected_overland_season

    # Current weather display
    if config.generated_overland_weather and config.generated_overland_weather.name:
        weather_str = str(config.generated_overland_weather)
        if '(' in weather_str:
            name_part = weather_str.split('(')[0].strip()
            effects_part = '(' + weather_str.split('(', 1)[1]
            ui.html(f'Current: <span class="emphasis">{name_part}</span> {effects_part}', sanitize=False).classes('mt-0 mb-1')
        else:
            ui.html(f'Current: <span class="emphasis">{weather_str}</span>', sanitize=False).classes('mt-0 mb-1')
    else:
        ui.label('No weather generated yet').classes('mt-0 mb-1 text-gray-500')

    # Regenerate button
    def handle_regenerate():
        regenerate_individual_weather()
        dialog.close()
        global_header.refresh()
        overland_content.refresh()
        resting_content.refresh()

    ui.button('Regenerate', on_click=handle_regenerate)

    ui.separator().classes('my-2')

    # List valid weathers for current season (above-0 probability, excluding "No Change")
    ui.label(f'Weathers for {season}').classes('font-bold mt-0 mb-1')

    if config.weather_by_season is not None:
        weights = {}
        for weather_name in config.weather_by_season.coords['Weather'].values:
            w = float(config.weather_by_season.loc[weather_name, season])
            if w > 0 and weather_name != "No Change":
                weights[weather_name] = w
        total = sum(weights.values())

        if weights:
            sorted_weathers = sorted(weights.items(), key=lambda x: x[1], reverse=True)
            with ui.column().classes('mt-0 mb-0 gap-0'):
                for weather_name, w in sorted_weathers:
                    pct = w / total * 100
                    effects = config.weathers_data.get(weather_name, {}).get('effects', [])
                    effects_str = f' ({", ".join(effects)})' if effects else ''
                    is_current = (config.generated_overland_weather and
                                  config.generated_overland_weather.name == weather_name)

                    def make_weather_click(name=weather_name):
                        def handler():
                            from models import Weather
                            from overland_logic import generate_overland_rest_info
                            weather_info = config.weathers_data.get(name, {'effects': []})
                            if config.generated_overland_weather is None:
                                config.generated_overland_weather = Weather()
                            config.generated_overland_weather.name = name
                            config.generated_overland_weather.effects = weather_info.get('effects', [])
                            generate_overland_rest_info()
                            dialog.close()
                            global_header.refresh()
                            overland_content.refresh()
                            resting_content.refresh()
                        return handler

                    display = f'{weather_name}{effects_str} — {pct:.0f}%'
                    if is_current:
                        ui.html(
                            f'<span class="emphasis" style="cursor: pointer;">{display}</span>',
                            sanitize=False
                        ).classes('mt-0 mb-0').on('click', make_weather_click())
                    else:
                        ui.html(
                            f'<span style="cursor: pointer;">{display}</span>',
                            sanitize=False
                        ).classes('mt-0 mb-0').on('click', make_weather_click())
        else:
            ui.label('No weathers available for this season').classes('mt-0 mb-0 text-gray-500')

    # Close button
    with ui.row().classes('w-full justify-end mt-2'):
        ui.button('Close', on_click=dialog.close)


def open_calendar_dialog():
    """Open the calendar date picker as a popup dialog."""
    with ui.dialog() as dialog, ui.card().classes('w-full').style('max-width: 600px;'):
        calendar_dialog_content(dialog)
    dialog.open()


def open_moon_dialog():
    """Open the moon phase selector as a popup dialog."""
    with ui.dialog() as dialog, ui.card():
        moon_dialog_content(dialog)
    dialog.open()


def calendar_dialog_content(dialog):
    """Render calendar date picker inside a dialog."""
    if not config.calendar_data:
        ui.label('No calendar loaded').classes('text-gray-500')
        return

    current = config.calendar_data.get('current', {})
    months = config.calendar_data.get('months', [])
    holidays = config.calendar_data.get('holidays', [])
    days_per_week = config.calendar_data.get('days_per_week', 6)

    # Build holiday lookup
    holiday_lookup = {}
    for holiday in holidays:
        key = (holiday.get('month'), holiday.get('day'))
        holiday_lookup[key] = holiday

    # Current date display at top
    date_string = get_calendar_date_string()
    if date_string:
        ui.html(date_string, sanitize=False).classes('text-lg font-bold mt-0 mb-0')

    # Holiday info if current date is a holiday
    current_holiday = get_current_holiday()
    if current_holiday:
        with ui.column().classes('mt-0 mb-1 ml-4 gap-0'):
            ui.html(f'<span class="emphasis">{current_holiday.get("name", "")}</span>', sanitize=False).classes('mt-0 mb-0')
            ui.label(current_holiday.get('description', '')).classes('mt-0 mb-0 text-sm')

    ui.separator().classes('my-2')

    # Month grids with season-change separators
    prev_season = None
    for month_idx, month in enumerate(months, 1):
        month_name = month.get('name', f'Month {month_idx}')
        month_season = month.get('season', '')
        days_in_month = month.get('days', 30)

        # Season change separator between months
        if prev_season is not None and month_season != prev_season:
            ui.separator().classes('my-2')
        prev_season = month_season

        ui.label(month_name).classes('calendar-month-header')

        with ui.grid(columns=days_per_week).classes('gap-0'):
            for day in range(1, days_in_month + 1):
                is_current = (current and
                              current.get('calendar_month') == month_idx and
                              current.get('calendar_day') == day)
                is_holiday = (month_name, day) in holiday_lookup

                btn_classes = 'calendar-day'
                if is_current:
                    btn_classes += ' calendar-day-current'
                if is_holiday:
                    btn_classes += ' calendar-day-holiday'

                def make_click_handler(m=month_idx, d=day):
                    def handler():
                        save_calendar_date(m, d)
                        new_season = get_current_season()
                        if new_season and new_season in config.seasons_list:
                            config.selected_overland_season = new_season
                        dialog.close()
                        global_header.refresh()
                        overland_content.refresh()
                    return handler

                btn = ui.button(str(day), on_click=make_click_handler()).props('flat dense')
                btn.classes(btn_classes)

                if is_holiday:
                    holiday_info = holiday_lookup[(month_name, day)]
                    btn.tooltip(holiday_info.get('name', ''))

    ui.separator().classes('my-2')

    # Holiday list
    ui.label('Holidays').classes('text-lg font-bold mt-0 mb-0')

    if holidays:
        with ui.column().classes('mt-0 mb-0 ml-4 gap-0'):
            for holiday in holidays:
                h_name = holiday.get('name', '')
                h_month = holiday.get('month', '')
                h_day = holiday.get('day', '')

                is_current_hol = (current_holiday and
                                  current_holiday.get('name') == h_name)

                holiday_text = f'{h_name} - {h_month} {h_day}'

                def make_holiday_click(month_name=h_month, day=h_day):
                    def handler():
                        month_idx = config.calendar_month_lookup.get(month_name)
                        if month_idx:
                            save_calendar_date(month_idx, day)
                            new_season = get_current_season()
                            if new_season and new_season in config.seasons_list:
                                config.selected_overland_season = new_season
                            dialog.close()
                            global_header.refresh()
                            overland_content.refresh()
                    return handler

                if is_current_hol:
                    ui.html(
                        f'<span class="emphasis" style="cursor: pointer;">{holiday_text}</span>',
                        sanitize=False
                    ).classes('mt-0 mb-0').on('click', make_holiday_click())
                else:
                    ui.html(
                        f'<span style="cursor: pointer;">{holiday_text}</span>',
                        sanitize=False
                    ).classes('mt-0 mb-0').on('click', make_holiday_click()).tooltip(holiday.get('description', ''))
    else:
        ui.label('No holidays defined').classes('mt-0 mb-0 ml-4 text-gray-500')

    # Close button
    with ui.row().classes('w-full justify-end mt-2'):
        ui.button('Close', on_click=dialog.close)


def moon_dialog_content(dialog):
    """Render moon phase selector inside a dialog."""
    if not config.calendar_data or not config.calendar_data.get('lunar_cycle_length'):
        ui.label('No lunar tracking configured').classes('text-gray-500')
        return

    # Initialize lunar day if needed
    current = config.calendar_data.get('current', {})
    if current.get('lunar_day') is None:
        initialize_lunar_day()

    moon_phase = get_moon_phase_info()
    current_phase_index = moon_phase['phase_index'] if moon_phase else -1

    # Current phase display
    if moon_phase:
        if moon_phase.get('is_blood_moon'):
            ui.html(
                f'<span class="blood-moon"></span> <span style="color: #cc2222;">{moon_phase["name"]}</span>',
                sanitize=False
            ).classes('text-lg font-bold mt-0 mb-0')
        else:
            ui.html(
                f'{moon_phase["icon"]} {moon_phase["name"]}',
                sanitize=False
            ).classes('text-lg font-bold mt-0 mb-0')

    ui.separator().classes('my-2')

    with ui.row().classes('items-center gap-1 mt-0 mb-1'):
        ui.label('Lunar Phase:').classes('mr-2')

        def handle_lunar_minus():
            adjust_lunar_day(-1)
            dialog.close()
            global_header.refresh()
            overland_content.refresh()
            open_moon_dialog()
        ui.button('−', on_click=handle_lunar_minus).props('flat dense').classes('lunar-phase-btn')

        for idx, phase in enumerate(MOON_PHASES):
            def make_phase_handler(phase_idx=idx):
                def handler():
                    set_lunar_day_to_phase(phase_idx)
                    dialog.close()
                    global_header.refresh()
                    overland_content.refresh()
                    open_moon_dialog()
                return handler

            btn_classes = 'lunar-phase-btn'
            if idx == current_phase_index:
                btn_classes += ' lunar-phase-current'

            ui.button(phase['icon'], on_click=make_phase_handler()).props('flat dense').classes(btn_classes).tooltip(phase['name'])

        def handle_lunar_plus():
            adjust_lunar_day(1)
            dialog.close()
            global_header.refresh()
            overland_content.refresh()
            open_moon_dialog()
        ui.button('+', on_click=handle_lunar_plus).props('flat dense').classes('lunar-phase-btn')

    # Close button
    with ui.row().classes('w-full justify-end mt-2'):
        ui.button('Close', on_click=dialog.close)


@ui.refreshable
def global_header():
    """Persistent header above all tabs — date/moon, weather, days out, zone/overlay/season."""

    has_calendar = config.calendar_data is not None
    has_calendar_date = has_calendar and config.calendar_data.get('current') is not None

    # Auto-sync season from calendar
    if has_calendar_date:
        calendar_season = get_current_season()
        if calendar_season and calendar_season in config.seasons_list:
            config.selected_overland_season = calendar_season

    # --- Row 1: New Day | Date/Moon | Weather | Days Out ---
    def handle_new_day():
        reset_expansion_states("overland")
        if has_calendar_date:
            advance_calendar_date(1)
            if config.calendar_data.get('lunar_cycle_length'):
                advance_lunar_day(1)
            new_season = get_current_season()
            if new_season and new_season in config.seasons_list:
                config.selected_overland_season = new_season
        overland_new_day()
        global_header.refresh()
        overland_content.refresh()
        resting_content.refresh()

    with ui.row().classes('w-full items-center gap-4 mt-0 mb-0'):
        ui.button('New Day', on_click=handle_new_day)

        # Date (clickable → calendar popup)
        if has_calendar:
            date_string = get_calendar_date_string()
            if date_string:
                ui.html(
                    f'<span style="cursor: pointer;" title="Click to open calendar">{date_string}</span>',
                    sanitize=False
                ).classes('mt-0 mb-0').on('click', lambda: open_calendar_dialog())

            # Moon phase (clickable → moon popup, separate from date)
            moon_phase = get_moon_phase_info()
            if moon_phase:
                if moon_phase.get('is_blood_moon'):
                    moon_html = f'<span class="blood-moon"></span> <span style="color: #cc2222;">{moon_phase["name"]}</span>'
                else:
                    moon_html = f'{moon_phase["icon"]} {moon_phase["name"]}'
                ui.html(
                    f'<span style="cursor: pointer;" title="Click to change moon phase">{moon_html}</span>',
                    sanitize=False
                ).classes('mt-0 mb-0').on('click', lambda: open_moon_dialog())

        # Weather display — name only, no effects (clickable → weather popup)
        if config.generated_overland_weather and config.generated_overland_weather.name:
            weather_html = f'Weather: <span class="emphasis">{config.generated_overland_weather.name}</span>'
            ui.html(
                f'<span style="cursor: pointer;" title="Click to change weather">{weather_html}</span>',
                sanitize=False
            ).classes('mt-0 mb-0').on('click', lambda: open_weather_dialog())
        else:
            ui.html(
                '<span style="cursor: pointer;" title="Click to set weather">No weather generated yet</span>',
                sanitize=False
            ).classes('mt-0 mb-0 text-gray-500').on('click', lambda: open_weather_dialog())

        # Days Out (clickable → confirmation dialog → reset)
        def handle_days_out_click():
            with ui.dialog() as dlg, ui.card():
                ui.label(f'Reset overland state? ({config.generated_overland_days} days, weather, encounters)').classes('mb-2')
                with ui.row().classes('w-full justify-end gap-2'):
                    ui.button('Cancel', on_click=dlg.close)
                    def confirm_reset():
                        dlg.close()
                        reset_expansion_states("overland")
                        overland_reset()
                        global_header.refresh()
                        overland_content.refresh()
                    ui.button('Reset', on_click=confirm_reset).props('color=negative')
            dlg.open()

        ui.html(
            f'<span style="cursor: pointer;" title="Click to reset">'
            f'{config.generated_overland_days} days</span>',
            sanitize=False
        ).classes('mt-0 mb-0').on('click', handle_days_out_click)

    # --- Row 2: Holiday info (conditional) ---
    if has_calendar_date:
        current_holiday = get_current_holiday()
        if current_holiday:
            with ui.row().classes('w-full items-center gap-2 mt-0 mb-0'):
                holiday_text = f"{current_holiday.get('name', '')} — {current_holiday.get('description', '')}"
                ui.label(holiday_text).classes('mt-0 mb-0 text-sm')

    # --- Row 3: Zone / Overlay / Season dropdowns ---
    def handle_header_zone_change(e):
        config.selected_overland_zone = e.value
        global_header.refresh()
        overland_content.refresh()
        resting_content.refresh()
        overland_probability_content.refresh()

    def handle_header_overlay_change(e):
        config.selected_overland_overlay = None if e.value == "None" else e.value
        global_header.refresh()
        overland_content.refresh()
        resting_content.refresh()
        overland_probability_content.refresh()

    def handle_header_season_change(e):
        config.selected_overland_season = e.value
        global_header.refresh()
        overland_content.refresh()
        resting_content.refresh()
        overland_probability_content.refresh()

    with ui.row().classes('w-full gap-2 mt-1 mb-1'):
        ui.select(
            options=config.overland_zones_list,
            value=config.selected_overland_zone,
            label='Overland Zone',
            on_change=handle_header_zone_change
        ).classes('flex-1')

        overlay_options = ["None"] + config.overland_overlay_list
        current_overlay = "None" if config.selected_overland_overlay is None else config.selected_overland_overlay
        ui.select(
            options=overlay_options,
            value=current_overlay,
            label='Overlay Zone',
            on_change=handle_header_overlay_change
        ).classes('flex-1')

        # Season dropdown: only show if NO calendar date (calendar drives season)
        if not has_calendar_date:
            ui.select(
                options=config.seasons_list,
                value=config.selected_overland_season,
                label='Season',
                on_change=handle_header_season_change
            ).classes('flex-1')

    ui.separator().classes('my-1')


@ui.refreshable
def overland_content():
    """Refreshable Overland Travel tab content."""

    # Weather with effects + popup button
    if config.generated_overland_weather and config.generated_overland_weather.name:
        with ui.row().classes('items-center gap-0 mt-0 mb-0'):
            weather_str = str(config.generated_overland_weather)
            if '(' in weather_str:
                name_part = weather_str.split('(')[0].strip()
                effects_part = '(' + weather_str.split('(', 1)[1]
                ui.html(f'Weather: <span class="emphasis">{name_part}</span> {effects_part}', sanitize=False)
            else:
                ui.html(f'Weather: <span class="emphasis">{weather_str}</span>', sanitize=False)
            ui.button('🔄', on_click=lambda: open_weather_dialog()).props('flat dense')

    # Encounters section
    def handle_regenerate_encounters():
        reset_expansion_states("overland")
        overland_regenerate_day()
        global_header.refresh()
        overland_content.refresh()
        resting_content.refresh()

    with ui.row().classes('items-center gap-0 mt-0 mb-0'):
        ui.label('Encounters').classes('text-lg font-bold')
        ui.button('🔄', on_click=handle_regenerate_encounters).props('flat dense')

    for watch in config.watches_list:
        encounter = config.generated_overland_encounters.get(watch)
        if encounter:
            render_encounter(encounter, watch, "overland", overland_content)


@ui.refreshable
def resting_content():
    """Refreshable Resting tab content."""

    # Rest Check section
    ui.label('Rest Check').classes('text-lg font-bold mt-0 mb-0')

    if config.generated_overland_rest_info:
        rest_info = config.generated_overland_rest_info

        ui.label(f'Rest DCs for {config.selected_overland_season}').classes('font-bold mt-0 mb-0 ml-4')
        rest_dcs = rest_info.get('rest_dcs', [])
        if rest_dcs:
            with ui.column().classes('mt-0 mb-0 ml-8'):
                for item in rest_dcs:
                    ui.label(f"{item.get('camp', '')}  {item.get('dc', '')}").classes('mt-0 mb-0')

        weather_mods = rest_info.get('weather_modifiers', [])
        if weather_mods:
            ui.label('Weather Modifiers').classes('font-bold mt-0 mb-0 ml-4')
            with ui.column().classes('mt-0 mb-0 ml-8'):
                for mod in weather_mods:
                    mod_text = f"{mod.get('description', '')}  {mod.get('modifier', '')}"
                    ui.html(f'<span class="emphasis">{mod_text}</span>', sanitize=False).classes('mt-0 mb-0')

        ui.label('Situational Modifiers').classes('font-bold mt-0 mb-0 ml-4')
        situational_mods = rest_info.get('situational_modifiers', [])
        if situational_mods:
            with ui.column().classes('mt-0 mb-0 ml-8'):
                for mod in situational_mods:
                    ui.label(f"{mod.get('situation', '')}  {mod.get('modifier', '')}").classes('mt-0 mb-0')
    else:
        ui.label('No rest information generated yet').classes('mt-0 mb-0 ml-4 text-gray-500')


@ui.refreshable
def site_content():
    """Refreshable Site tab content."""
    
    # Zone dropdown
    def handle_site_zone_change(e):
        config.selected_site_zone = e.value
        site_probability_content.refresh()

    with ui.row().classes('w-full mt-1 mb-1'):
        ui.select(
            options=config.site_zones_list,
            value=config.selected_site_zone,
            label='Site Zone',
            on_change=handle_site_zone_change
        ).classes('flex-1')
    
    # Action buttons
    with ui.row().classes('gap-2 mt-1 mb-1'):
        ui.button('New Turn', on_click=lambda: (reset_expansion_states("site"), site_new_turn(), site_content.refresh()))
        ui.button('Regenerate All', on_click=lambda: (reset_expansion_states("site"), site_regenerate_turn(), site_content.refresh()))
        ui.button('Reset', on_click=lambda: (reset_expansion_states("site"), site_reset(), site_content.refresh()))
    
    # General section
    ui.label('General').classes('text-lg font-bold mt-0 mb-0')
    time_str = format_time_display(config.generated_site_time)
    # Emphasize only "X minutes" part, not the "(H hours M minutes)" part
    if '(' in time_str:
        minutes_part = time_str.split('(')[0].strip()
        hours_part = '(' + time_str.split('(', 1)[1]
        ui.html(f'<span class="emphasis">{minutes_part}</span> {hours_part}', sanitize=False).classes('mt-0 mb-0 ml-4')
    else:
        ui.html(f'<span class="emphasis">{time_str}</span>', sanitize=False).classes('mt-0 mb-0 ml-4')
    
    # Timers section - button shows +/- based on form visibility
    timer_form_visible = app.storage.user.get('show_timer_form', False)
    with ui.row().classes('items-center gap-0 mt-0 mb-0'):
        ui.label('Timers').classes('text-lg font-bold')
        timer_button_icon = '➖' if timer_form_visible else '➕'
        ui.button(timer_button_icon, on_click=lambda: toggle_timer_form()).props('flat dense')

    # Timer creation form (conditional) - indented
    if timer_form_visible:
        with ui.row().classes('gap-2 mt-0 mb-0 items-end ml-4'):
            timer_name = ui.input(label='Timer Name', placeholder='e.g., Torch expires').classes('flex-1')
            timer_duration = ui.number(label='Duration (min)', value=60, step=10, min=0).classes('w-32')
            
            def add_timer_action():
                if timer_name.value:
                    site_add_timer(timer_name.value, int(timer_duration.value or 60))
                    app.storage.user['show_timer_form'] = False
                    site_content.refresh()
            
            def cancel_timer():
                app.storage.user['show_timer_form'] = False
                site_content.refresh()
            
            ui.button('Add Timer', on_click=add_timer_action)
            ui.button('Cancel', on_click=cancel_timer)
    
    # Display timers - indented
    if config.generated_site_timers:
        with ui.column().classes('w-full mt-0 mb-0 ml-4'):
            for i, timer in enumerate(config.generated_site_timers):
                with ui.row().classes('w-full items-center gap-0 mt-0 mb-0'):
                    # Emphasize name only if "Current:"
                    timer_str = str(timer)
                    if timer_str.startswith('Current:'):
                        # Parse "Current: Name" and emphasize only the name
                        timer_name = timer_str.split(':', 1)[1].strip()
                        ui.html(f'Current: <span class="emphasis">{timer_name}</span>', sanitize=False)
                    else:
                        # Normal timer display
                        ui.label(timer_str)
                    
                    ui.button('❌', on_click=lambda idx=i: (site_delete_timer(idx), site_content.refresh())).props('flat dense')
    else:
        ui.label('No active timers').classes('mt-0 mb-0 ml-4 text-gray-500')
    
    # Encounters section
    ui.label('Encounters').classes('text-lg font-bold mt-0 mb-0')
    
    for time_slot in config.SITE_TIME_SLOTS:
        encounter = config.generated_site_encounters.get(time_slot)
        if encounter:
            render_encounter(encounter, time_slot, "site", site_content)


@ui.refreshable
def site_probability_content():
    """Refreshable Site probability distribution tab content."""

    def handle_zone_change(e):
        config.selected_site_zone = e.value
        site_probability_content.refresh()
        site_content.refresh()

    # Zone dropdown (synced with site tab's zone)
    with ui.row().classes('w-full mt-1 mb-1'):
        ui.select(
            options=config.site_zones_list,
            value=config.selected_site_zone,
            label='Site Zone',
            on_change=handle_zone_change
        ).classes('flex-1')

    # Encounter chance
    encounter_chance = parse_percentage(config.zones_data[config.selected_site_zone]['encounter_chance'])
    ui.label(f'Encounter chance: {encounter_chance:.0%}').classes('mt-0 mb-0 ml-4')

    ui.separator().classes('my-1')

    # Build probability list from 2D array
    weights = {}
    for enc in config.encounter_by_zone.coords['Encounter'].values:
        w = float(config.encounter_by_zone.loc[enc, config.selected_site_zone])
        if w > 0:
            weights[enc] = w
    total = sum(weights.values())

    # Sort descending, display
    if total > 0:
        sorted_encs = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        with ui.column().classes('mt-0 mb-0 ml-4'):
            for name, w in sorted_encs:
                pct = w / total * 100
                ui.label(f'{name}: {pct:.1f}%').classes('mt-0 mb-0')
    else:
        ui.label('No encounters available for this zone').classes('mt-0 mb-0 ml-4 text-gray-500')


@ui.refreshable
def overland_probability_content():
    """Refreshable Overland probability distribution tab content."""

    def handle_zone_change(e):
        config.selected_overland_zone = e.value
        global_header.refresh()
        overland_probability_content.refresh()
        overland_content.refresh()

    def handle_overlay_change(e):
        config.selected_overland_overlay = None if e.value == "None" else e.value
        global_header.refresh()
        overland_probability_content.refresh()
        overland_content.refresh()

    def handle_watch_change(e):
        config.selected_overland_watch = e.value
        overland_probability_content.refresh()

    # Dropdowns synced with header — zone, overlay from config globals + local watch; season displayed as text
    with ui.row().classes('w-full gap-2 mt-1 mb-1 items-center'):
        ui.select(
            options=config.overland_zones_list,
            value=config.selected_overland_zone,
            label='Zone',
            on_change=handle_zone_change
        ).classes('flex-1')

        overlay_options = ["None"] + config.overland_overlay_list
        current_overlay = "None" if config.selected_overland_overlay is None else config.selected_overland_overlay
        ui.select(
            options=overlay_options,
            value=current_overlay,
            label='Overlay',
            on_change=handle_overlay_change
        ).classes('flex-1')

        ui.select(
            options=config.watches_list,
            value=config.selected_overland_watch,
            label='Watch',
            on_change=handle_watch_change
        ).classes('flex-1')

        ui.label(config.selected_overland_season).classes('mt-0 mb-0')

    zone = config.selected_overland_zone
    overlay = config.selected_overland_overlay
    season = config.selected_overland_season
    watch = config.selected_overland_watch

    season_mod = parse_percentage(config.seasons_data[season]['encounter_modification'])

    if overlay is None:
        # No overlay - simple calculation
        ec = parse_percentage(config.zones_data[zone]['encounter_chance']) * season_mod
        ui.label(f'Encounter chance: {ec:.2%}').classes('mt-0 mb-0 ml-4')

        ui.separator().classes('my-1')

        # Build probability list from 4D array
        weights = {}
        for enc in config.encounter_by_zone_watch_and_season.coords['Encounter'].values:
            w = float(config.encounter_by_zone_watch_and_season.loc[enc, zone, watch, season])
            if w > 0:
                weights[enc] = w
        total = sum(weights.values())

        if total > 0:
            sorted_encs = sorted(weights.items(), key=lambda x: x[1], reverse=True)
            with ui.column().classes('mt-0 mb-0 ml-4'):
                for name, w in sorted_encs:
                    pct = w / total * 100
                    ui.label(f'{name}: {pct:.1f}%').classes('mt-0 mb-0')
        else:
            ui.label('No encounters available for this combination').classes('mt-0 mb-0 ml-4 text-gray-500')
    else:
        # Overlay - blended calculation
        ec_base = parse_percentage(config.zones_data[zone]['encounter_chance']) * season_mod
        ec_overlay = parse_percentage(config.zones_data[overlay]['encounter_chance']) * season_mod
        blended_ec = 0.5 * ec_base + 0.5 * ec_overlay
        ui.label(f'Encounter chance: {blended_ec:.2%}').classes('mt-0 mb-0 ml-4')

        ui.separator().classes('my-1')

        # Build weights for both zones
        base_weights = {}
        overlay_weights = {}
        all_encounters = set()
        for enc in config.encounter_by_zone_watch_and_season.coords['Encounter'].values:
            w_base = float(config.encounter_by_zone_watch_and_season.loc[enc, zone, watch, season])
            w_overlay = float(config.encounter_by_zone_watch_and_season.loc[enc, overlay, watch, season])
            if w_base > 0:
                base_weights[enc] = w_base
                all_encounters.add(enc)
            if w_overlay > 0:
                overlay_weights[enc] = w_overlay
                all_encounters.add(enc)

        total_base = sum(base_weights.values())
        total_overlay = sum(overlay_weights.values())

        if all_encounters and blended_ec > 0:
            # True conditional probability: P(E | encounter occurs)
            blended_probs = {}
            for enc in all_encounters:
                p_base = (base_weights.get(enc, 0) / total_base) if total_base > 0 else 0
                p_overlay = (overlay_weights.get(enc, 0) / total_overlay) if total_overlay > 0 else 0
                blended_p = (0.5 * ec_base * p_base + 0.5 * ec_overlay * p_overlay) / blended_ec
                if blended_p > 0:
                    blended_probs[enc] = blended_p * 100

            sorted_encs = sorted(blended_probs.items(), key=lambda x: x[1], reverse=True)
            with ui.column().classes('mt-0 mb-0 ml-4'):
                for name, pct in sorted_encs:
                    ui.label(f'{name}: {pct:.1f}%').classes('mt-0 mb-0')
        else:
            ui.label('No encounters available for this combination').classes('mt-0 mb-0 ml-4 text-gray-500')


def toggle_timer_form():
    """Toggle timer form visibility."""
    # Initialize if not exists
    if 'show_timer_form' not in app.storage.user:
        app.storage.user['show_timer_form'] = False

    current = app.storage.user.get('show_timer_form', False)
    app.storage.user['show_timer_form'] = not current
    site_content.refresh()


@ui.page('/')
def index():
    """Main application page."""

    # Initialize UI state - ensure timer form starts collapsed
    app.storage.user['show_timer_form'] = False

    # Enable dark mode - auto-detect from system
    dark = ui.dark_mode()
    dark.auto()  # Automatically follow system dark/light mode preference
    
    # Custom CSS for additional spacing control
    ui.add_head_html('''
        <style>
            /* Emphasis color - coral pink */
            .emphasis {
                color: #F78080 !important;
                font-weight: 500;
            }
            
            /* Ultra-tight overall spacing */
            .nicegui-content {
                padding-top: 0.5rem !important;
                line-height: 1.2 !important;
            }
            /* Minimal spacing between all elements */
            .q-field {
                margin-bottom: 0.1rem !important;
            }
            /* No spacing for expansion items */
            .q-expansion-item__container {
                margin-bottom: 0rem !important;
            }
            /* Remove expansion indentation - flush left */
            .q-expansion-item {
                margin-left: 0 !important;
                padding-left: 0 !important;
                margin-bottom: 0 !important;
            }
            .q-item {
                padding-left: 0 !important;
                min-height: 0 !important;
                padding-top: 0.1rem !important;
                padding-bottom: 0.1rem !important;
            }
            /* Hide expansion icon to remove indentation */
            .q-expansion-item .q-item__section--side {
                display: none !important;
            }
            /* Left-align tabs - multiple selectors for specificity */
            .q-tabs,
            .q-tabs__content {
                justify-content: flex-start !important;
            }
            .q-tabs .q-tabs__content {
                justify-content: flex-start !important;
            }
            /* Normal case for tabs instead of all caps */
            .q-tab__label {
                text-transform: none !important;
            }
            /* Tighter labels */
            .q-field__label {
                font-size: 0.875rem !important;
            }
            /* Reduce button padding */
            .q-btn {
                min-height: 1.5rem !important;
                padding: 0.1rem 0.3rem !important;
            }
            /* Tighter text elements */
            p, div {
                margin-top: 0 !important;
                margin-bottom: 0 !important;
            }

            /* Calendar styles */
            .calendar-day {
                min-width: 2.2rem !important;
                min-height: 2rem !important;
                padding: 0.2rem !important;
                margin: 1px !important;
            }
            .calendar-day-current,
            .calendar-day-current .q-btn__content {
                color: #F78080 !important;
                font-weight: bold !important;
            }
            .calendar-day-holiday {
                background-color: rgba(255, 193, 7, 0.3) !important;
            }
            .calendar-month-header {
                font-weight: bold;
                margin-top: 0.5rem;
                margin-bottom: 0.2rem;
            }

            /* Blood Moon styles - layered CSS technique */
            .blood-moon {
                position: relative;
                display: inline-block;
                width: 1em;
                height: 1em;
                filter: contrast(1.4);
                vertical-align: middle;
                line-height: 1;
            }
            .blood-moon::before {
                content: "🌕";
                position: absolute;
                top: -0.1em;
                left: 0;
                filter: grayscale(0.95);
                z-index: 1;
            }
            .blood-moon::after {
                content: "🌕";
                position: absolute;
                top: -0.1em;
                left: 0;
                z-index: 2;
                color: transparent;
                -webkit-background-clip: text;
                background-clip: text;
                background-color: rgba(255, 0, 0, 0.5);
                pointer-events: none;
            }

            /* Lunar phase selector styles */
            .lunar-phase-btn {
                min-width: 2rem !important;
                min-height: 2rem !important;
                padding: 0.1rem !important;
                margin: 0 !important;
                font-size: 1.2rem !important;
            }
            .lunar-phase-current {
                background-color: rgba(247, 128, 128, 0.3) !important;
                border: 1px solid #F78080 !important;
            }
        </style>
    ''')
    
    # Page title with custom font
    ui.html('''
        <h1 style="font-family: 'GreyhawkGothic', 'Grenze Gotisch', 'UnifrakturMaguntia', serif; 
                   font-size: 2rem; 
                   margin-bottom: 0.5rem; 
                   margin-top: 0;">
            Torchcrawl GM Control Panel
        </h1>
    ''', sanitize=False)
    
    # Persistent global header above tabs
    global_header()

    # 8 tabs
    with ui.tabs().classes('w-full') as tabs:
        overland_tab = ui.tab('Overland Travel')
        forage_tab = ui.tab('Forage')
        resting_tab = ui.tab('Resting')
        site_tab = ui.tab('Site Exploration')
        settlements_tab = ui.tab('Settlements')
        creatures_tab = ui.tab('Creatures')
        overland_prob_tab = ui.tab('Overland Enc. Prob.')
        site_prob_tab = ui.tab('Site Enc. Prob.')

    with ui.tab_panels(tabs, value=overland_tab).classes('w-full'):
        with ui.tab_panel(overland_tab):
            overland_content()

        with ui.tab_panel(forage_tab):
            ui.label('Coming soon').classes('text-gray-500')

        with ui.tab_panel(resting_tab):
            resting_content()

        with ui.tab_panel(site_tab):
            site_content()

        with ui.tab_panel(settlements_tab):
            ui.label('Coming soon').classes('text-gray-500')

        with ui.tab_panel(creatures_tab):
            ui.label('Coming soon').classes('text-gray-500')

        with ui.tab_panel(overland_prob_tab):
            overland_probability_content()

        with ui.tab_panel(site_prob_tab):
            site_probability_content()


def main():
    """Main application entry point."""
    
    # Parse arguments
    args = parse_arguments()
    set_verbose_mode(args.verbose)
    
    # Setup logging
    setup_logging()
    
    verbose_print("=== Application Starting ===")
    log_info("=" * 60)
    log_info("Torchcrawl GM Control Panel - NiceGUI Version Started")
    log_info("=" * 60)
    
    # Load data
    success = load_all_data()
    
    if not success:
        log_error("Application startup failed - data loading error")
        print("ERROR: Failed to load data files. Check logs/TCControlPanel.log for details.")
        sys.exit(1)
    
    # Initialize selections if not set
    if not config.selected_overland_season and config.seasons_list:
        config.selected_overland_season = config.seasons_list[0]
    if not config.selected_overland_zone and config.overland_zones_list:
        config.selected_overland_zone = config.overland_zones_list[0]
    if not config.selected_site_zone and config.site_zones_list:
        config.selected_site_zone = config.site_zones_list[0]
    if not config.selected_overland_watch and config.watches_list:
        config.selected_overland_watch = config.watches_list[0]
    
    verbose_print("=== Application Ready ===")
    
    # Run NiceGUI with storage secret
    ui.run(
        title='Torchcrawl GM Control Panel',
        favicon='🎲',
        reload=False,
        show=True,
        port=8080,
        storage_secret='torchcrawl_gm_secret_key_2026'  # Required for app.storage.user
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
