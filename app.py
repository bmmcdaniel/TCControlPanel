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
    set_verbose_mode, verbose_print, format_time_display,
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
        for watch in config.OVERLAND_WATCHES:
            key = f"expanded_overland_{watch}"
            if key in app.storage.user:
                app.storage.user[key] = False
    
    if mode == "all" or mode == "site":
        for slot in config.SITE_TIME_SLOTS:
            key = f"expanded_site_{slot}"
            if key in app.storage.user:
                app.storage.user[key] = False


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
                
                # For site mode, check if this encounter should be initially expanded
                if mode == "site":
                    expansions = app.storage.user.get('site_expansions', {})
                    details_container.visible = expansions.get(label, False)
                else:
                    details_container.visible = False
                
                # Toggle function - saves state for site mode
                def toggle_expand():
                    details_container.visible = not details_container.visible
                    
                    # Save expansion state for site mode so it persists when encounters shift
                    if mode == "site":
                        expansions = app.storage.user.get('site_expansions', {})
                        expansions[label] = details_container.visible
                        app.storage.user['site_expansions'] = expansions
                
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


@ui.refreshable
def overland_content():
    """Refreshable Overland tab content."""

    # Determine calendar state
    has_calendar = config.calendar_data is not None
    has_calendar_date = has_calendar and config.calendar_data.get('current_date') is not None

    # If calendar with date, auto-sync season from calendar
    if has_calendar_date:
        calendar_season = get_current_season()
        if calendar_season and calendar_season in config.seasons_list:
            config.selected_overland_season = calendar_season

    # Dropdowns - season dropdown conditional on calendar state
    with ui.row().classes('w-full gap-2 mt-1 mb-1'):
        # Season dropdown: only show if NO calendar or calendar without date
        if not has_calendar_date:
            season_select = ui.select(
                options=config.seasons_list,
                value=config.selected_overland_season,
                label='Season'
            ).classes('flex-1')
            season_select.on('change', lambda e: (setattr(config, 'selected_overland_season', e.value), overland_content.refresh()))

        zone_select = ui.select(
            options=config.overland_zones_list,
            value=config.selected_overland_zone,
            label='Zone'
        ).classes('flex-1')

        overlay_options = ["None"] + config.overland_overlay_list
        current_overlay = "None" if config.selected_overland_overlay is None else config.selected_overland_overlay
        overlay_select = ui.select(
            options=overlay_options,
            value=current_overlay,
            label='Overlay'
        ).classes('flex-1')

        # Change handlers
        zone_select.on('change', lambda e: (setattr(config, 'selected_overland_zone', e.value), overland_content.refresh()))
        overlay_select.on('change', lambda e: (setattr(config, 'selected_overland_overlay', None if e.value == "None" else e.value), overland_content.refresh()))

    # Action buttons with calendar-aware New Day
    def handle_new_day():
        reset_expansion_states("overland")
        # Advance calendar date if calendar with date is active
        if has_calendar_date:
            advance_calendar_date(1)
            # Advance lunar day if lunar tracking is active
            if config.calendar_data.get('lunar_cycle_length'):
                advance_lunar_day(1)
            # Update season from calendar (in case month changed)
            new_season = get_current_season()
            if new_season and new_season in config.seasons_list:
                config.selected_overland_season = new_season
        overland_new_day()
        overland_content.refresh()
        calendar_content.refresh()

    with ui.row().classes('gap-2 mt-1 mb-1'):
        ui.button('New Day', on_click=handle_new_day)
        ui.button('Regenerate All', on_click=lambda: (reset_expansion_states("overland"), overland_regenerate_day(), overland_content.refresh()))
        ui.button('Reset', on_click=lambda: (reset_expansion_states("overland"), overland_reset(), overland_content.refresh()))

    # General section
    ui.label('General').classes('text-lg font-bold mt-0 mb-0')

    # Date display (if calendar active)
    if has_calendar:
        date_string = get_calendar_date_string()
        if date_string:
            # Build date + moon phase display
            date_html = date_string

            # Add moon phase if available
            moon_phase = get_moon_phase_info()
            if moon_phase:
                if moon_phase.get('is_blood_moon'):
                    # Blood moon with special styling
                    moon_html = f'&nbsp;&nbsp;<span class="blood-moon"></span> <span style="color: #cc2222;">{moon_phase["name"]}</span>'
                else:
                    moon_html = f'&nbsp;&nbsp;{moon_phase["icon"]} {moon_phase["name"]}'
                date_html += moon_html

            ui.html(date_html, sanitize=False).classes('mt-0 mb-0 ml-4')

            # Holiday display (if current date is a holiday)
            current_holiday = get_current_holiday()
            if current_holiday:
                holiday_text = f"{current_holiday.get('name', '')} - {current_holiday.get('description', '')}"
                ui.label(holiday_text).classes('mt-0 mb-0 ml-4 text-sm')

    # Days count
    ui.label(f'{config.generated_overland_days} days').classes('mt-0 mb-0 ml-4')
    
    # Weather - indented under General
    if config.generated_overland_weather and config.generated_overland_weather.name:
        with ui.row().classes('items-center gap-0 mt-0 mb-0 ml-4'):
            # Parse weather string to emphasize only the name
            weather_str = str(config.generated_overland_weather)
            if '(' in weather_str:
                # Format: "Name (effects)"
                name_part = weather_str.split('(')[0].strip()
                effects_part = '(' + weather_str.split('(', 1)[1]
                ui.html(f'Weather: <span class="emphasis">{name_part}</span> {effects_part}', sanitize=False)
            else:
                # Just the name
                ui.html(f'Weather: <span class="emphasis">{weather_str}</span>', sanitize=False)
            ui.button('🔄', on_click=lambda: (regenerate_individual_weather(), overland_content.refresh())).props('flat dense')
    else:
        ui.label('No weather generated yet').classes('mt-0 mb-0 ml-4 text-gray-500')
    
    # Encounters section
    ui.label('Encounters').classes('text-lg font-bold mt-0 mb-0')
    
    for watch in config.OVERLAND_WATCHES:
        encounter = config.generated_overland_encounters.get(watch)
        if encounter:
            render_encounter(encounter, watch, "overland", overland_content)
    
    # Rest Check section
    ui.label('Rest Check').classes('text-lg font-bold mt-0 mb-0')
    
    if config.generated_overland_rest_info:
        rest_info = config.generated_overland_rest_info
        
        # Rest DCs - indented
        ui.label(f'Rest DCs for {config.selected_overland_season}').classes('font-bold mt-0 mb-0 ml-4')
        rest_dcs = rest_info.get('rest_dcs', [])
        if rest_dcs:
            with ui.column().classes('mt-0 mb-0 ml-8'):
                for item in rest_dcs:
                    ui.label(f"{item.get('camp', '')}  {item.get('dc', '')}").classes('mt-0 mb-0')
        
        # Weather Modifiers (only if exist) - indented
        weather_mods = rest_info.get('weather_modifiers', [])
        if weather_mods:
            ui.label('Weather Modifiers').classes('font-bold mt-0 mb-0 ml-4')
            with ui.column().classes('mt-0 mb-0 ml-8'):
                for mod in weather_mods:
                    # Emphasize the weather effect
                    mod_text = f"{mod.get('description', '')}  {mod.get('modifier', '')}"
                    ui.html(f'<span class="emphasis">{mod_text}</span>', sanitize=False).classes('mt-0 mb-0')
        
        # Situational Modifiers - indented
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
    with ui.row().classes('w-full mt-1 mb-1'):
        zone_select = ui.select(
            options=config.site_zones_list,
            value=config.selected_site_zone,
            label='Site Zone'
        ).classes('flex-1')
        
        zone_select.on('change', lambda e: (setattr(config, 'selected_site_zone', e.value), site_content.refresh()))
    
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
def calendar_content():
    """Refreshable Calendar tab content."""

    # Safety check - should not be called if no calendar
    if not config.calendar_data:
        ui.label('No calendar loaded').classes('text-gray-500')
        return

    # Initialize lunar day if calendar has lunar settings but no lunar_day yet
    if config.calendar_data.get('lunar_cycle_length') and config.calendar_data.get('lunar_day') is None:
        initialize_lunar_day()

    # Get calendar info
    months = config.calendar_data.get('months', [])
    holidays = config.calendar_data.get('holidays', [])
    days_per_week = config.calendar_data.get('days_per_week', 6)
    current_date = config.calendar_data.get('current_date')

    # Build holiday lookup: (month_name, day) -> holiday
    holiday_lookup = {}
    for holiday in holidays:
        key = (holiday.get('month'), holiday.get('day'))
        holiday_lookup[key] = holiday

    # Current date display at top
    date_string = get_calendar_date_string()
    if date_string:
        date_html = date_string

        # Add moon phase if available
        moon_phase = get_moon_phase_info()
        if moon_phase:
            if moon_phase.get('is_blood_moon'):
                moon_html = f'&nbsp;&nbsp;<span class="blood-moon"></span> <span style="color: #cc2222;">{moon_phase["name"]}</span>'
            else:
                moon_html = f'&nbsp;&nbsp;{moon_phase["icon"]} {moon_phase["name"]}'
            date_html += moon_html

        ui.html(date_html, sanitize=False).classes('text-lg font-bold mt-0 mb-0')

    # If current date is a holiday, show holiday info
    current_holiday = get_current_holiday()
    if current_holiday:
        with ui.column().classes('mt-0 mb-1 ml-4 gap-0'):
            ui.html(f'🎉 <span class="emphasis">{current_holiday.get("name", "")}</span>', sanitize=False).classes('mt-0 mb-0')
            ui.label(current_holiday.get('description', '')).classes('mt-0 mb-0 text-sm')

    ui.separator().classes('my-2')

    # Render all month grids
    for month_idx, month in enumerate(months, 1):
        month_name = month.get('name', f'Month {month_idx}')
        days_in_month = month.get('days', 30)

        # Month header
        ui.label(month_name).classes('calendar-month-header')

        # Create grid for this month
        with ui.grid(columns=days_per_week).classes('gap-0'):
            for day in range(1, days_in_month + 1):
                # Determine styling
                is_current = (current_date and
                              current_date.get('month') == month_idx and
                              current_date.get('day') == day)
                is_holiday = (month_name, day) in holiday_lookup

                # Build CSS classes
                btn_classes = 'calendar-day'
                if is_current:
                    btn_classes += ' calendar-day-current'
                if is_holiday:
                    btn_classes += ' calendar-day-holiday'

                # Create day button with closure for correct values
                def make_click_handler(m=month_idx, d=day):
                    def handler():
                        save_calendar_date(m, d)
                        calendar_content.refresh()
                        # Also refresh overland if it's using calendar season
                        overland_content.refresh()
                    return handler

                btn = ui.button(str(day), on_click=make_click_handler()).props('flat dense')
                btn.classes(btn_classes)

                # Add tooltip for holidays
                if is_holiday:
                    holiday_info = holiday_lookup[(month_name, day)]
                    btn.tooltip(holiday_info.get('name', ''))

    # Lunar phase selector (if lunar tracking is enabled)
    if config.calendar_data.get('lunar_cycle_length'):
        moon_phase = get_moon_phase_info()
        current_phase_index = moon_phase['phase_index'] if moon_phase else -1

        with ui.row().classes('items-center gap-1 mt-2 mb-1'):
            ui.label('Lunar Phase:').classes('mr-2')

            # Minus button
            def handle_lunar_minus():
                adjust_lunar_day(-1)
                calendar_content.refresh()
                overland_content.refresh()
            ui.button('−', on_click=handle_lunar_minus).props('flat dense').classes('lunar-phase-btn')

            # Phase icon buttons
            for idx, phase in enumerate(MOON_PHASES):
                def make_phase_handler(phase_idx=idx):
                    def handler():
                        set_lunar_day_to_phase(phase_idx)
                        calendar_content.refresh()
                        overland_content.refresh()
                    return handler

                btn_classes = 'lunar-phase-btn'
                if idx == current_phase_index:
                    btn_classes += ' lunar-phase-current'

                ui.button(phase['icon'], on_click=make_phase_handler()).props('flat dense').classes(btn_classes).tooltip(phase['name'])

            # Plus button
            def handle_lunar_plus():
                adjust_lunar_day(1)
                calendar_content.refresh()
                overland_content.refresh()
            ui.button('+', on_click=handle_lunar_plus).props('flat dense').classes('lunar-phase-btn')

    ui.separator().classes('my-2')

    # Holiday list at bottom
    ui.label('Holidays').classes('text-lg font-bold mt-0 mb-0')

    if holidays:
        with ui.column().classes('mt-0 mb-0 ml-4 gap-0'):
            for holiday in holidays:
                h_name = holiday.get('name', '')
                h_month = holiday.get('month', '')
                h_day = holiday.get('day', '')

                # Check if this is the current holiday
                is_current_holiday = (current_holiday and
                                      current_holiday.get('name') == h_name)

                holiday_text = f'{h_name} - {h_month} {h_day}'

                if is_current_holiday:
                    ui.html(f'<span class="emphasis">{holiday_text}</span>', sanitize=False).classes('mt-0 mb-0')
                else:
                    label = ui.label(holiday_text).classes('mt-0 mb-0')
                    label.tooltip(holiday.get('description', ''))
    else:
        ui.label('No holidays defined').classes('mt-0 mb-0 ml-4 text-gray-500')


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
    
    # Tabs - Calendar tab only shown if calendar is loaded
    with ui.tabs().classes('w-full') as tabs:
        overland_tab = ui.tab('Overland')
        site_tab = ui.tab('Site')
        if config.calendar_data:
            calendar_tab = ui.tab('Calendar')

    with ui.tab_panels(tabs, value=overland_tab).classes('w-full'):
        with ui.tab_panel(overland_tab):
            overland_content()

        with ui.tab_panel(site_tab):
            site_content()

        if config.calendar_data:
            with ui.tab_panel(calendar_tab):
                calendar_content()


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
