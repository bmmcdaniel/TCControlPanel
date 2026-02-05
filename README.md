# Torchcrawl GM Control Panel - NiceGUI Version

**A modern web-based GM tool with perfect spacing control.**

Migrated from Streamlit to NiceGUI to eliminate CSS fighting and achieve pixel-perfect layout.

## 🎯 Why NiceGUI?

**Problems with Streamlit:**
- ❌ CSS spacing impossible to control
- ❌ Constant fighting with framework styles
- ❌ Expandable content required complex workarounds
- ❌ Hours spent on spacing issues

**Advantages with NiceGUI:**
- ✅ **Perfect spacing** - Tailwind classes work as expected
- ✅ **Built-in expansion** - `ui.expansion()` component
- ✅ **Clean UI** - Modern, professional components
- ✅ **Still Python** - No HTML/CSS/JS required
- ✅ **Fast development** - Immediate refresh

## Features

### Overland Mode
- Day-by-day travel tracking
- Weather generation with seasonal variation
- 6 encounters per day (Dawn through Late Night)
- Expandable encounter details
- 50/50 overlay system (Road, River, Ruin)
- Rest check information with modifiers
- Individual regeneration buttons

### Site Mode
- 10-minute turn tracking
- Timer management with auto-expiration and warnings
- 6-slot encounter system (Current + 5 future slots)
- Expandable encounter details
- Inline timer creation
- Individual regeneration buttons

## Installation

### Prerequisites
- Python 3.9 or higher
- pip

### Quick Start

```bash
# 1. Navigate to directory
cd torchcrawl_nicegui

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python app.py
```

Application opens automatically at `http://localhost:8080`

### Verbose Mode
```bash
python app.py --verbose
```

## Using the Application

### Overland Mode

**Setup:**
1. Select Season (Spring, Summer, Autumn, Winter)
2. Select Zone (Flats, Shudds, Croch)
3. Select Overlay (Road, River, Ruin, or None)

**Actions:**
- **New Day** - Advance day counter and generate content
- **Regenerate All** - Regenerate without advancing day
- **Reset** - Return to Day 0

**Encounters:**
- Click encounter to expand (shows description + sparks)
- Click again to collapse
- Click 🔄 to regenerate that specific encounter

**Rest Check:**
- View camping DCs for current season
- Weather modifiers (shown only when applicable)
- Situational modifiers

### Site Mode

**Setup:**
1. Select Site Zone (Ruin, Cave, Dungeon)

**Actions:**
- **New Turn** - Advance 10 minutes
- **Regenerate All** - Regenerate current encounters
- **Reset** - Return to 0 minutes

**Timers:**
- Click ➕ to show timer form
- Enter name and duration
- Timers auto-decrement each turn
- Expired timers show ⚠️ in red
- Click ❌ to delete

**Encounters:**
- Current + next 5 upcoming encounters
- Auto-advance each turn
- Expandable like Overland mode

## Key Improvements Over Streamlit

### Spacing Control
✅ **Tailwind classes work perfectly**
- `mt-0` = margin-top: 0 (actually works!)
- `mb-1` = margin-bottom: 0.25rem
- `gap-2` = 0.5rem gap between elements

✅ **No CSS fighting**
- Every spacing value applies correctly
- No framework overrides
- Predictable behavior

✅ **Compact by default**
- Efficient use of screen space
- 2-3x more content visible
- Clean, professional appearance

### Better Components
✅ **Native expansion** - `ui.expansion()` built for this
✅ **Clean tables** - Easy to customize
✅ **Modern buttons** - Flat, dense options
✅ **Notifications** - Toast messages (not currently used)

### Professional UI
✅ **Consistent spacing** - Same system throughout
✅ **Clear hierarchy** - Proper heading sizes
✅ **Modern design** - Clean, contemporary look
✅ **Maximum density** - More info on screen

## Spacing Examples

### Perfect Encounter Spacing
```
Morning: Traveler ▼🔄
    Description: A fellow traveler...
    1. A merchant with broken wagon...
    2. A group of pilgrims...
    3. A lone wanderer...
                                      ← 0.75em gap
Afternoon: No Encounter 🔄
```

**Result:**
- Description tight against encounter line
- Sparks grouped together
- Clear separation before next encounter
- No excessive whitespace

### Clean Tables
```
Rest DCs for Spring
Unsheltered Camp  DC 15
Sheltered Camp  DC 10
Fortified Camp  DC 5
```

- No headers
- Tight spacing
- Monospace font for alignment
- Clean presentation

## Project Structure

