# Calendar System Implementation - Conversation Summary
**Date:** February 5, 2026  
**Context:** Adding optional calendar tracking to Torchcrawl GM Control Panel

---

## Overview

Adding an **optional calendar system** to the Torchcrawl application with:
- Visual calendar grid for date selection
- Holiday tracking with descriptions
- Automatic season detection from current month
- Persistent date storage in calendar YAML file

---

## Key Decisions Made

### 1. Calendar is Optional

**Three Operating Modes:**

**Mode 1: No Calendar**
- No calendar file exists OR file is blank OR contains only `calendar:`
- **Behavior:** No Calendar tab, season dropdown shown (current behavior)

**Mode 2: Calendar Without Date Set**
- Calendar file exists with months but `current_date` is null
- **Behavior:** Calendar tab shown, Overland tab shows "No date set - set date via Calendar tab", season dropdown still shown

**Mode 3: Calendar With Date Set**
- Calendar file exists with months and valid `current_date`
- **Behavior:** Calendar tab shown, date displayed, season auto-detected (NO season dropdown)

---

### 2. Calendar YAML Format

```yaml
calendar:
  name: "Torchcrawl Standard Calendar"
  description: "A simple 10-month fantasy calendar"
  days_per_week: 6
  
  # Current date (null initially, written by application)
  current_date:
    month: 1    # 1-based index
    day: 15     # 1-based day
  
  months:
    - name: "Deepwinter"
      days: 30
      season: "Winter"
    # ... more months
  
  holidays:
    - name: "Midwinter Festival"
      description: "A week-long celebration marking the darkest point of winter, with feasting, storytelling, and gift-giving."
      month: "Deepwinter"  # References month name (not number)
      day: 15
    # ... more holidays
```

**Key Points:**
- `days_per_week`: Defines calendar grid columns (default 6)
- `current_date`: null until user sets it
- Holiday `month`: String matching a month name
- Holiday `day`: 1-based day number
- **This is the ONLY data file the application writes to**

---

### 3. No Year Tracking

**Decision:** Calendar only tracks month and day (no year)

**Rationale:** In Torchcrawl setting, "nobody knows what the year is"

**Behavior:** When reaching end of last month, wraps to month 1

---

### 4. Calendar Tab UI

**Layout Structure:**

```
┌─────────────────────────────────────────┐
│ Deepwinter 15 (Winter)                  │  ← Current date (top)
│ 🎉 Midwinter Festival                   │  ← Holiday name (if applicable)
│    Week-long celebration...             │     Holiday description
├─────────────────────────────────────────┤
│                                         │
│ Deepwinter                              │  ← Month name
│ ┌───┬───┬───┬───┬───┬───┐              │  ← Grid (days_per_week columns)
│ │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │              │
│ ├───┼───┼───┼───┼───┼───┤              │
│ │ 7 │ 8 │ 9 │10 │11 │12 │              │
│ ├───┼───┼───┼───┼───┼───┤              │
│ │13 │14 │15 │16 │17 │18 │              │  ← 15 is current date
│ └───┴───┴───┴───┴───┴───┘              │
│                                         │
│ Latewinter                              │
│ [Similar grid...]                       │
│                                         │
│ [ALL 10 months stacked vertically]     │
│                                         │
├─────────────────────────────────────────┤
│ Holidays:                               │  ← Holiday list (bottom)
│ - Midwinter Festival - Deepwinter 15   │
│ - Day of Thaw - Earlyspring 1          │
│ - Greengrass - Latespring 20            │
│ ...                                     │
└─────────────────────────────────────────┘
```

**Grid Layout:**
- One grid per month, all displayed vertically (scrollable)
- Number of columns = `calendar['days_per_week']` (dynamic!)
- Each row represents one week (or partial week)

