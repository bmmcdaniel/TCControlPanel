# Torchcrawl GM Control Panel - Complete Specification

**Version:** 2.1 (NiceGUI + Calendar)
**Date:** February 5, 2026
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
- **Overland Mode:** Day-by-day travel with weather, encounters (6 per day), and rest checks
- **Site Mode:** 10-minute turn tracking with encounters (current + 5 future slots) and timers
- **Calendar System:** Optional fantasy calendar with date tracking, holidays, and auto-season detection
- **Data-Driven:** All encounters, weather, zones loaded from YAML/Excel files
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
    sparks: List[str]             # Situation prompts (1-4 items)
    description: Optional[str]    # Physical description
    habitat: Optional[str]        # Environmental context
    
    def is_encounter() -> bool:
        """Returns True if name is not None"""
    
    def generate_overland_encounter(...):
        """Generate for specific watch period"""
    
    def generate_site_encounter(...):
        """Generate for specific time slot"""
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
│ Current Date: Deepwinter 15 (Winter)                            │
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

**Watches (6 per day):**
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

**Conditional Display:** Only visible when a calendar file is loaded (configured in Test Data Files.yaml)

#### 5.3.1 Calendar Header

**Structure:**
```
Calendar: Torchcrawl Standard Calendar
A simple 10-month fantasy calendar with 300 days per year

Current Date: Deepwinter 15 (Winter)
              ^^^^^^^^^^
              emphasized (coral pink)
```

**Layout:**
```
ui.label(calendar_name)              # Calendar name (bold)
ui.label(description)                # Calendar description
ui.html(date_string)                 # Current date with emphasis
```

**Date Display Modes:**
- **Date set:** `<span class="emphasis">{month}</span> {day} ({season})`
- **No date set:** "No date set - set date via calendar below"

#### 5.3.2 Holiday Display

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

#### 5.3.3 Month Grid

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

#### 5.3.4 Calendar Data Requirements

**Required fields in calendar YAML:**
- `name`: Calendar display name
- `description`: Calendar description
- `days_per_week`: Number of days per week (for grid columns)
- `current_date`: Object with `month` (1-based) and `day`, or null
- `months`: List of month objects with `name`, `days`, `season`
- `holidays`: List of holiday objects with `name`, `description`, `month` (name), `day`

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
5. Generate 6 encounters (one per watch)
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

3. Roll for encounter:
   - Random 1-100
   - If roll <= encounter_chance: generate encounter
   - Else: no encounter (name = None)

