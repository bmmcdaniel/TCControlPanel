# Torchcrawl GM Control Panel - Complete Specification

**Version:** 2.3 (NiceGUI + Calendar + Moon Phases + Seasonal Encounters)
**Date:** February 12, 2026
**Framework:** NiceGUI 1.4+
**Language:** Python 3.9+

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Data Models](#3-data-models)
4. [UI Specification](#4-ui-specification)
5. [Logic & Algorithms](#5-logic--algorithms)
6. [Features](#6-features)
7. [Technical Requirements](#7-technical-requirements)
8. [File Structure](#8-file-structure)
9. [Configuration](#9-configuration)
10. [Data Files](#10-data-files)

---

## 1. Overview

### 1.1 Purpose
A game master control panel for the Torchcrawl tabletop RPG system that generates and manages encounters, weather, timers, and rest checks for both overland travel and site-based exploration.

### 1.2 Key Features
- **Overland Mode:** Day-by-day travel with weather, season-weighted encounters, and rest checks
- **Site Mode:** 10-minute turn tracking with encounters (current + 5 future slots) and timers
- **Calendar System:** Optional fantasy calendar with date tracking, holidays, auto-season detection, and moon phases
- **Data-Driven:** All encounters, weather, zones, seasons, and watches loaded from YAML/Excel files
- **Persistent State:** Expansion states preserved when encounters shift
- **Responsive UI:** Ultra-compact spacing, dark mode, emphasis colors

### 1.3 User Experience Goals
- Maximum information density (tight spacing)
- Clear visual hierarchy (indentation, emphasis)
- Minimal clicks (persistent expansion states)
- Professional appearance (consistent styling)
- Comfortable viewing (dark mode support)

---

## 2. Architecture

### 2.1 Framework Stack

```
┌─────────────────────────────────┐
│     NiceGUI (FastAPI + Vue)     │  ← Web Framework
├─────────────────────────────────┤
│   Quasar Components + Tailwind  │  ← UI Components
├─────────────────────────────────┤
│    Python Business Logic        │  ← Game Logic
├─────────────────────────────────┤
│  YAML + Excel Data Sources      │  ← Data Layer
└─────────────────────────────────┘
```

### 2.2 Module Structure

```
app.py                 ← Main UI + Routing
├── models.py         ← Data classes (Encounter, Weather, Timer)
├── config.py         ← Global configuration & state
├── data_loader.py    ← YAML/Excel loading
├── overland_logic.py ← Overland generation & state
├── site_logic.py     ← Site generation & state
├── utils.py          ← Utility functions
└── logger.py         ← Logging system
```

### 2.3 State Management

**Global State (config.py):**
- Generated encounters, weather, timers
- User selections (zone, season, overlay)
- Loaded data (YAML, Excel)

**Session State (app.storage.user):**
- Expansion states (site encounters)
- UI preferences

**Component State:**
- Visibility toggles (expansion)
- Form inputs (timer creation)

---

## 3. Data Models

### 3.1 Encounter

```python
class Encounter:
    name: Optional[str]           # Encounter name (None = no encounter)
    time: Optional[str]           # Time of occurrence
    sparks: List[str]             # Situation prompts (1-N items)
    description: Optional[str]    # Physical description
    habitat: Optional[List[str]]  # Applicable zones
    habitat_notes: Optional[str]  # Special habitat notes
    seasons: Union[str, Dict]     # "Any" or {season: percentage} dict

    def is_encounter() -> bool:
        """Returns True if name is not None"""

    def generate_overland_encounter(zone, overlay, watch, season,
            encounters_data, encounter_by_zone_watch_and_season,
            zones_data, seasons_data):
        """Generate for specific watch period using 4D array with season"""

    def generate_site_encounter(zone, time_slot,
            encounters_data, encounter_by_zone, zones_data):
        """Generate for specific time slot (no season modifier)"""
```

**Source:** `Default Encounters.yaml`

### 3.2 Weather

```python
class Weather:
    name: str                     # Weather name
    effects: List[str]            # Mechanical effects
    
    def __str__() -> str:
        """Returns 'Name' or 'Name (Effect1, Effect2)'"""
    
    def generate_weather(...):
        """Generate based on season probabilities"""
```

**Source:** `Default Weathers.yaml`, `Default Weather By Season.xlsx`

### 3.3 Timer

```python
class Timer:
    name: str                     # Timer description
    remaining_duration: int       # Minutes remaining (can be negative)
    
    def decrement_timer(amount: int = 10) -> str:
        """Decrease by amount, return 'active' or 'expired'"""
    
    def is_expired() -> bool:
        """Returns True if remaining_duration < 0"""
    
    def __str__() -> str:
        """Returns formatted string based on duration:
           - < 0: '⚠️ EXPIRED: {name}'
           - 0-9: 'Current: {name}'
           - >= 10: '{duration} minutes: {name}'
        """
```

**Lifecycle:**
- Created with duration in minutes
- Decrements by 10 each turn
- Labeled "Current:" when 0-9 minutes
- Removed when goes negative

---

## 4. UI Specification

### 4.1 Global Layout

```
┌──────────────────────────────────────────┐
│  Torchcrawl GM Control Panel             │  ← Header (h2)
├──────────────────────────────────────────┤
│  [Overland]  [Site]  [Calendar]          │  ← Tabs (left-aligned, Calendar conditional)
├──────────────────────────────────────────┤
│                                          │
│  Tab Content                             │  ← Scrollable content area
│  (Overland, Site, or Calendar)           │
│                                          │
└──────────────────────────────────────────┘
```

**Conditional Tabs:**
- Overland: Always visible
- Site: Always visible
- Calendar: Only visible when a calendar file is loaded

### 4.2 Colors

**Primary Text:** Default (light gray on dark, dark gray on light)  
**Emphasis Color:** `#F78080` (coral pink)  
**Background:** Auto (follows system dark/light mode preference)

**Emphasis Applied To:**
- Weather names (not effects)
- Overland: All encounter names (not "No Encounter")
- Site: "Current" encounter names only
- Rest Check: Weather modifiers only
- Site: Time minutes (not hours conversion)
- Site: "Current" timer names only
- Calendar: Current month name in date display
- Overland: Current date display (month name only)

### 4.3 Typography

**Headers:**
- Section headers: `text-lg font-bold` (18px, bold)
- Subsection headers: `font-bold` (16px, bold)

**Body:**
- Normal text: Default size, normal weight
- Line height: `1.2` (ultra-tight)
- Font: System default (no monospace)

**Emphasis:**
- Color: `#F78080`
- Weight: `500` (medium)

### 4.4 Spacing

**Ultra-Tight Configuration:**
- Global line-height: `1.2`
- Section header top margin: `0`
- Content top margin: `0`
- Element gaps: `0` (all containers use `gap-0`)
- Button padding: `0.1rem` vertical, `0.3rem` horizontal

**Indentation Hierarchy:**
- Level 0: Section headers (flush left)
- Level 1: Section content (`ml-4` = 1rem)
- Level 2: Sub-items in Rest Check (`ml-8` = 2rem)
- Expansion details: `2em` left margin in HTML

### 4.5 Dark Mode

**Implementation:**
```python
dark = ui.dark_mode()
dark.auto()  # Follow system preference
```

**Behavior:**
- Automatically detects system dark/light mode
- Updates instantly when system changes
- Fallback to light if browser doesn't support

---

## 5. UI Specification (Detailed)

### 5.1 Overland Tab

#### 5.1.1 Configuration Section

**Layout (with calendar date set):**
```
┌─────────────────────────────────┐
│ Current Date: Deepwinter 15 (Winter)  🌒 Waxing Crescent        │
│ Zone: [Dropdown ▼] Overlay: [Dropdown ▼]                        │
│ [Generate] [Reset] [New Day]                                     │
└─────────────────────────────────┘
```

**Layout (without calendar or no date set):**
```
┌─────────────────────────────────┐
│ Zone: [Dropdown ▼] Overlay: [Dropdown ▼] Season: [Dropdown ▼]  │
│ [Generate] [Reset]                                               │
└─────────────────────────────────┘
```

**Elements:**
- Date display: Only shown when calendar has current_date set
  - Month name emphasized in coral pink
  - Format: `<span class="emphasis">{month}</span> {day} ({season})`
- Moon phase display: Only shown when calendar has lunar_day set
  - Shows unicode moon icon + phase name
  - Format: `🌒 Waxing Crescent` (or `🌕 Full Moon`, etc.)
  - Blood Moon: Icon uses layered CSS technique (grayscale + red overlay), text in red
- Zone dropdown: Required, no default
- Overlay dropdown: Optional, "None" default
- Season dropdown: Conditional
  - Shown when no calendar or no current_date set
  - Hidden when calendar date is set (season auto-detected from month)
- Generate button: Triggers `overland_generate()`
- Reset button: Triggers `overland_reset()`
- New Day button: Only shown when calendar date is set
  - Advances calendar by 1 day
  - Triggers `advance_calendar_date(1)` then regenerates

**Styling:**
- Row: `gap-2` (small spacing between dropdowns)
- Buttons: `mt-1` (small top margin)

---

#### 5.1.2 General Section

**Structure:**
```
General
    3 days
    Weather: Clear Skies (Bright sunlight) 🔄
             ^^^^^^^^^^^
             emphasized
```

**Layout:**
```
ui.label('General')              # Section header
    ui.label('X days')           # Indented (ml-4)
    ui.row:                      # Weather row (ml-4)
        ui.html('Weather: ...')  # With emphasis
        ui.button('🔄')          # Regenerate
```

**Weather Format:**
- Parse string to find name vs effects
- Emphasize only name part (before parentheses)
- Button on same line, flush left after weather

**Spacing:**
- Section header: `mt-0 mb-0`
- Days: `mt-0 mb-0 ml-4`
- Weather row: `mt-0 mb-0 ml-4 gap-0`

---

#### 5.1.3 Encounters Section

**Structure:**
```
Encounters
    Dawn: Ankheg 🔄
          ^^^^^^
          emphasized (coral pink)
        Description: 12-foot tall mantis...
        1. The adventuring company...
        2. An ankheg is digging...
    
    Morning: No Encounter 🔄
             (not emphasized)
```

**Layout per Encounter:**
```
ui.row (ml-4):                           # Indentation
    ui.column (gap-0):                   # Outer container
        ui.row (gap-0):                  # Name + button row
            ui.html (clickable)          # Encounter name
            ui.button('🔄')              # Regenerate
        ui.column (gap-0):               # Details container
            ui.html                      # Description
            ui.html (loop)               # Sparks
```

**Encounter Name:**
- Clickable: `cursor: pointer`
- Emphasized: All encounter names (not "No Encounter")
- Format: `{watch}: <span class="emphasis">{name}</span>`

**Expansion Behavior:**
- Click name to toggle details
- Details container initially hidden
- No expansion icon visible
- Overland: State not preserved (always starts collapsed)

**Details Format:**
```html
<div style="margin: 0; padding: 0; margin-left: 2em; line-height: 1.2;">
    Description: {description}
</div>
<div style="margin: 0; padding: 0; margin-left: 2em; margin-bottom: 0.3em; line-height: 1.2;">
    1. {spark}
</div>
```

**Spacing:**
- Outer row: `gap-0 mt-0 mb-0 ml-4`
- Outer column: `gap-0 mt-0 mb-0` + `gap: 0 !important;`
- Name row: `gap-0 mt-0 mb-0`
- Details column: `gap-0 mt-0 mb-0` + `padding: 0; margin: 0; gap: 0;`
- Last spark: `margin-bottom: 0.3em`

**Watches (loaded dynamically from Default Watches.yaml):**

Watch periods are not hardcoded. They are read from the watches YAML file at startup and flow dynamically throughout the application via `config.watches_list`. The default set is:
1. Dawn
2. Morning
3. Afternoon
4. Dusk
5. Early Night
6. Late Night

---

#### 5.1.4 Rest Check Section

**Structure:**
```
Rest Check
    Rest DCs for Spring
        Unsheltered Camp  DC 15
        Sheltered Camp  DC 10
    Weather Modifiers
        Light precipitation without shelter  -5
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        emphasized (entire line)
    Situational Modifiers
        Heavy rain  +5
        (not emphasized)
```

**Layout:**
```
ui.label('Rest Check')                    # Section header
    ui.label('Rest DCs for {season}')     # Subsection (ml-4)
        ui.column (ml-8):                 # Items (double indent)
            ui.label (each DC)
    ui.label('Weather Modifiers')         # Subsection (ml-4)
        ui.column (ml-8):                 # Items (double indent)
            ui.html (each, emphasized)    # Full line emphasis
    ui.label('Situational Modifiers')     # Subsection (ml-4)
        ui.column (ml-8):                 # Items (double indent)
            ui.label (each)               # Not emphasized
```

**Emphasis:**
- Only Weather Modifiers
- Entire line: `<span class="emphasis">{description}  {modifier}</span>`

**Source:** `Default Rest Info.yaml`

---

### 5.2 Site Tab

#### 5.2.1 Configuration Section

**Layout:**
```
┌─────────────────────────────────┐
│ Zone: [Dropdown ▼]              │
│ [Generate] [Reset]               │
└─────────────────────────────────┘
```

**Elements:**
- Zone dropdown: Required, no default
- Generate button: Triggers `site_generate()`
- Reset button: Triggers `site_reset()`

---

#### 5.2.2 Controls Section

**Layout:**
```
┌─────────────────────────────────┐
│ [New Turn] [Regenerate All]     │
└─────────────────────────────────┘
```

**Buttons:**
- New Turn: Advances time by 10 minutes, shifts encounters, decrements timers
- Regenerate All: Regenerates current encounter only

**Behavior:**
- Both trigger `site_content.refresh()`

---

#### 5.2.3 General Section

**Structure:**
```
General
    170 minutes (2 hours 50 minutes)
    ^^^^^^^^^^^
    emphasized
```

**Layout:**
```
ui.label('General')                       # Section header
    ui.html('X minutes (H hours...)')     # Indented (ml-4)
```

**Format:**
- Parse string to separate minutes from hours
- Emphasize only "X minutes" part
- Keep "(H hours M minutes)" normal

**Conversion:**
- <= 50 minutes: "X minutes"
- > 50 minutes: "X minutes (H hours M minutes)"

---

#### 5.2.4 Timers Section

**Structure (form collapsed):**
```
Timers➕
    Current: Torch expires 🔄
             ^^^^^^^^^^^^^
             emphasized
    10 minutes: Poison effect ❌
    (not emphasized)
```

**Structure (form expanded):**
```
Timers➖
    [Timer Name] [Duration] [Add Timer] [Cancel]
    Current: Torch expires 🔄
    10 minutes: Poison effect ❌
```

**Layout:**
```
ui.row (gap-0):                          # Header row
    ui.label('Timers')                   # Section header
    ui.button('➕' or '➖')               # Toggle button (shows state)

[Timer Form - conditional]               # If show_timer_form = True
    ui.row (ml-4):
        ui.input('Timer Name')
        ui.number('Duration')
        ui.button('Add Timer')
        ui.button('Cancel')

ui.column (ml-4):                        # Timer list
    ui.row (each timer):
        ui.html/ui.label                 # Timer string
        ui.button('❌')                   # Delete
```

**Timer Display:**
- < 0: "⚠️ EXPIRED: {name}" (never shown - removed)
- 0-9: "Current: {name}" (emphasized)
- >= 10: "{duration} minutes: {name}" (not emphasized)

**Emphasis:**
- Only timer names that start with "Current:"
- Format: `Current: <span class="emphasis">{name}</span>`

**Spacing:**
- Header row: `gap-0 mt-0 mb-0`
- Timer form row: `gap-2 mt-0 mb-0 ml-4`
- Timer list: `mt-0 mb-0 ml-4 gap-0`
- Each timer row: `gap-0 mt-0 mb-0`

**Timer Form:**
- **Default state:** Collapsed (hidden) on page load
- Stored in `app.storage.user['show_timer_form']`
- Initialized to `False` in `index()` on each page load
- Toggled by button in header row
- **Button icon:**
  - Shows `➖` when form is expanded (visible)
  - Shows `➕` when form is collapsed (hidden)
- Fields: name (text), duration (number, default 60)
- Buttons: Add Timer (creates), Cancel (hides form)

---

#### 5.2.5 Encounters Section

**Structure:**
```
Encounters
    Current: Barrow-Wight 🔄
             ^^^^^^^^^^^^
             emphasized (coral pink)
        Description: Corpse-like humanoid...
        1. The adventuring company...
    
    10 minutes: Ankheg 🔄
                (not emphasized)
    
    20 minutes: No Encounter 🔄
```

**Layout:** Same as Overland encounters

**Differences from Overland:**
- **Emphasis:** Only "Current" encounter names emphasized
- **Slots:** 6 total (Current, 10, 20, 30, 40, 50 minutes)
- **Persistence:** Expansion states preserved when encounters shift

**Expansion State Persistence:**
- Stored in `app.storage.user['site_expansions']`
- Dictionary: `{slot_label: boolean}`
- Shifts along with encounters on "New Turn"
- Example:
  ```
  Turn 1: "20 minutes" expanded
  Turn 2: "10 minutes" expanded (same encounter)
  Turn 3: "Current" expanded (same encounter)
  ```

**New Turn Behavior:**
1. Shift expansion states: `new["Current"] = old["10 minutes"]`, etc.
2. Shift encounters: `new["Current"] = old["10 minutes"]`, etc.
3. New "50 minutes" encounter: expansion = False

---

### 5.3 Calendar Tab

**Conditional Display:** Only visible when a calendar file is loaded (configured in Default Data Files.yaml)

#### 5.3.1 Calendar Header

**Structure:**
```
Calendar: Torchcrawl Standard Calendar
A simple 10-month fantasy calendar with 300 days per year

Current Date: Deepwinter 15 (Winter)  🌒 Waxing Crescent
              ^^^^^^^^^^
              emphasized (coral pink)

Lunar Phase: [-] 🌑 🌒 🌓 🌔 🌕 🌖 🌗 🌘 [+]
```

**Layout:**
```
ui.label(calendar_name)              # Calendar name (bold)
ui.label(description)                # Calendar description
ui.html(date_string)                 # Current date with emphasis + moon phase
```

**Date Display Modes:**
- **Date set:** `<span class="emphasis">{month}</span> {day} ({season})  {moon_icon} {phase_name}`
- **No date set:** "No date set - set date via calendar below"
- **Blood Moon:** Moon icon uses CSS filter, "Blood Moon" text in red

#### 5.3.2 Lunar Phase Selector

**Structure:**
```
Lunar Phase: [-] 🌑 🌒 🌓 🌔 🌕 🌖 🌗 🌘 [+]
```

**Layout:**
```
ui.row:
    ui.label("Lunar Phase:")
    ui.button("−")                   # Decrease lunar_day
    for phase in phases:
        ui.button(phase_icon)        # Set to this phase
    ui.button("+")                   # Increase lunar_day
```

**Behavior:**
- **Phase icon buttons:** Click to set lunar_day to the start of that phase
- **[-] button:** Decrease lunar_day by 1 (wraps from 1 to lunar_cycle_length)
- **[+] button:** Increase lunar_day by 1 (wraps from lunar_cycle_length to 1)
- Changes are saved to calendar file immediately
- If setting to full moon phase, blood moon is rolled

**Phase Icons:**
| Phase | Icon | Days (27-day cycle) |
|-------|------|---------------------|
| New Moon | 🌑 | ~3-4 days |
| Waxing Crescent | 🌒 | ~3-4 days |
| First Quarter | 🌓 | ~3-4 days |
| Waxing Gibbous | 🌔 | ~3-4 days |
| Full Moon | 🌕 | ~3-4 days |
| Waning Gibbous | 🌖 | ~3-4 days |
| Last Quarter | 🌗 | ~3-4 days |
| Waning Crescent | 🌘 | ~3-4 days |

**Blood Moon Display:**
- Uses layered CSS technique for red-tinted moon icon
- Text "Blood Moon" displayed in red (#cc2222)

**Blood Moon CSS (layered technique):**
```css
.blood-moon {
  position: relative;
  display: inline-block;
  width: 1em;
  height: 1em;
  filter: contrast(1.4);
}

/* Bottom layer: desaturated moon */
.blood-moon::before {
  content: "🌕";
  position: absolute;
  top: 0;
  left: 0;
  filter: grayscale(0.95);
  z-index: 1;
}

/* Top layer: red tint overlay */
.blood-moon::after {
  content: "🌕";
  position: absolute;
  top: 0;
  left: 0;
  z-index: 2;
  color: transparent;
  -webkit-background-clip: text;
  background-clip: text;
  background-color: rgba(255, 0, 0, 0.5);
  pointer-events: none;
}
```

#### 5.3.3 Holiday Display

**Structure (when current date is a holiday):**
```
🎉 Today is Midwinter Festival
   A week-long celebration marking the darkest point of winter...
```

**Layout:**
```
if get_current_holiday():
    ui.label(f"🎉 Today is {holiday['name']}")    # Bold
    ui.label(holiday['description'], ml-4)         # Indented
```

#### 5.3.4 Month Grid

**Structure:**
```
── Deepwinter (Winter) ──────────────────
   [ 1] [ 2] [ 3] [ 4] [ 5] [ 6]
   [ 7] [ 8] [ 9] [10] [11] [12]
   [13] [14] [15] [16] [17] [18]    ← 15 highlighted if current
   [19] [20] [21] [22] [23] [24]
   [25] [26] [27] [28] [29] [30]

── Latewinter (Winter) ──────────────────
   [ 1] [ 2] [ 3] [ 4] [ 5] [ 6]
   ...
```

**Layout per month:**
```
ui.separator                              # Visual divider
ui.label(f"{month_name} ({season})")      # Month header (bold)
ui.grid(columns=days_per_week):           # Grid with configured columns
    for day in range(1, days+1):
        ui.button(str(day))               # Clickable day button
```

**Day Button Behavior:**
- Click any day to set current date to that month/day
- Calls `save_calendar_date(month_index, day)`
- Refreshes calendar display

**Day Button Styling:**
- **Normal days:** Default button style
- **Current date:** Highlighted with coral pink background
- **Holiday days:** Could be indicated with different styling (optional)

**Grid Configuration:**
- Columns determined by `calendar_data['days_per_week']` (default 6)
- Rows automatically calculated based on days in month

#### 5.3.5 Calendar Data Requirements

**Required fields in calendar YAML:**
- `name`: Calendar display name
- `description`: Calendar description
- `days_per_week`: Number of days per week (for grid columns)
- `current_date`: Object with `month` (1-based) and `day`, or null
- `months`: List of month objects with `name`, `days`, `season`
- `holidays`: List of holiday objects with `name`, `description`, `month` (name), `day`

**Lunar phase fields (optional):**
- `lunar_cycle_length`: Days in lunar cycle (e.g., 27)
- `blood_moon_chance`: Percent chance of blood moon on full moon (e.g., 10)
- `lunar_day`: Current position in cycle (1 to lunar_cycle_length), or null
- `is_blood_moon`: Whether current full moon is a blood moon (true/false)

### 5.4 CSS Styling

#### 5.3.1 Global CSS

```css
/* Emphasis color */
.emphasis {
    color: #F78080 !important;
    font-weight: 500;
}

/* Ultra-tight spacing */
.nicegui-content {
    padding-top: 0.5rem !important;
    line-height: 1.2 !important;
}

/* Minimal field spacing */
.q-field {
    margin-bottom: 0.1rem !important;
}

/* No expansion spacing */
.q-expansion-item__container {
    margin-bottom: 0rem !important;
}

/* Remove expansion indentation */
.q-expansion-item {
    margin-left: 0 !important;
    padding-left: 0 !important;
    margin-bottom: 0 !important;
}

/* Compact q-items */
.q-item {
    padding-left: 0 !important;
    min-height: 0 !important;
    padding-top: 0.1rem !important;
    padding-bottom: 0.1rem !important;
}

/* Hide expansion icon */
.q-expansion-item .q-item__section--side {
    display: none !important;
}

/* Left-align tabs */
.q-tabs,
.q-tabs__content {
    justify-content: flex-start !important;
}

/* Normal case for tabs */
.q-tab__label {
    text-transform: none !important;
}

/* Compact buttons */
.q-btn {
    min-height: 1.5rem !important;
    padding: 0.1rem 0.3rem !important;
}

/* Reset text margins */
p, div {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}
```

#### 5.3.2 Inline Styles

**Used for maximum specificity on containers:**

```python
# Parent columns (encounters)
.style('gap: 0 !important;')

# Details containers
.style('padding: 0 !important; margin: 0 !important; gap: 0 !important;')

# HTML divs
style="margin: 0; padding: 0; margin-left: 2em; line-height: 1.2;"
```

---

## 6. Logic & Algorithms

### 6.1 Overland Generation

#### 6.1.1 overland_generate()

**Algorithm:**
```
1. Get user selections (zone, overlay, season)
2. Validate selections (all required fields)
3. Generate days (random 1-6)
4. Generate weather for season
5. Generate encounters (one per watch from config.watches_list)
6. Generate rest info for season
7. Log completion
```

#### 6.1.2 Encounter Generation (Overland)

**Algorithm for each watch:**
```
1. Determine active zone:
   - If overlay exists: 50% chance overlay, 50% base zone
   - If no overlay: always base zone

2. Get encounter_chance from active zone data

3. Apply season encounter_modification:
   - encounter_chance = zone_encounter_chance × season_encounter_modification
   - Example: Mountains (18%) in Winter (40%) = 7.2% effective chance

4. Roll for encounter:
   - Random 0.0-1.0
   - If roll <= encounter_chance: generate encounter
   - Else: no encounter (name = None)

5. If encounter:
   a. Get weight table from 4D array for (active_zone, watch, season)
   b. Weights already incorporate per-encounter season percentages
   c. Weighted random selection from encounters with weight > 0
   d. Populate: name, description, habitat, all sparks

6. Set encounter.time = watch
```

**Source Tables:**
- Encounter chance: `zones_data[zone]['encounter_chance']` × `seasons_data[season]['encounter_modification']`
- Weights: `encounter_by_zone_watch_and_season[encounter, zone, watch, season]`

**Two-Level Season Effect:**
- **Level 1 (encounter_modification):** From `Default Seasons.yaml`. Adjusts whether ANY encounter occurs at all. Applied multiplicatively to the zone's base encounter_chance. Overland only.
- **Level 2 (per-encounter season %):** From `Default Encounters.yaml` `season` field. Adjusts the relative probability of WHICH encounter is selected. Baked into the 4D array at startup. An encounter with `Winter: 0%` can never appear in Winter.

---

### 6.2 Site Generation

#### 6.2.1 site_generate()

**Algorithm:**
```
1. Get user selection (zone)
2. Validate selection
3. Reset time to 0
4. Clear timers
5. Clear expansion states
6. Generate initial encounters:
   - Current: empty (no encounter)
   - 10-50 minutes: generated (5 encounters)
7. Log completion
```

#### 6.2.2 Encounter Generation (Site)

**Algorithm for each slot:**
```
1. Get encounter_chance from zone

2. Roll for encounter (same as overland)

3. If encounter:
   a. Get weight table for zone (time_slot ignored)
   b. Weighted random selection
   c. Populate: name, description, habitat
   d. Generate 1-4 sparks

4. Set encounter.time = time_slot
```

**Note:** Site encounters don't use watch-specific weights (no time_slot dimension)

---

### 6.3 Site Turn Advancement

#### 6.3.1 site_new_turn()

**Algorithm:**
```
1. Increment time by 10 minutes

2. Update timers:
   a. Decrement each by 10
   b. Remove timers where remaining_duration < 0

3. Shift expansion states:
   old_expansions = get from storage
   new_expansions["Current"] = old_expansions["10 minutes"]
   new_expansions["10 minutes"] = old_expansions["20 minutes"]
   ... (continue pattern)
   new_expansions["50 minutes"] = False
   Save new_expansions to storage

4. Shift encounters:
   new["Current"] = old["10 minutes"]
   new["10 minutes"] = old["20 minutes"]
   ... (continue pattern)

5. Generate new "50 minutes" encounter

6. Log advancement
```

**Key:** Expansion states shift BEFORE encounters to maintain sync

---

### 6.4 Timer Management

#### 6.4.1 Timer Lifecycle

**States:**
```
Created (X minutes)
    ↓ decrement by 10
Active (10+ minutes)     → Display: "X minutes: Name"
    ↓ decrement by 10
Current (0-9 minutes)    → Display: "Current: Name" (emphasized)
    ↓ decrement by 10
Expired (< 0 minutes)    → Removed from list
```

#### 6.4.2 Timer Display Logic

```python
def __str__(self) -> str:
    if self.remaining_duration < 0:
        return f"⚠️ EXPIRED: {self.name}"  # Never displayed
    elif 0 <= self.remaining_duration < 10:
        return f"Current: {self.name}"  # Emphasized
    else:
        return f"{self.remaining_duration} minutes: {self.name}"
```

#### 6.4.3 Timer Removal

**Condition:** `remaining_duration < 0`

**Implementation:**
```python
config.generated_site_timers = [
    t for t in config.generated_site_timers 
    if t.remaining_duration >= 0
]
```

**Timing:** After decrement in `site_new_turn()`

---

## 7. Features

### 7.1 Overland Mode Features

**Generation:**
- ✅ Random days (1-6)
- ✅ Weather by season
- ✅ Encounters per day (one per watch, watches loaded from file)
- ✅ 50/50 overlay system
- ✅ Rest checks with DCs and modifiers
- ✅ Season encounter_modification adjusts base encounter chance
- ✅ Per-encounter season percentages weight which encounter is selected
- ✅ 4D encounter probability array [Encounter, Zone, Watch, Season] precomputed at startup

**Regeneration:**
- ✅ Individual weather regeneration
- ✅ Individual encounter regeneration
- ✅ Full reset

**Display:**
- ✅ Expandable encounters (click name)
- ✅ Emphasized encounter names
- ✅ Emphasized weather names
- ✅ Emphasized weather modifiers in Rest Check
- ✅ Clear hierarchical layout

---

### 7.2 Site Mode Features

**Generation:**
- ✅ 6 encounter slots (Current + 5 future)
- ✅ Current always empty initially
- ✅ Future slots generated

**Turn Management:**
- ✅ New Turn: advances time, shifts encounters, updates timers
- ✅ Regenerate All: regenerates current encounter only
- ✅ Individual encounter regeneration
- ✅ Full reset

**Timers:**
- ✅ Add timer (name + duration)
- ✅ Auto-decrement on new turn
- ✅ "Current:" label for 0-9 minutes
- ✅ Auto-removal when negative
- ✅ Manual deletion

**Expansion State Persistence:**
- ✅ Remembers which encounters are expanded
- ✅ Shifts states along with encounters
- ✅ Survives turn advancement
- ✅ Cleared on reset

**Display:**
- ✅ Expandable encounters (click name)
- ✅ Emphasized "Current" encounters only
- ✅ Emphasized "Current" timers only
- ✅ Emphasized time minutes (not hours)
- ✅ Clear hierarchical layout

---

### 7.3 Calendar Features

**Operating Modes:**
- ✅ No calendar (no calendar_file configured)
- ✅ Calendar without date (calendar loaded, current_date: null)
- ✅ Calendar with date (calendar loaded, current_date set)

**Calendar Tab:**
- ✅ Calendar name and description display
- ✅ Current date display with month emphasis
- ✅ Holiday display for current date
- ✅ Visual month grid with clickable days
- ✅ Grid columns based on days_per_week
- ✅ Click day to set current date
- ✅ Current date highlighted in grid
- ✅ Lunar phase selector with [-] icons [+] buttons

**Moon Phase System:**
- ✅ 8 phases: New Moon, Waxing Crescent, First Quarter, Waxing Gibbous, Full Moon, Waning Gibbous, Last Quarter, Waning Crescent
- ✅ Unicode icons: 🌑 🌒 🌓 🌔 🌕 🌖 🌗 🌘
- ✅ Configurable lunar cycle length (default 27 days)
- ✅ Phases roughly equal duration
- ✅ Lunar day advances with calendar day
- ✅ Blood moon chance on full moon (configurable, default 10%)
- ✅ Blood moon result saved to file
- ✅ Blood moon icon with red CSS filter
- ✅ Manual lunar phase adjustment via selector

**Overland Integration:**
- ✅ Date display when calendar date set
- ✅ Moon phase display next to date
- ✅ Auto-season detection from current month
- ✅ Conditional Season dropdown (hidden when auto-detected)
- ✅ New Day button to advance calendar and lunar day

**Data Persistence:**
- ✅ Current date saved to calendar YAML file
- ✅ Lunar day saved to calendar YAML file
- ✅ Blood moon status saved to calendar YAML file
- ✅ Date persists across application restarts
- ✅ Calendar file path configurable in Default Data Files.yaml

---

### 7.4 Universal Features

**UI:**
- ✅ Dark mode (auto-detects system preference)
- ✅ Ultra-tight spacing (maximum density)
- ✅ Consistent indentation hierarchy
- ✅ Flush-left button alignment
- ✅ No gaps between encounter names and details
- ✅ Clickable encounter names (no separate expand icon)

**Data:**
- ✅ YAML for encounters, weather, zones, seasons, watches, rest info
- ✅ Excel for probabilities (weather by season, encounters by zone)
- ✅ Weighted random selection
- ✅ Human-readable, editable data files
- ✅ All dimension sizes (encounters, zones, watches, seasons) set dynamically from data files

**Code:**
- ✅ Modular architecture (separate logic files)
- ✅ Logging system
- ✅ Type hints
- ✅ Comprehensive documentation

---

## 8. Technical Requirements

### 8.1 Dependencies

```txt
nicegui>=1.4.0
pyyaml>=6.0
openpyxl>=3.0.0
xarray>=2023.0.0
pandas>=2.0.0
```

### 8.2 Python Version

**Minimum:** Python 3.9  
**Recommended:** Python 3.11+

### 8.3 Browser Compatibility

**Supported:**
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

**Features requiring modern browser:**
- Dark mode auto-detection (`prefers-color-scheme`)
- CSS Grid/Flexbox
- ES6 JavaScript

### 8.4 System Requirements

**Minimum:**
- 512 MB RAM
- 50 MB disk space
- 1024x768 display

**Recommended:**
- 1 GB RAM
- 100 MB disk space
- 1280x720 display

### 8.5 Performance Targets

- **Startup time:** < 2 seconds
- **Page load:** < 1 second
- **Generation time:** < 100ms per encounter
- **Memory usage:** < 50 MB
- **CPU usage:** < 5% idle

---

## 9. File Structure

```
torchcrawl_nicegui/
├── app.py                          # Main application (376 lines)
├── config.py                       # Global configuration
├── models.py                       # Data classes (372 lines)
├── data_loader.py                  # YAML/Excel loading
├── overland_logic.py              # Overland generation logic
├── site_logic.py                  # Site generation logic (288 lines)
├── utils.py                       # Utility functions
├── logger.py                      # Logging system
├── requirements.txt               # Python dependencies
├── README.md                      # User documentation
├── CHANGELOG.md                   # Version history
├── logs/                          # Runtime logs (created on first run)
│   └── TCControlPanel.log
└── Data/                          # Data files
    ├── Default Data Files.yaml    # Configuration for data file paths
    ├── Default Encounters.yaml
    ├── Default Seasons.yaml       # Season definitions with encounter_modification
    ├── Default Watches.yaml       # Watch period definitions
    ├── Default Weathers.yaml
    ├── Default Zones.yaml
    ├── Default Rest Info.yaml
    ├── Default Calendar.yaml      # Optional calendar file
    ├── Default Encounters By Zone.xlsx
    └── Default Weather By Season.xlsx
```

### 9.1 File Responsibilities

**app.py:**
- NiceGUI application setup
- UI rendering (tabs, sections, components)
- Event handlers (button clicks, toggles)
- CSS styling
- Dark mode configuration

**models.py:**
- Encounter class (generation methods)
- Weather class (generation method)
- Timer class (lifecycle methods)

**config.py:**
- Global state variables
- Constants (time slots)
- Loaded data storage (including dynamically loaded watches and seasons lists)

**data_loader.py:**
- YAML file parsing (encounters, seasons, watches, zones, weathers, rest info, calendar)
- Excel file parsing (with openpyxl)
- xarray DataArray creation (4D encounter array, 2D weather array)
- `load_seasons_file()`: Load season definitions and encounter_modification values
- `load_watches_file()`: Load watch period names dynamically
- `generate_encounter_by_zone_watch_and_season()`: Build 4D encounter probability array
- `load_calendar_file()`: Load calendar data (optional)
- `save_calendar_date()`: Save current date to calendar YAML
- Error handling for missing files
- Data validation across all loaded files

**overland_logic.py:**
- `overland_generate()`: Full generation
- `overland_reset()`: Clear state
- `regenerate_individual_overland_encounter()`: Single encounter
- `regenerate_individual_weather()`: Weather only

**site_logic.py:**
- `site_generate()`: Full generation
- `site_reset()`: Clear state
- `site_new_turn()`: Advance time + shift
- `site_add_timer()`: Create timer
- `site_delete_timer()`: Remove timer
- `regenerate_individual_site_encounter()`: Single encounter

**utils.py:**
- `format_time_display()`: Convert minutes to readable format
- `verbose_print()`: Debug output
- `get_calendar_date_string()`: Format current calendar date for display
- `get_current_season()`: Get season from current calendar month
- `advance_calendar_date()`: Advance calendar date by N days
- `get_current_holiday()`: Get holiday for current date if any

**logger.py:**
- Rotating file handler
- Log formatting
- Log level configuration

---

## 10. Configuration

### 10.1 Constants and Dynamic Lists (config.py)

```python
# Constants (hardcoded)
SITE_TIME_SLOTS = [
    "Current", "10 minutes", "20 minutes",
    "30 minutes", "40 minutes", "50 minutes"
]

# Dynamic lists (loaded from YAML files at startup)
seasons_list: List[str] = []           # From Default Seasons.yaml (e.g., ["Spring", "Summer", "Autumn", "Winter"])
watches_list: List[str] = []           # From Default Watches.yaml (e.g., ["Dawn", "Morning", ...])
watches_key_list: List[str] = []       # Lowercase keys derived from watches_list (e.g., ["dawn", "morning", ...])

# Season data
seasons_data: Dict[str, Dict] = {}    # Season name -> {encounter_modification: "85%"}
                                       # encounter_modification adjusts overland encounter chance

# File paths (loaded from Default Data Files.yaml)
datafile_file: str = "Data/Default Data Files.yaml"  # Master config
encounters_file: str = ""
seasons_file: str = ""
watches_file: str = ""
zones_file: str = ""
weathers_file: str = ""
restinfo_file: str = ""
encounter_by_zone_file: str = ""
weather_by_season_file: str = ""
calendar_file: str = ""
```

**Note:** Watch periods are NO LONGER hardcoded. The former `OVERLAND_WATCHES` constant has been replaced by `watches_list`, which is loaded dynamically from the watches YAML file. This allows watch periods to be customized per campaign.

### 10.2 State Variables (config.py)

```python
# User selections
selected_overland_zone: Optional[str] = None
selected_overland_overlay: Optional[str] = None
selected_overland_season: Optional[str] = None
selected_site_zone: Optional[str] = None

# Generated content
generated_overland_days: int = 0
generated_overland_weather: Optional[Weather] = None
generated_overland_encounters: Dict[str, Encounter] = {}
generated_overland_rest_info: Optional[Dict] = None

generated_site_time: int = 0
generated_site_encounters: Dict[str, Encounter] = {}
generated_site_timers: List[Timer] = []

# Loaded data from YAML
encounters_data: Dict = {}             # Encounter name -> {description, habitat, sparks, watch, season}
weathers_data: Dict = {}               # Weather name -> {effects}
zones_data: Dict = {}                  # Zone name -> {types, encounter_chance}
restinfo_data: Dict = {}               # Rest check tables and modifiers
seasons_data: Dict = {}                # Season name -> {encounter_modification}

# xarray DataArrays (multi-dimensional labeled arrays)
encounter_by_zone: xr.DataArray = None                    # 2D: [Encounter, Zone] - for site encounters
encounter_by_zone_watch_and_season: xr.DataArray = None   # 4D: [Encounter, Zone, Watch, Season] - for overland
weather_by_season: xr.DataArray = None                    # 2D: [Weather, Season]

# Calendar data (optional feature)
calendar_file: str = ""                   # Path to calendar file (from Default Data Files.yaml)
calendar_data: Optional[Dict] = None      # Full calendar structure from YAML (includes current_date)
calendar_month_lookup: Dict[str, int] = {}  # Month name -> 1-based index for quick lookups
```

**4D Encounter Array (`encounter_by_zone_watch_and_season`):**
- Dimensions: `[Encounter, Zone, Watch, Season]`
- All dimension sizes are set dynamically from data files:
  - **Encounter:** Names from `Default Encounters.yaml` (authoritative list)
  - **Zone:** Column headers from `Default Encounters By Zone.xlsx`
  - **Watch:** Names from `Default Watches.yaml`
  - **Season:** Names from `Default Seasons.yaml`
- Cell value = `zone_weight × watch_percentage × season_percentage`
- Encounters in the YAML but not in the Excel get zone_weight = 0 (never selected)
- Built once at startup by `generate_encounter_by_zone_watch_and_season()`

---

## 11. Data Files

### 11.1 Default Encounters.yaml

**Format:**
```yaml
encounters:
  - name: Ankheg
    description: "12-foot tall mantis-like insect; serrated arms; mandibles"
    habitat: [Meadows, Rolling Hills]
    habitat_notes: "Prefers dry and sandy plains with dirt suitable for burrowing."
    watch: {dawn: 15%, morning: 30%, afternoon: 30%, dusk: 15%, early night: 5%, late night: 5%}
    season: {Spring: 80%, Summer: 100%, Autumn: 60%, Winter: 0%}
    sparks:
      - "The adventuring company comes across the crumbling lip of a hole"
      - "An ankheg is digging a new pit-burrow"
      - "The ankheg is fleeing from a land shark"
```

**Fields:**
- `name`: String (required) - Encounter name
- `description`: String (optional) - Physical description
- `habitat`: List[String] (required) - Applicable zone names
- `habitat_notes`: String (optional) - Special habitat notes
- `watch`: Dict (required) - Watch period percentages as `{key: "X%"}`. Keys are lowercase watch names matching the watches file. Percentages control relative probability during each watch period.
- `season`: Dict or String (required) - Season percentages. Two formats:
  - Dict: `{Spring: 100%, Summer: 80%, Autumn: 100%, Winter: 80%}` — per-season percentage
  - String: `All 100%` — shorthand for all seasons at the specified percentage
  - Missing/null treated as all 100%
- `sparks`: List[String] (required, 1-N items) - Situation prompts

**Season Percentage Effect:** Multiplied into the 4D array at startup. An encounter with `Winter: 0%` will have weight 0 for all zones/watches in Winter and can never be selected. An encounter with `Winter: 50%` will be half as likely in Winter compared to a season where it has 100%.

**Naming Convention:** Descriptive, proper case

---

### 11.2 Default Weathers.yaml

**Format:**
```yaml
weathers:
  - name: "Clear Skies"
    effects:
      - "Bright sunlight"
  - name: "Gentle Rains"
    effects:
      - "Light Precipitation"
```

**Fields:**
- `name`: String (required) - Weather name
- `effects`: List[String] (required, 0-N items) - Mechanical effects

**Display:**
- 0 effects: "Name"
- 1+ effects: "Name (Effect1, Effect2, ...)"

---

### 11.3 Default Zones.yaml

**Format:**
```yaml
zones:
  - name: Meadows
    types: [Overland]
    encounter_chance: 10%

  - name: Roads
    types: [Overlay]
    encounter_chance: 20%

  - name: Settlements
    types: [Site]
    encounter_chance: 18%

  - name: Ruins
    types: [Overlay, Site]
    encounter_chance: 25%
```

**Fields:**
- `name`: String (required) - Zone name
- `types`: List[String] (required) - Zone categories: `Overland`, `Overlay`, and/or `Site`
- `encounter_chance`: String (required) - Base percent chance of encounter (e.g., "18%"). For overland zones, this is further modified by the season's `encounter_modification`.

---

### 11.4 Default Rest Info.yaml

**Format:**
```yaml
rest_checks:
  spring:
    rest_dcs:
      - camp: "Unsheltered Camp"
        dc: "DC 15"
      - camp: "Sheltered Camp"
        dc: "DC 10"
    weather_modifiers:
      - description: "Light precipitation without shelter"
        modifier: "-5"
    situational_modifiers:
      - situation: "Heavy rain"
        modifier: "+5"
```

**Structure:**
- By season (spring, summer, fall, winter)
- Three subsections: rest_dcs, weather_modifiers, situational_modifiers

**Display:**
- Only Weather Modifiers are emphasized (coral pink)

---

### 11.5 Default Encounters By Zone.xlsx

**Format:**
```
| Encounter       | Meadows | Rolling Hills | Mountains | Roads | Settlements | ... |
|-----------------|---------|---------------|-----------|-------|-------------|-----|
| Air Elemental   | 0       | 0             | 1         | 0     | 0           | ... |
| Ankheg          | 1       | 1             | 0         | 0     | 0           | ... |
```

**Dimensions:**
- Rows: Encounter names (subset of encounters in Default Encounters.yaml)
- Columns: Zone names (must match Default Zones.yaml)
- Values: Integer weights (0 = never appears in zone, higher = more likely)

**Relationship to 4D Array:**
This Excel file provides the **zone_weight** component of the 4D array. The encounter list in the YAML is authoritative — encounters that appear in the YAML but not in this Excel file will have zone_weight = 0 for all zones (effectively never selected). The zone_weight is multiplied by watch_percentage (from encounter YAML) and season_percentage (from encounter YAML) to produce the final 4D array values.

**Note:** This file provides base zone weights used by both overland (via 4D array) and site (via 2D array) encounter generation. Watch and season modifiers are applied only for overland.

---

### 11.6 Default Weather By Season.xlsx

**Format:**
```
| Weather       | Spring | Summer | Fall | Winter |
|---------------|--------|--------|------|--------|
| Clear Skies   | 30     | 40     | 20   | 10     |
| Gentle Rains  | 40     | 30     | 30   | 20     |
| Blizzard      | 0      | 0      | 5    | 40     |
```

**Dimensions:**
- Rows: Weather names (must match Weathers.yaml)
- Columns: Season names
- Values: Integer weights (0 = never, higher = more likely)

---

### 11.7 Default Seasons.yaml

**Format:**
```yaml
seasons:
  - name: Spring
    encounter_modification: 85%

  - name: Summer
    encounter_modification: 100%

  - name: Autumn
    encounter_modification: 85%

  - name: Winter
    encounter_modification: 40%
```

**Fields:**
- `name`: String (required) - Season name. Must match season names used in encounters YAML, weather Excel, rest info, and calendar months.
- `encounter_modification`: String (required) - Percentage modifier applied to zone encounter_chance for overland encounters. "100%" means no modification; "40%" means encounters are 40% as likely.

**Purpose:** Defines the authoritative list of seasons and controls how encounter frequency varies by season. The season names from this file populate `config.seasons_list`. The `encounter_modification` is applied multiplicatively to a zone's `encounter_chance` when generating overland encounters.

**Example:** Mountains zone has `encounter_chance: 18%`. In Winter (`encounter_modification: 40%`), the effective encounter chance is `18% × 40% = 7.2%`.

---

### 11.8 Default Watches.yaml

**Format:**
```yaml
watches:
  - name: Dawn
  - name: Morning
  - name: Afternoon
  - name: Dusk
  - name: Early Night
  - name: Late Night
```

**Fields:**
- `name`: String (required) - Watch period display name. The lowercase form (via `.lower()`) is used as the key when looking up watch percentages in encounter YAML data (e.g., "Early Night" → "early night").

**Purpose:** Defines the authoritative list of overland watch periods. These names populate `config.watches_list` and `config.watches_key_list` and flow dynamically throughout the application — there are no hardcoded watch period names in the code.

---

### 11.9 Default Calendar.yaml (Optional)

**Format:**
```yaml
calendar:
  name: "Torchcrawl Standard Calendar"
  description: "A simple 10-month fantasy calendar with 300 days per year"
  days_per_week: 6
  current_date:
    month: 1
    day: 15
  lunar_cycle_length: 27
  blood_moon_chance: 10
  lunar_day: null
  is_blood_moon: false
  months:
    - name: "Deepwinter"
      days: 30
      season: "Winter"
    - name: "Latewinter"
      days: 30
      season: "Winter"
    # ... additional months
  holidays:
    - name: "Midwinter Festival"
      description: "A week-long celebration marking the darkest point of winter..."
      month: "Deepwinter"
      day: 15
    # ... additional holidays
```

**Required Fields:**
- `name`: String - Calendar display name
- `description`: String - Calendar description
- `days_per_week`: Integer - Days per week (used for grid columns, e.g., 6)
- `current_date`: Object or null
  - `month`: Integer (1-based) - Current month index
  - `day`: Integer - Current day of month
- `months`: List of month objects
  - `name`: String - Month name
  - `days`: Integer - Days in month
  - `season`: String - Season name (for auto-detection)
- `holidays`: List of holiday objects
  - `name`: String - Holiday name
  - `description`: String - Holiday description
  - `month`: String - Month name (must match a month name)
  - `day`: Integer - Day of month

**Lunar Phase Fields (optional):**
- `lunar_cycle_length`: Integer - Days in one lunar cycle (e.g., 27)
- `blood_moon_chance`: Integer - Percent chance of blood moon on full moon (e.g., 10)
- `lunar_day`: Integer or null - Current position in lunar cycle (1 to lunar_cycle_length)
  - If null on first load, randomized to a starting position
- `is_blood_moon`: Boolean - Whether current full moon is a blood moon
  - Only meaningful when lunar_day is in full moon phase
  - Rolled when entering full moon phase, saved until next cycle

**Configuration:**
Calendar file path is specified in `Default Data Files.yaml`:
```yaml
files:
  calendar_file: "Data/Default Calendar.yaml"
```

**Note:** Calendar feature is optional. If `calendar_file` is not specified or file doesn't exist, the Calendar tab won't appear.

---

### 11.10 Default Data Files.yaml

**Format:**
```yaml
files:
  encounters_file: "Data/Default Encounters.yaml"
  seasons_file: "Data/Default Seasons.yaml"
  watches_file: "Data/Default Watches.yaml"
  zones_file: "Data/Default Zones.yaml"
  weathers_file: "Data/Default Weathers.yaml"
  restinfo_file: "Data/Default Rest Info.yaml"
  encounter_by_zone_file: "Data/Default Encounters By Zone.xlsx"
  weather_by_season_file: "Data/Default Weather By Season.xlsx"
  calendar_file: "Data/Default Calendar.yaml"
```

**Purpose:** Allows configuring different data file sets for different campaigns without modifying code. All data file paths are relative to the application root directory.

---

## 12. Implementation Notes

### 12.1 Critical Design Decisions

**1. Clickable Names Instead of Separate Icon:**
- **Decision:** Click encounter name to expand
- **Rationale:** Cleaner UI, no indentation from icon, intuitive interaction
- **Implementation:** `cursor: pointer` on name, toggle function on click

**2. Gap Removal for Ultra-Tight Spacing:**
- **Decision:** Use `gap-0` class + `gap: 0 !important;` inline style
- **Rationale:** NiceGUI columns have default gaps, need both class and style for certainty
- **Implementation:** Applied to all parent columns and containers

**3. Expansion State Persistence (Site Only):**
- **Decision:** Remember expansion when encounters shift
- **Rationale:** Users tracking approaching threats don't want to re-expand
- **Implementation:** Store in `app.storage.user`, shift along with encounters

**4. Timer "Current" State (0-9 Minutes):**
- **Decision:** Label 0-9 minutes as "Current:" instead of removing immediately
- **Rationale:** Gives users one turn warning before expiration
- **Implementation:** Check range in `__str__`, remove when < 0

**5. Emphasis Only on Specific Elements:**
- **Decision:** Selective emphasis (weather names, encounter names, etc.)
- **Rationale:** Highlight important info without overwhelming
- **Implementation:** Parse strings, wrap specific parts in `<span class="emphasis">`

**6. Calendar as Optional Feature:**
- **Decision:** Calendar only appears when calendar_file is configured and exists
- **Rationale:** Not all campaigns need fantasy calendars
- **Implementation:** Conditional Calendar tab, conditional season dropdown

**7. Current Date in Calendar YAML:**
- **Decision:** Store current_date in the calendar YAML file, not in code
- **Rationale:** Date persists across restarts, easily editable, portable with campaign
- **Implementation:** `save_calendar_date()` rewrites YAML file after date changes

**8. Timer Form Starts Collapsed:**
- **Decision:** Timer form hidden by default, toggled with +/- button
- **Rationale:** Reduces visual clutter until user needs to add timer
- **Implementation:** `show_timer_form` initialized to False in `index()`

**9. Moon Phases with Roughly Equal Duration:**
- **Decision:** Distribute lunar cycle days roughly equally across 8 phases
- **Rationale:** More natural lunar cycle feel than arbitrary phase lengths
- **Implementation:** Calculate phase from lunar_day using cycle_length / 8

**10. Blood Moon Rolled Once Per Full Moon:**
- **Decision:** Roll for blood moon when entering full moon phase, save result
- **Rationale:** Blood moon should be memorable event, not flickering on/off
- **Implementation:** Check if entering full moon phase, roll once, save `is_blood_moon` to file

**11. Blood Moon Icon Using Layered CSS:**
- **Decision:** Use layered CSS technique with grayscale base + red overlay
- **Rationale:** Produces true red color without orange tint from emoji base color
- **Implementation:** Two pseudo-elements (::before grayscale, ::after red overlay) with contrast filter on container

**12. Lunar Day Randomized on First Load:**
- **Decision:** When lunar_day is null, randomize to a position in the cycle
- **Rationale:** More interesting than always starting at new moon
- **Implementation:** `random.randint(1, lunar_cycle_length)` if lunar_day is null

**13. Dynamic Watches from File:**
- **Decision:** Load watch periods from YAML file instead of hardcoding
- **Rationale:** Different campaigns may use different time divisions; data-driven approach is consistent with rest of application
- **Implementation:** `load_watches_file()` populates `config.watches_list`; all code references the dynamic list

**14. Seasons from Dedicated File:**
- **Decision:** Load seasons from a dedicated YAML file with encounter_modification, instead of deriving from Excel column headers
- **Rationale:** Seasons are a first-class concept with their own properties (encounter_modification); Excel columns are a side effect of weather data structure
- **Implementation:** `load_seasons_file()` populates `config.seasons_list` and `config.seasons_data`

**15. Two-Level Season Effect:**
- **Decision:** Season affects both (1) whether any encounter occurs and (2) which encounter is selected
- **Rationale:** Winter should have fewer encounters overall (encounter_modification) AND should exclude creatures that don't appear in winter (per-encounter season %)
- **Implementation:** encounter_modification applied to zone's encounter_chance at runtime; per-encounter season % baked into 4D array at startup

**16. 4D Encounter Array Built at Startup:**
- **Decision:** Precompute all encounter weights for all combinations of [Encounter, Zone, Watch, Season]
- **Rationale:** Avoids recalculating weights on every encounter generation; array lookup is O(1)
- **Implementation:** `generate_encounter_by_zone_watch_and_season()` builds the array once during `load_all_data()`

**17. Encounter List from YAML, Not Excel:**
- **Decision:** The encounters YAML file is the authoritative list of encounters for the 4D array; encounters in YAML but not in Excel get zone_weight = 0
- **Rationale:** Encounters may be defined in YAML for documentation/reference even if they don't appear in any zone; avoids silent data loss if Excel is incomplete
- **Implementation:** 4D array iterates `config.encounters_data.keys()` and checks if each encounter exists in `encounter_by_zone` coords

---

### 12.2 Common Pitfalls

**1. Browser Caching:**
- **Issue:** CSS changes not visible after updates
- **Solution:** Hard refresh (Ctrl+F5 / Cmd+Shift+R)
- **Prevention:** Version CSS or use cache-busting

**2. Expansion Icon Indentation:**
- **Issue:** Expansion components have built-in icons that create indent
- **Solution:** Hide icon with CSS: `.q-expansion-item .q-item__section--side { display: none; }`
- **Alternative:** Use manual toggle with clickable name (current implementation)

**3. Parent Gap Between Children:**
- **Issue:** Columns have default gap between child elements
- **Solution:** Always use `gap-0` class AND `gap: 0 !important;` style
- **Why both:** Framework defaults are strong, need both for certainty

**4. Expansion State Loss:**
- **Issue:** Refreshing UI loses expansion states
- **Solution:** Store in `app.storage.user`, load on render
- **Scope:** Session-scoped, per-user

**5. Timer Removal Timing:**
- **Issue:** When to remove expired timers?
- **Solution:** Remove when `< 0`, not when `== 0`
- **Rationale:** Users see "Current:" label at 0-9 minutes before removal

---

### 12.3 Testing Checklist

**Overland Mode:**
- [ ] Generate with zone, overlay, season (no calendar)
- [ ] Generate with zone, overlay (with calendar date - season auto-detected)
- [ ] Current date displays with emphasized month name
- [ ] Season dropdown hidden when calendar date is set
- [ ] Season dropdown visible when no calendar or no date
- [ ] New Day button advances calendar and regenerates
- [ ] Weather displays with emphasized name
- [ ] Encounters generated for each watch period (or "No Encounter")
- [ ] Encounter names emphasized (not "No Encounter")
- [ ] Click encounter name to expand/collapse
- [ ] Details show immediately below name (no gap)
- [ ] Individual regeneration works
- [ ] Rest Check displays with emphasized weather modifiers
- [ ] Reset clears all content
- [ ] Season encounter_modification affects encounter frequency (fewer in Winter)
- [ ] Encounters with 0% season never appear in that season (e.g., Ankheg in Winter)
- [ ] Encounters with lower season % appear less frequently than those with higher %

**Site Mode:**
- [ ] Generate with zone
- [ ] Time displays with emphasized minutes
- [ ] Current slot empty, 5 future slots generated
- [ ] "Current" encounter names emphasized
- [ ] Non-current encounter names not emphasized
- [ ] Click encounter name to expand/collapse
- [ ] Timer form starts collapsed on page load
- [ ] Timer button shows ➕ when collapsed, ➖ when expanded
- [ ] Add timer with name and duration
- [ ] Timer displays "Current:" at 0-9 minutes
- [ ] Timer removed when goes negative
- [ ] "Current" timer names emphasized
- [ ] New Turn shifts encounters and timers
- [ ] Expansion states preserved after New Turn
- [ ] Reset clears all content and states

**Calendar Tab:**
- [ ] Tab only visible when calendar file loaded
- [ ] Calendar name and description display
- [ ] Current date displays with emphasized month name
- [ ] "No date set" message when current_date is null
- [ ] Holiday displays when current date matches a holiday
- [ ] Month grids show all months with correct days
- [ ] Grid columns match days_per_week setting
- [ ] Click day sets current date
- [ ] Current date highlighted in grid
- [ ] Date changes persist across page refresh
- [ ] Date changes reflect immediately in Overland tab

**Moon Phases:**
- [ ] Moon phase displays next to date (Calendar tab and Overland tab)
- [ ] Correct unicode icon for each phase (🌑🌒🌓🌔🌕🌖🌗🌘)
- [ ] Phase name displays correctly
- [ ] Lunar phase selector shows all 8 phase icons
- [ ] Click phase icon sets lunar_day to that phase
- [ ] [-] button decreases lunar_day (wraps correctly)
- [ ] [+] button increases lunar_day (wraps correctly)
- [ ] Lunar day advances when calendar day advances (New Day)
- [ ] Blood moon rolled when entering full moon phase
- [ ] Blood moon icon has red CSS filter applied
- [ ] Blood moon text displays in red
- [ ] Blood moon status persists until next lunar cycle
- [ ] Lunar day randomized on first load if null
- [ ] Lunar day persists across page refresh

**Data Loading & Seasons:**
- [ ] Seasons loaded from Default Seasons.yaml (check logs)
- [ ] Watches loaded from Default Watches.yaml (check logs)
- [ ] 4D encounter array generated with correct shape (check logs)
- [ ] seasons_list populated from seasons file (not Excel headers)
- [ ] watches_list populated from watches file (not hardcoded)
- [ ] Encounters in YAML but not in Excel have weight 0 (never selected)
- [ ] Application starts without errors with all data files present

**UI:**
- [ ] Dark mode follows system preference
- [ ] Tabs left-aligned, normal case
- [ ] Calendar tab conditional (only when calendar loaded)
- [ ] All buttons flush left (not far right)
- [ ] Ultra-tight spacing throughout
- [ ] No gaps between encounter names and details
- [ ] Consistent indentation hierarchy
- [ ] Emphasis color (#F78080) correct

---

## 13. Future Enhancements

### 13.1 Potential Features

**Data Management:**
- Import/export custom encounters, weather, zones
- Multiple data file sets (switch between campaigns)
- Encounter history/log

**UI Improvements:**
- Customizable emphasis color
- Font size adjustment
- Export to PDF/Markdown

**Gameplay:**
- Dice roller integration
- Initiative tracker
- Session notes

**Technical:**
- Multi-user support (sync between GMs)
- Mobile app version
- Offline mode

---

## 14. Glossary

**Watch:** A time period in overland travel (e.g., Dawn, Morning). Loaded dynamically from Default Watches.yaml.
**Time Slot:** A time period in site exploration (Current, 10 minutes, etc.)
**Spark:** A situation prompt for an encounter (1-N per encounter)
**Overlay:** A secondary zone that modifies encounter chances (50/50 with base zone)
**Expansion State:** Whether an encounter's details are visible or hidden
**Emphasis:** Coral pink highlighting (#F78080) applied to important text
**Current:** Label for timers or encounters at 0-9 minutes or "now"
**Calendar:** Optional fantasy calendar system with months, seasons, and holidays
**Current Date:** The in-game date set in the calendar (stored in calendar YAML file)
**Holiday:** Special day in the calendar with name and description
**Auto-Season:** Season automatically detected from current calendar month
**Encounter Modification:** A season-level percentage that adjusts the base encounter chance for overland zones (e.g., Winter at 40% makes all zones 40% as likely to produce encounters)
**Season Percentage:** A per-encounter percentage indicating how likely that encounter is in a given season (e.g., Ankheg at Winter: 0% never appears in winter). Baked into the 4D array.
**4D Encounter Array:** Precomputed array of encounter weights with dimensions [Encounter, Zone, Watch, Season]. Cell value = zone_weight × watch_percentage × season_percentage.
**Lunar Cycle:** The repeating cycle of moon phases (default 27 days)
**Lunar Day:** Current position in the lunar cycle (1 to lunar_cycle_length)
**Moon Phase:** One of 8 phases: New Moon, Waxing Crescent, First Quarter, Waxing Gibbous, Full Moon, Waning Gibbous, Last Quarter, Waning Crescent
**Blood Moon:** A rare full moon with red appearance (chance configured in calendar file)

---

## 15. Revision History

**Version 2.3 - February 12, 2026:**
- Added Default Seasons.yaml: defines seasons with encounter_modification percentage
- Added Default Watches.yaml: defines watch periods dynamically (replaces hardcoded OVERLAND_WATCHES)
- Seasons list now loaded from seasons YAML file (was: derived from weather Excel column headers)
- Watch periods flow dynamically throughout the application from the watches file
- Season encounter_modification adjusts overland zone encounter_chance multiplicatively
- Per-encounter season percentages (from encounters YAML `season` field) now factored into encounter selection
- 4D encounter probability array [Encounter, Zone, Watch, Season] replaces former 3D array [Encounter, Zone, Watch]
- 4D array dimension sizes all set dynamically from data files
- Encounter list for 4D array sourced from encounters YAML (authoritative), not Excel
- Encounters in YAML but not in Excel get zone_weight = 0 (never selected)
- Fixed `season` key mismatch in encounters YAML loading (was reading `seasons` plural)
- Renamed Default Data Files.yaml (was: Default Data Files.yaml)
- Added seasons_file and watches_file entries to data files config

**Version 2.2 - February 5, 2026:**
- Added moon phase tracking system
- 8 moon phases with unicode icons (🌑🌒🌓🌔🌕🌖🌗🌘)
- Configurable lunar cycle length (default 27 days)
- Blood moon feature with configurable chance (default 10%)
- Blood moon display with red CSS filter on icon
- Lunar phase selector on Calendar tab ([-] icons [+])
- Moon phase displays on both Calendar and Overland tabs
- Lunar day advances with calendar day
- Lunar day randomized on first load if not set
- Blood moon status persists until next lunar cycle

**Version 2.1 - February 5, 2026:**
- Added optional Calendar system with fantasy calendar support
- Calendar Tab: Visual month grid, clickable days, holiday display
- Overland integration: Date display, auto-season detection, New Day button
- Current date stored in calendar YAML file (persists across restarts)
- Calendar file path configurable in Default Data Files.yaml
- Timer form now starts collapsed (hidden by default)
- Timer toggle button shows ➖ when expanded, ➕ when collapsed
- Added calendar utility functions (get_calendar_date_string, get_current_season, advance_calendar_date, get_current_holiday)

**Version 2.0 - February 5, 2026:**
- Migrated from Streamlit to NiceGUI
- Implemented ultra-tight spacing
- Added coral pink emphasis (#F78080)
- Made encounter names clickable
- Added persistent expansion states for Site mode
- Implemented timer "Current:" state (0-9 minutes)
- Added dark mode auto-detection
- Complete UI polish and bug fixes

**Version 1.0 - Prior:**
- Original Streamlit implementation
- Basic encounter and weather generation
- Site mode with timers

---

## End of Specification

**This document is sufficient to recreate the application from scratch.**

For implementation, begin with:
1. Setup NiceGUI project structure
2. Create data models (models.py)
3. Implement data loading (data_loader.py)
4. Build Overland logic (overland_logic.py)
5. Build Site logic (site_logic.py)
6. Create UI (app.py) following this specification
7. Apply CSS styling as specified
8. Test against checklist
9. Polish and optimize

**Contact:** [Your contact information]  
**License:** [Your license]  
**Repository:** [Your repository URL]