**Styling:**
- **Current day text:** Emphasized (coral pink #F78080)
- **Holiday day background:** Light gold/amber color
- **Current day + holiday:** Both stylings applied

**Interactions:**
- **Click any day:** Sets current date to that month/day, saves to file immediately
- **Hover on holiday day:** Tooltip shows holiday name
- **Hover on holiday in list:** Tooltip shows holiday description

**Current Date Display at Top:**
- Format: `Deepwinter 15 (Winter)` (NO "Current Date:" label)
- If current date is a holiday, show holiday name and description below date
- Holiday name should be emphasized (coral pink)

**Holiday List at Bottom:**
- Simple format: `- Holiday Name - Month Day`
- If current date is a holiday, that holiday is emphasized
- Hover shows full description in tooltip

---

### 5. Overland Tab Changes

**Date Display (When Calendar Active with Date):**

```
General
    Deepwinter 15 (Winter)
    3 days
    Weather: Clear Skies 🔄
```

- NO "Current Date:" label
- Format: `{Month} {Day} ({Season})`
- Only month name is emphasized (coral pink)
- Placed at top of General section

**Holiday Display (If Current Date is Holiday):**

```
General
    Deepwinter 15 (Winter)
    Midwinter Festival - A week-long celebration marking the darkest point of winter...
    
    3 days
    Weather: Clear Skies 🔄
```

- Holiday name and full description on line below date
- Holiday name NOT emphasized
- Description in normal text

**Season Selection Logic:**
- **If calendar + date set:** NO season dropdown (season auto-detected from current month)
- **If calendar + no date:** Season dropdown shown + "No date set - set date via Calendar tab" message
- **If no calendar:** Season dropdown shown (current behavior)

---

### 6. Button Behaviors

**New Day Button (Overland Tab):**
1. Increments `config.generated_overland_days` by 1
2. **If calendar with date:** Advances calendar date by 1 day (wraps at month end)
3. Saves new date to calendar file
4. Generates new weather/encounters
5. Auto-detects season from (potentially new) current month

**Reset Button (Overland Tab):**
- Sets `config.generated_overland_days = 0`
- **Does NOT change calendar date**
- Calendar date is independent of reset

**Rationale:** Reset resets the "counter" but not the actual date

---

### 7. Date Advancement Logic

**Algorithm:**
```python
def advance_calendar_date(days: int = 1):
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
```

**Key:** Wraps at end of calendar (no year increment)

---

### 8. File Persistence

**What Gets Saved:**
- Only `current_date: {month: X, day: Y}` in calendar YAML

**When Saved:**
- User clicks a date in Calendar tab
- "New Day" button pressed in Overland tab

**How Saved:**
1. Update `config.calendar_data['current_date']`
2. Read full YAML file
3. Update `data['calendar']['current_date']`
4. Write YAML back to file (using `yaml.dump()`)

**File:** `Default Calendar.yaml` (same file as template)

---

### 9. Data Layer Implementation Status

**✅ COMPLETED:**

**config.py:**
- Added `calendar_data: Optional[Dict] = None`
- Added `calendar_month_lookup: Dict[str, int] = {}`

**data_loader.py:**
- Added `load_calendar_file() -> bool` (loads calendar, handles missing/blank files)
- Added `save_calendar_date(month: int, day: int) -> bool` (writes to file)
- Integrated `load_calendar_file()` into `load_all_data()`

**utils.py:**
- Added `get_calendar_date_string() -> str` (formats for display)
- Added `get_current_season() -> str` (auto-detect from month)
- Added `advance_calendar_date(days: int = 1) -> bool` (advance and save)
- Added `get_current_holiday() -> dict|None` (check if current date is holiday)

**Default Calendar.yaml:**
- Updated with `days_per_week: 6`
- Updated with `current_date: null`
- Contains 10 months (30 days each)
- Contains 8 holidays (2 per season)

---

### 10. UI Implementation Needed

**⏳ TO IMPLEMENT:**

**app.py - Calendar Tab:**
- Create new "Calendar" tab (conditionally shown)
- Render current date at top using `get_calendar_date_string()`
- If current holiday, display name and description below date
- Render all month grids:
  - Each month as separate section with month name
  - Grid with `calendar['days_per_week']` columns
  - Each day as clickable button
  - Apply styling to current day (text emphasis)
  - Apply styling to holiday days (background color)
  - Click handler: calls `save_calendar_date(month, day)` and refreshes
- Render holiday list at bottom
  - Simple list format
  - Emphasize current holiday
  - Tooltips on hover

**app.py - Overland Tab:**
- Add date display at top of General section
  - Use `get_calendar_date_string()`
  - Parse to emphasize month name only
- Add holiday display below date (if applicable)
  - Use `get_current_holiday()`
  - Show name and description
- Make season dropdown conditional:
  - If `config.calendar_data` exists and has current_date: NO dropdown, use `get_current_season()`
  - Otherwise: Show dropdown as before

**overland_logic.py:**
- Update `overland_generate()` or New Day handler to call `advance_calendar_date(1)` when calendar is active

---

### 11. Styling Requirements

**Colors:**
- **Current day text:** Coral pink `#F78080` (emphasis class)
- **Holiday day background:** Light gold/amber (subtle)
- **Current holiday text:** Coral pink `#F78080` (emphasis class)

**Grid Styling:**
- Use table or grid layout for calendar
- Ensure consistent sizing (days take different character widths)
- Maintain ultra-tight spacing principles
- Days should be clickable buttons

**Tooltips:**
- Holiday days: Show holiday name
- Holiday list items: Show full description

---

### 12. Helper Functions Available

```python
# In utils.py (already implemented)
get_calendar_date_string() -> str
# Returns: "Deepwinter 15 (Winter)" or "No date set - set date via Calendar tab" or ""

get_current_season() -> str
# Returns: "Winter" or "" if no calendar

advance_calendar_date(days: int = 1) -> bool
# Advances date by N days, wraps at end of calendar, saves to file

get_current_holiday() -> dict|None
# Returns: {'name': 'Midwinter Festival', 'description': '...', 'month': 'Deepwinter', 'day': 15}

# In data_loader.py (already implemented)
save_calendar_date(month: int, day: int) -> bool
# Saves current_date to calendar file
```

---

### 13. Testing Requirements

**Calendar Tab:**
- [ ] Tab only appears when calendar file has months
- [ ] All months displayed with correct number of columns
- [ ] Current day highlighted correctly
- [ ] Holiday days have gold background
- [ ] Click on day sets date and saves to file
- [ ] Date persists after app restart
- [ ] Holiday tooltips work on hover

**Overland Tab:**
- [ ] Date displays without "Current Date:" label
- [ ] Month name emphasized in coral pink
- [ ] Holiday shows below date when applicable
- [ ] Season dropdown hidden when calendar active with date
- [ ] Season dropdown shown when no calendar or no date
- [ ] New Day advances calendar date
- [ ] Reset does not change calendar date

**Edge Cases:**
- [ ] Calendar wraps correctly at end of year
- [ ] Works with different days_per_week values
- [ ] Handles missing calendar file gracefully
- [ ] Handles blank calendar file gracefully

---

## Important Constraints

1. **Dynamic Columns:** Calendar grid columns MUST equal `calendar['days_per_week']` (not hardcoded to 6)

2. **No Year Field:** Never display or track year anywhere

3. **Date Format:** Always `{Month} {Day} ({Season})` with NO "Current Date:" label in Overland tab

4. **File Writing:** Calendar file is the ONLY data file the application writes to

5. **Backward Compatibility:** Application must work perfectly without calendar file

6. **Season Auto-Detection:** When calendar with date exists, season comes from calendar (not user selection)

7. **Holiday Month References:** Holiday `month` field is a STRING matching month name (not index number)

8. **Emphasis Selective:** In date display, ONLY the month name gets emphasized (not the whole date)

9. **Grid Layout:** Each row in calendar grid represents one week based on days_per_week

10. **All Months Visible:** Display all months in Calendar tab vertically (not paginated)

---

## Example Calendar File

**File:** `Default Calendar.yaml`
- 10 months × 30 days = 300 days/year
- 6-day weeks
- 8 holidays (2 per season: Winter, Spring, Summer, Fall)
- Season distribution: 3 Winter, 2 Spring, 3 Summer, 2 Fall months

---

## References

**Specification:** See updated `TORCHCRAWL_SPECIFICATION.md` Section 6 (Calendar System) for complete details

**Implementation Guide:** See `CALENDAR_IMPLEMENTATION_SUMMARY.md` for step-by-step guide

**Sample Data:** See `Default Calendar.yaml` for working example

---

## Next Steps for Implementation

1. Check if calendar exists with `config.calendar_data is not None`
2. Create Calendar tab conditionally
3. Render calendar grids with dynamic columns
4. Implement date selection (click handlers)
5. Update Overland tab date display
6. Make season dropdown conditional
7. Integrate date advancement with New Day button
8. Test all three modes

---

**Key Takeaway:** Calendar is an optional layer on top of existing system. Application works perfectly without it, but when present, provides immersive date tracking with automatic season detection and visual date selection.