4. If encounter:
   a. Get weight table for (active_zone, watch)
   b. Weighted random selection from encounters
   c. Populate: name, description, habitat
   d. Generate 1-4 sparks (random from encounter's sparks list)

5. Set encounter.time = watch
```

**Source Tables:**
- Encounter chance: `zones_data[zone]['encounter_chance']`
- Weights: `encounter_by_zone_and_watch[zone, watch]`

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
- ✅ 6 encounters per day (by watch)
- ✅ 50/50 overlay system
- ✅ Rest checks with DCs and modifiers

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

**Overland Integration:**
- ✅ Date display when calendar date set
- ✅ Auto-season detection from current month
- ✅ Conditional Season dropdown (hidden when auto-detected)
- ✅ New Day button to advance calendar

**Data Persistence:**
- ✅ Current date saved to calendar YAML file
- ✅ Date persists across application restarts
- ✅ Calendar file path configurable in Test Data Files.yaml

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
- ✅ YAML for encounters, weather, zones, rest info
- ✅ Excel for probabilities (weather by season, encounters by zone)
- ✅ Weighted random selection
- ✅ Human-readable, editable data files

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
    ├── Test Data Files.yaml       # Configuration for data file paths
    ├── Default Encounters.yaml
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
- Constants (watches, time slots, file paths)
- Loaded data storage

**data_loader.py:**
- YAML file parsing
- Excel file parsing (with openpyxl)
- xarray DataArray creation
- Error handling for missing files
- `load_calendar_file()`: Load calendar data (optional)
- `save_calendar_date()`: Save current date to calendar YAML

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

### 10.1 Constants (config.py)

```python
# Overland
OVERLAND_WATCHES = [
    "Dawn", "Morning", "Afternoon", 
    "Dusk", "Early Night", "Late Night"
]
OVERLAND_SEASONS = ["Spring", "Summer", "Fall", "Winter"]

# Site
SITE_TIME_SLOTS = [
    "Current", "10 minutes", "20 minutes", 
    "30 minutes", "40 minutes", "50 minutes"
]

# File paths
DATA_DIR = Path(__file__).parent / "data"
ENCOUNTERS_FILE = DATA_DIR / "Default Encounters.yaml"
WEATHERS_FILE = DATA_DIR / "Default Weathers.yaml"
ZONES_FILE = DATA_DIR / "Default Zones.yaml"
REST_INFO_FILE = DATA_DIR / "Default Rest Info.yaml"
ENCOUNTERS_BY_ZONE_FILE = DATA_DIR / "Default Encounters By Zone.xlsx"
WEATHER_BY_SEASON_FILE = DATA_DIR / "Default Weather By Season.xlsx"
```

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

# Loaded data
encounters_data: Dict = {}
weathers_data: Dict = {}
zones_data: Dict = {}
rest_info_data: Dict = {}
encounter_by_zone_and_watch: xr.DataArray = None
encounter_by_zone: xr.DataArray = None
weather_by_season: xr.DataArray = None

# Calendar data (optional feature)
calendar_file: str = ""                   # Path to calendar file (from Test Data Files.yaml)
calendar_data: Optional[Dict] = None      # Full calendar structure from YAML (includes current_date)
calendar_month_lookup: Dict[str, int] = {}  # Month name -> 1-based index for quick lookups
```

---

## 11. Data Files

### 11.1 Default Encounters.yaml

**Format:**
```yaml
encounters:
  - name: "Ankheg"
    description: "12-foot tall mantis-like insect with powerful mandibles"
    habitat: "Temperate forests and plains"
    sparks:
      - "The adventuring company comes across the crumbling lip of a hole"
      - "An ankheg is digging a new pit-burrow"
      - "The ankheg is fleeing from a land shark"
```

**Fields:**
- `name`: String (required) - Encounter name
- `description`: String (optional) - Physical description
- `habitat`: String (optional) - Environment context
- `sparks`: List[String] (required, 1-N items) - Situation prompts

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
  - name: "Mirkwood"
    encounter_chance: 40
  - name: "Road"
    encounter_chance: 20
```

**Fields:**
- `name`: String (required) - Zone name
- `encounter_chance`: Integer (required, 1-100) - Percent chance of encounter

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

**Sheet: "Overland"**

**Format:**
```
| Encounter | Mirkwood_Dawn | Mirkwood_Morning | ... | Road_Dawn | ... |
|-----------|---------------|------------------|-----|-----------|-----|
| Ankheg    | 10            | 5                | ... | 2         | ... |
| Troll     | 8             | 12               | ... | 1         | ... |
```

**Dimensions:**
- Rows: Encounter names (must match Encounters.yaml)
- Columns: `{Zone}_{Watch}` combinations
- Values: Integer weights (0 = never, higher = more likely)

**Sheet: "Site"**

**Format:**
```
| Encounter | Mirkwood | Road | Ruins | ... |
|-----------|----------|------|-------|-----|
| Ankheg    | 10       | 2    | 0     | ... |
| Troll     | 8        | 1    | 15    | ... |
```

**Dimensions:**
- Rows: Encounter names
- Columns: Zone names
- Values: Integer weights

**Note:** Site mode doesn't use watch-specific weights

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

### 11.7 Default Calendar.yaml (Optional)

**Format:**
```yaml
calendar:
  name: "Torchcrawl Standard Calendar"
  description: "A simple 10-month fantasy calendar with 300 days per year"
  days_per_week: 6
  current_date:
    month: 1
    day: 15
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

**Configuration:**
Calendar file path is specified in `Test Data Files.yaml`:
```yaml
files:
  calendar_file: "Data/Default Calendar.yaml"
```

**Note:** Calendar feature is optional. If `calendar_file` is not specified or file doesn't exist, the Calendar tab won't appear.

---

### 11.8 Test Data Files.yaml

**Format:**
```yaml
files:
  encounters_file: "Data/Default Encounters.yaml"
  zones_file: "Data/Default Zones.yaml"
  weathers_file: "Data/Default Weathers.yaml"
  restinfo_file: "Data/Default Rest Info.yaml"
  encounter_by_zone_file: "Data/Default Encounters By Zone.xlsx"
  weather_by_season_file: "Data/Default Weather By Season.xlsx"
  calendar_file: "Data/Default Calendar.yaml"
```

**Purpose:** Allows configuring different data file sets for different campaigns without modifying code.

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
- [ ] 6 encounters generated (or "No Encounter")
- [ ] Encounter names emphasized (not "No Encounter")
- [ ] Click encounter name to expand/collapse
- [ ] Details show immediately below name (no gap)
- [ ] Individual regeneration works
- [ ] Rest Check displays with emphasized weather modifiers
- [ ] Reset clears all content

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

**Watch:** A time period in overland travel (Dawn, Morning, etc.)
**Time Slot:** A time period in site exploration (Current, 10 minutes, etc.)
**Spark:** A situation prompt for an encounter (1-4 per encounter)
**Overlay:** A secondary zone that modifies encounter chances (50/50 with base zone)
**Expansion State:** Whether an encounter's details are visible or hidden
**Emphasis:** Coral pink highlighting (#F78080) applied to important text
**Current:** Label for timers or encounters at 0-9 minutes or "now"
**Calendar:** Optional fantasy calendar system with months, seasons, and holidays
**Current Date:** The in-game date set in the calendar (stored in calendar YAML file)
**Holiday:** Special day in the calendar with name and description
**Auto-Season:** Season automatically detected from current calendar month

---

## 15. Revision History

**Version 2.1 - February 5, 2026:**
- Added optional Calendar system with fantasy calendar support
- Calendar Tab: Visual month grid, clickable days, holiday display
- Overland integration: Date display, auto-season detection, New Day button
- Current date stored in calendar YAML file (persists across restarts)
- Calendar file path configurable in Test Data Files.yaml
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
