# Torchcrawl GM Control Panel - Complete Specification

**Version:** 2.0 (NiceGUI)  
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
6. [Calendar System](#6-calendar-system)
7. [Features](#7-features)
8. [Technical Requirements](#8-technical-requirements)
9. [File Structure](#9-file-structure)
10. [Configuration](#10-configuration)
11. [Data Files](#11-data-files)

---

## 1. Overview

### 1.1 Purpose
A game master control panel for the Torchcrawl tabletop RPG system that generates and manages encounters, weather, timers, and rest checks for both overland travel and site-based exploration.

### 1.2 Key Features
- **Overland Mode:** Day-by-day travel with weather, encounters (6 per day), and rest checks
- **Site Mode:** 10-minute turn tracking with encounters (current + 5 future slots) and timers
- **Calendar System:** Optional calendar tracking with visual date selection, holidays, and automatic season detection
- **Data-Driven:** All encounters, weather, zones, calendar loaded from YAML/Excel files
- **Persistent State:** Expansion states preserved when encounters shift; calendar date saved to file
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
│  [Overland]  [Site]                      │  ← Tabs (left-aligned)
├──────────────────────────────────────────┤
│                                          │
│  Tab Content                             │  ← Scrollable content area
│  (Overland or Site)                      │
│                                          │
└──────────────────────────────────────────┘
```

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

**Layout:**
```
┌─────────────────────────────────┐
│ Zone: [Dropdown ▼] Overlay: [Dropdown ▼] Season: [Dropdown ▼]  │
│ [Generate] [Reset]                                               │
└─────────────────────────────────┘
```

**Elements:**
- 3 dropdowns in a row (`ui.row`)
- Zone: Required, no default
- Overlay: Optional, "None" default
- Season: Required, no default
- Generate button: Triggers `overland_generate()`
- Reset button: Triggers `overland_reset()`

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

**Structure:**
```
Timers➕
    Current: Torch expires 🔄
             ^^^^^^^^^^^^^ 
             emphasized
    10 minutes: Poison effect ❌
    (not emphasized)
```

**Layout:**
```
ui.row (gap-0):                          # Header row
    ui.label('Timers')                   # Section header
    ui.button('➕')                       # Add button (flush left!)

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
- Shown when `app.storage.user['show_timer_form'] = True`
- Toggled by ➕ button
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

### 5.3 CSS Styling

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

## 6. Calendar System

### 6.1 Overview

The calendar system is **optional** and provides:
- Visual date selection with calendar grid
- Automatic season detection from current month
- Holiday tracking with rich descriptions
- Persistent date storage in calendar YAML file
- Date advancement via "New Day" button

**Key Principle:** Calendar file is both template (months, holidays) and state (current_date)

---

### 6.2 Calendar Modes

#### 6.2.1 No Calendar Mode

**Condition:** Calendar file doesn't exist, is blank, or contains only `calendar:`

**Behavior:**
- No Calendar tab displayed
- Overland tab shows season dropdown (current behavior)
- No date display
- Application works normally

---

#### 6.2.2 Calendar Without Date

**Condition:** Calendar file has months/holidays but `current_date` is null or unset

**Behavior:**
- Calendar tab displayed
- Overland tab shows "No date set - set date via Calendar tab" where date would appear
- Season dropdown still displayed
- User must click a date in Calendar tab to set initial date

---

#### 6.2.3 Calendar With Date

**Condition:** Calendar file has months/holidays and valid `current_date`

**Behavior:**
- Calendar tab displayed
- Overland tab shows date (e.g., "Deepwinter 15 (Winter)")
- Season auto-detected from current month (NO season dropdown)
- Date advances when "New Day" pressed
- Date can be changed by clicking in Calendar tab

---

### 6.3 Calendar Tab UI

#### 6.3.1 Layout

```
┌─────────────────────────────────────────┐
│ Deepwinter 15 (Winter)                  │  ← Current date (top)
│ 🎉 Midwinter Festival                   │  ← Holiday (if applicable)
│    A week-long celebration...           │
├─────────────────────────────────────────┤
│                                         │
│ Deepwinter                              │  ← Month name
│ ┌───┬───┬───┬───┬───┬───┐              │  ← Grid (days_per_week columns)
│ │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │              │
│ ├───┼───┼───┼───┼───┼───┤              │
│ │ 7 │ 8 │ 9 │10 │11 │12 │              │
│ ├───┼───┼───┼───┼───┼───┤              │
│ │13 │14 │15 │16 │17 │18 │              │  ← 15 is current (coral pink)
│ │   │   │🎉 │   │   │   │              │  ← 15 is holiday (gold bg)
│ ├───┼───┼───┼───┼───┼───┤              │
│ │19 │20 │21 │22 │23 │24 │              │
│ ├───┼───┼───┼───┼───┼───┤              │
│ │25 │26 │27 │28 │29 │30 │              │
│ └───┴───┴───┴───┴───┴───┘              │
│                                         │
│ Latewinter                              │
│ [Similar grid...]                       │
│                                         │
│ [All 10 months displayed vertically]   │
│                                         │
├─────────────────────────────────────────┤
│ Holidays:                               │  ← Holiday list (bottom)
│ - Midwinter Festival - Deepwinter 15   │  ← Current holiday emphasized
│ - Day of Thaw - Earlyspring 1          │
│ - Greengrass - Latespring 20            │
│ ...                                     │
└─────────────────────────────────────────┘
```

---

#### 6.3.2 Current Date Display

**Format:** `{Month} {Day} ({Season})`

**Example:** `Deepwinter 15 (Winter)`

**Emphasis:** 
- If current date is a holiday, holiday name emphasized in coral pink
- Date itself not emphasized

**Placement:** Top of Calendar tab

---

#### 6.3.3 Holiday Display (If Current Date)

**Format:**
```
Deepwinter 15 (Winter)
🎉 Midwinter Festival
   A week-long celebration marking the darkest point of winter, with feasting, storytelling, and gift-giving.
```

**Styling:**
- Holiday name: Emphasized (coral pink #F78080)
- Description: Normal text, indented
- Only shown if current date matches a holiday

---

#### 6.3.4 Calendar Grids

**Structure:**
- One grid per month
- All months displayed vertically (scrollable)
- Grid columns = `calendar['days_per_week']` (e.g., 6)

**Day Styling:**
- **Normal day:** Default background, clickable button
- **Current day:** Text emphasized (coral pink #F78080)
- **Holiday day:** Background light gold/amber
- **Current + Holiday:** Both stylings applied

**Interactions:**
- **Click day:** Sets current date to that month/day, saves to file
- **Hover holiday:** Tooltip shows holiday name
- **Current day:** Highlighted so user knows current position

---

#### 6.3.5 Holiday List

**Format:** Simple list at bottom

```
Holidays:
- Midwinter Festival - Deepwinter 15
- Day of Thaw - Earlyspring 1
- Greengrass - Latespring 20
- Midsummer - Highsun 15
- First Harvest - Latesummer 25
- Harvest Home - Earlyfall 20
- Day of the Dead - Latefall 30
- Longnight - Frostfall 1
```

**Styling:**
- Current date holiday: Emphasized (coral pink)
- Other holidays: Normal text
- Hover: Tooltip shows full description

---

### 6.4 Overland Tab Changes

#### 6.4.1 Date Display (With Calendar)

**Location:** Top of General section (no "Current Date:" label)

**Format:** `{Month} {Day} ({Season})`

**Example:**
```
General
    Deepwinter 15 (Winter)
    3 days
    Weather: Clear Skies 🔄
```

**Emphasis:** Only month name is emphasized (coral pink)

---

#### 6.4.2 Holiday Display (With Calendar)

**If current date is a holiday:**

```
General
    Deepwinter 15 (Winter)
    Midwinter Festival - A week-long celebration marking the darkest point of winter, with feasting, storytelling, and gift-giving.
    
    3 days
    Weather: Clear Skies 🔄
```

**Styling:**
- Holiday name: Not emphasized
- Description: Normal text
- Placed directly under date

---

#### 6.4.3 Season Selection

**With calendar + date set:**
- NO season dropdown
- Season auto-detected from current month

**With calendar + no date:**
- Season dropdown displayed
- Shows "No date set - set date via Calendar tab" instead of date

**Without calendar:**
- Season dropdown displayed (current behavior)
- No date display

---

#### 6.4.4 New Day Button Behavior

**With calendar + date set:**
1. Increments `generated_overland_days` by 1
2. Advances calendar date by 1 day
3. Saves new date to calendar file
4. Generates new weather/encounters for new date
5. Auto-detects season from new month (if month changed)

**With calendar + no date OR without calendar:**
- Works as before (no calendar changes)

---

#### 6.4.5 Reset Button Behavior

**Always:**
- Sets `generated_overland_days = 0`
- Does NOT change calendar date
- Calendar date is independent of reset

**Rationale:** Reset resets the "day counter" but not the actual calendar date

---

### 6.5 Calendar Data Model

#### 6.5.1 YAML Structure

```yaml
calendar:
  name: "Torchcrawl Standard Calendar"
  description: "A simple 10-month fantasy calendar"
  days_per_week: 6
  
  # Current date (written by application)
  current_date:
    month: 1    # 1-based month index
    day: 15     # 1-based day of month
  
  # Month definitions
  months:
    - name: "Deepwinter"
      days: 30
      season: "Winter"
    # ... more months
  
  # Holiday definitions
  holidays:
    - name: "Midwinter Festival"
      description: "A week-long celebration..."
      month: "Deepwinter"  # References month name
      day: 15
    # ... more holidays
```

---

#### 6.5.2 Calendar Fields

**calendar (root):**
- `name`: Calendar name (string)
- `description`: Calendar description (string, optional)
- `days_per_week`: Number of days in a week (integer, default 6)
- `current_date`: Current date object (null or {month, day})
- `months`: List of month objects
- `holidays`: List of holiday objects

**Month Object:**
- `name`: Month name (string, required)
- `days`: Days in month (integer, required)
- `season`: Season name (string, required: Spring/Summer/Fall/Winter)

**Holiday Object:**
- `name`: Holiday name (string, required)
- `description`: Rich description (string, required)
- `month`: Month name (string, must match a month)
- `day`: Day of month (integer, 1-based, must be valid for month)

**Current Date Object:**
- `month`: Month number (integer, 1-based index into months list)
- `day`: Day number (integer, 1-based, must be 1 to months[month-1].days)

---

### 6.6 Calendar Logic

#### 6.6.1 Date Advancement Algorithm

```python
def advance_calendar_date(days: int = 1) -> bool:
    """Advance calendar date by specified days."""
    
    # Get current state
    month = current_date['month']  # 1-based
    day = current_date['day']
    months = calendar_data['months']
    
    # Add days
    day += days
    
    # Handle overflow
    while day > months[month - 1]['days']:
        day -= months[month - 1]['days']
        month += 1
        
        # Wrap to month 1 if overflow
        if month > len(months):
            month = 1
    
    # Save to file
    save_calendar_date(month, day)
    
    return True
```

**Key:** No year tracking. When reaching end of last month, wrap to month 1.

---

#### 6.6.2 Season Detection

```python
def get_current_season() -> str:
    """Get season from current month."""
    
    if not calendar_data or not current_date:
        return ""
    
    month_idx = current_date['month'] - 1
    return calendar_data['months'][month_idx]['season']
```

**Usage:** Overland mode uses this instead of user selection when calendar with date exists.

---

#### 6.6.3 Holiday Detection

```python
def get_current_holiday():
    """Get holiday for current date, if any."""
    
    month_name = calendar_data['months'][current_date['month'] - 1]['name']
    day = current_date['day']
    
    for holiday in calendar_data['holidays']:
        if holiday['month'] == month_name and holiday['day'] == day:
            return holiday
    
    return None
```

**Returns:** Holiday dict or None

---

#### 6.6.4 Date Persistence

**Save Operation:**
1. Update `config.calendar_data['current_date']`
2. Read full YAML file
3. Update `data['calendar']['current_date']`
4. Write YAML back to file

**Load Operation:**
1. Read YAML file
2. Store in `config.calendar_data`
3. Extract `current_date` if present

**File:** `Default Calendar.yaml` (same file as calendar definition)

---

### 6.7 Calendar Utility Functions

**In utils.py:**

```python
def get_calendar_date_string() -> str:
    """Format current date for display."""
    # Returns "Deepwinter 15 (Winter)" or 
    # "No date set - set date via Calendar tab" or ""

def get_current_season() -> str:
    """Get season from current month."""
    # Returns "Winter" or ""

def advance_calendar_date(days: int = 1) -> bool:
    """Advance date and save to file."""
    # Returns True if successful

def get_current_holiday():
    """Get holiday for current date."""
    # Returns holiday dict or None
```

**In data_loader.py:**

```python
def load_calendar_file() -> bool:
    """Load calendar (optional)."""
    # Returns True always (doesn't fail if missing)

def save_calendar_date(month: int, day: int) -> bool:
    """Save date to calendar file."""
    # Returns True if successful
```

---

### 6.8 Calendar Validation

**Month Validation:**
- Name: Non-empty string
- Days: Integer >= 1
- Season: One of "Spring", "Summer", "Fall", "Winter"

**Holiday Validation:**
- Name: Non-empty string
- Description: Non-empty string
- Month: Must match a month name in months list
- Day: Must be 1 <= day <= days_in_month

**Current Date Validation:**
- Month: 1 <= month <= len(months)
- Day: 1 <= day <= months[month-1]['days']

**File Validation:**
- days_per_week: Integer >= 1 (defaults to 6 if missing)
- At least 1 month required for calendar to be active
- Holidays optional

---

### 6.9 Example Calendar

**10 months, 6-day weeks, 8 holidays:**

```yaml
calendar:
  name: "Torchcrawl Standard Calendar"
  days_per_week: 6
  current_date:
    month: 1
    day: 15
  
  months:
    - name: "Deepwinter"
      days: 30
      season: "Winter"
    # ... 9 more months (300 days total)
  
  holidays:
    - name: "Midwinter Festival"
      description: "Week-long winter celebration..."
      month: "Deepwinter"
      day: 15
    # ... 7 more holidays
```

**See:** `Default Calendar.yaml` for complete example

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

**Optional System:**
- ✅ Works with or without calendar file
- ✅ Calendar tab only appears if calendar defined
- ✅ Falls back to season dropdown if no calendar

**Visual Calendar:**
- ✅ Grid display of all months
- ✅ Dynamic columns based on days_per_week
- ✅ Click any day to set current date
- ✅ Current day highlighted (coral pink text)
- ✅ Holiday days marked (gold background)

**Date Tracking:**
- ✅ Current date saved to calendar file
- ✅ Persists across application restarts
- ✅ Advances automatically with "New Day" button
- ✅ No year tracking (wraps at end of year)

**Holiday System:**
- ✅ Rich holiday descriptions
- ✅ Display on current date in both tabs
- ✅ Hover tooltips on holiday days
- ✅ Emphasized when current

**Season Integration:**
- ✅ Auto-detect season from current month
- ✅ No season dropdown when calendar active
- ✅ Seamless weather generation integration

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
- ✅ YAML for encounters, weather, zones, rest info, calendar
- ✅ Excel for probabilities (weather by season, encounters by zone)
- ✅ Weighted random selection
- ✅ Human-readable, editable data files
- ✅ Calendar file is both template and state storage

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
├── Default Calendar.yaml          # Calendar definition + current date (OPTIONAL)
├── logs/                          # Runtime logs (created on first run)
│   └── TCControlPanel.log
└── data/                          # Data files
    ├── Default Encounters.yaml
    ├── Default Weathers.yaml
    ├── Default Zones.yaml
    ├── Default Rest Info.yaml
    ├── Default Encounters By Zone.xlsx
    └── Default Weather By Season.xlsx
```

### 9.1 File Responsibilities

**app.py:**
- NiceGUI application setup
- UI rendering (tabs, sections, components)
- Calendar tab rendering (grids, date selection)
- Event handlers (button clicks, toggles, date selection)
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
- Calendar data and month lookup

**data_loader.py:**
- YAML file parsing
- Excel file parsing (with openpyxl)
- xarray DataArray creation
- Error handling for missing files
- Calendar loading (optional)
- Calendar date saving (writes to file)

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
- `get_calendar_date_string()`: Format current date
- `get_current_season()`: Get season from calendar
- `advance_calendar_date()`: Advance and save date
- `get_current_holiday()`: Get holiday for current date

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
  
  # Current date (written by application, null if not set)
  current_date:
    month: 1
    day: 15
  
  # Month definitions
  months:
    - name: "Deepwinter"
      days: 30
      season: "Winter"
    
    - name: "Latewinter"
      days: 30
      season: "Winter"
    
    # ... more months
  
  # Holiday definitions
  holidays:
    - name: "Midwinter Festival"
      description: "A week-long celebration marking the darkest point of winter, with feasting, storytelling, and gift-giving."
      month: "Deepwinter"
      day: 15
    
    # ... more holidays
```

**Fields:**

**calendar (root):**
- `name`: Calendar name (string, optional)
- `description`: Calendar description (string, optional)
- `days_per_week`: Days in a week (integer, required, default 6)
- `current_date`: Current date object or null (written by app)
- `months`: List of month objects (required, at least 1)
- `holidays`: List of holiday objects (optional)

**Month Object:**
- `name`: Month name (string, required)
- `days`: Days in month (integer >= 1, required)
- `season`: Season name (string, required: Spring/Summer/Fall/Winter)

**Holiday Object:**
- `name`: Holiday name (string, required)
- `description`: Rich description (string, required)
- `month`: Month name (string, must match a month name)
- `day`: Day of month (integer, 1-based, must be valid for month)

**Current Date Object:**
- `month`: Month index (integer, 1-based, 1 to len(months))
- `day`: Day of month (integer, 1-based, 1 to month.days)

**Special Notes:**
- **Optional File:** Application works without this file
- **Blank File:** If file is blank or contains only `calendar:`, app works without calendar
- **Read/Write:** This is the ONLY data file the application writes to (saves current_date)
- **State Storage:** File stores both template (months/holidays) and state (current_date)
- **No Year:** Calendar does not track years; wraps at end of last month

**Example - 10 Month Calendar:**
- 10 months × 30 days = 300 days per year
- 6-day weeks
- 8 holidays (2 per season)
- Seasons: 3 Winter, 2 Spring, 3 Summer, 2 Fall

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
- **Decision:** Calendar system is completely optional
- **Rationale:** Backward compatibility; not all campaigns need calendar tracking
- **Implementation:** Application detects calendar file presence and adapts UI accordingly

**7. Calendar File Dual Purpose:**
- **Decision:** Calendar YAML is both template and state storage
- **Rationale:** Simplicity; avoids separate config file for just one value
- **Implementation:** Application writes current_date back to calendar file

**8. No Year Tracking:**
- **Decision:** Calendar tracks month and day only, no year
- **Rationale:** Fits Torchcrawl setting where "nobody knows what year it is"
- **Implementation:** Date wraps to month 1 at end of calendar

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
- [ ] Generate with zone, overlay, season
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
- [ ] Add timer with name and duration
- [ ] Timer displays "Current:" at 0-9 minutes
- [ ] Timer removed when goes negative
- [ ] "Current" timer names emphasized
- [ ] New Turn shifts encounters and timers
- [ ] Expansion states preserved after New Turn
- [ ] Reset clears all content and states

**Calendar Mode:**
- [ ] Calendar tab appears when calendar file exists with months
- [ ] Calendar tab not shown when no calendar or blank calendar
- [ ] All months displayed vertically with correct number of columns (days_per_week)
- [ ] Click day to set current date
- [ ] Current day highlighted (coral pink text)
- [ ] Holiday days have gold background
- [ ] Hover on holiday day shows tooltip with holiday name
- [ ] Current date displayed at top
- [ ] If current date is holiday, holiday name/description shown
- [ ] Holiday list at bottom shows all holidays
- [ ] Current holiday emphasized in list
- [ ] Hover on holiday in list shows description tooltip

**Overland with Calendar:**
- [ ] Date displayed without "Current Date:" label
- [ ] Date format: "Deepwinter 15 (Winter)"
- [ ] Month name emphasized (coral pink)
- [ ] Season auto-detected (no season dropdown)
- [ ] Holiday name and description shown if current date is holiday
- [ ] New Day advances date by 1
- [ ] Date wraps to month 1 at end of year
- [ ] Date persists after app restart
- [ ] Reset doesn't change date

**Overland without Calendar:**
- [ ] Season dropdown displayed
- [ ] No date shown
- [ ] Works as before

**UI:**
- [ ] Dark mode follows system preference
- [ ] Tabs left-aligned, normal case
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

---

## 15. Revision History

**Version 2.1 - February 5, 2026:**
- Added optional calendar system
- Visual calendar grid with date selection
- Holiday tracking with rich descriptions
- Automatic season detection from current month
- Calendar date persists to file
- New Calendar tab for date management
- Overland tab adapts based on calendar presence

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