```
torchcrawl_nicegui/
├── app.py                     # Main NiceGUI application
├── config.py                  # Global variables
├── models.py                  # Data classes (Encounter, Weather, Timer)
├── data_loader.py             # YAML/Excel data loading
├── overland_logic.py          # Overland mode functions
├── site_logic.py              # Site mode functions
├── utils.py                   # Utility functions
├── logger.py                  # Logging setup
├── requirements.txt           # Dependencies
├── README.md                  # This file
│
├── Data/
│   ├── Test Data Files.yaml
│   ├── Default Encounters.yaml
│   ├── Default Weathers.yaml
│   ├── Default Zones.yaml
│   ├── Default Rest Info.yaml
│   ├── Default Encounters By Zone.xlsx
│   └── Default Weather By Season.xlsx
│
└── logs/
    └── TCControlPanel.log     # Runtime logs
```

## Customization

All game data in `Data/` directory (YAML and Excel files).

**Add Encounters:**
Edit `Default Encounters.yaml` and `Default Encounters By Zone.xlsx`

**Add Zones:**
Edit `Default Zones.yaml` and update encounter tables

**Modify Weather:**
Edit `Default Weathers.yaml` and `Default Weather By Season.xlsx`

**Adjust Rest DCs:**
Edit `Default Rest Info.yaml`

## Sample Data

**9 Encounters:** Ankheg, Badger (Giant), Barrow-Wight, Traveler, Catamount, Bear, Bug (Giant), Frog (Giant), Gargoyle

**8 Zones:** 
- Overland: Flats, Shudds, Croch
- Overlay: Road, River, Ruin
- Site: Ruin, Cave, Dungeon

**6 Weather Types:** Clear, Misty, Gentle Rains, Heavy Rains, Thunderstorm, Heavy Snow

**4 Seasons:** Spring, Summer, Autumn, Winter

## GreyhawkGothic Font (Optional)

Title uses GreyhawkGothic font if installed.

**Installation:**
1. Obtain font file (.ttf or .otf)
2. **Windows:** Right-click → Install
3. **Mac:** Double-click → Install Font
4. **Linux:** Copy to ~/.fonts/, run `fc-cache -f -v`
5. Restart browser

**Without font:** Falls back to Grenze Gotisch, UnifrakturMaguntia, or serif.

## Logging

Activity logged to `logs/TCControlPanel.log`:
- Data file loading
- Day/turn advancement
- Weather/encounter generation
- Timer events
- Errors and warnings

## Troubleshooting

### Application Won't Start
- Check Python version: `python --version` (need 3.9+)
- Install dependencies: `pip install -r requirements.txt`
- Check logs: `logs/TCControlPanel.log`

### Data Files Not Found
- Run from `torchcrawl_nicegui/` directory
- Verify `Data/` folder contains all 7 files

### UI Not Updating
- Check browser console (F12) for errors
- Hard refresh: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
- Restart application

### Encounters Not Generating
- Check `Default Encounters By Zone.xlsx` has correct weights
- Verify zone encounter_chance percentages
- Check logs for generation errors

## NiceGUI Notes

### State Management
- Uses `app.storage.user` for persistent state
- Survives page reloads
- User-specific

### Reactivity
- `@ui.refreshable` decorator for sections
- Call `.refresh()` to update
- Manual control over when/what updates

### Styling
- Tailwind CSS classes for spacing
- Custom CSS via `ui.add_head_html()` if needed
- No framework fighting!

## Comparison: Streamlit vs NiceGUI

| Feature | Streamlit v3.1 | NiceGUI v1.0 |
|---------|----------------|--------------|
| Spacing Control | ❌ Terrible | ✅ Perfect |
| Expandable Content | 🔧 Workarounds | ✅ Built-in |
| CSS Customization | ❌ Fights you | ✅ Works |
| Development | ✅ Fast | ✅ Fast |
| Learning Curve | ✅ Very low | ✅ Low |
| Professional UI | ⚠️ Basic | ✅ Modern |
| Python-First | ✅ Yes | ✅ Yes |
| Your Sanity | 😤 Lost | 😊 Preserved |

## Version History

### NiceGUI Version 1.0 (February 4, 2026)
- Complete rewrite using NiceGUI framework
- Perfect spacing control with Tailwind CSS
- Native expandable encounters
- Clean, modern UI components
- All Streamlit functionality preserved
- Improved user experience
- **No more CSS fighting!**

### Previous Streamlit Versions
- v3.1: Final attempt at Streamlit spacing
- v3.0: Major UI redesign
- v2.2: Specification finalization

## Credits

- Application by Claude (Anthropic)
- Based on Torchcrawl specification
- Built with NiceGUI, Python, xarray, pandas
- **Migrated from Streamlit for sanity**

---

**Ready to GM with perfect spacing!** 🎲✨

**No more CSS nightmares. Just clean tools for your game.**
