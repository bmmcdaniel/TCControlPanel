# Quick Start Guide - Torchcrawl NiceGUI

## ⚡ 3-Minute Setup

### Step 1: Extract (10 seconds)
```bash
tar -xzf torchcrawl_nicegui.tar.gz
cd torchcrawl_nicegui
```

### Step 2: Install (1 minute)
```bash
pip install -r requirements.txt
```

### Step 3: Run (5 seconds)
```bash
python app.py
```

**Done!** Opens at `http://localhost:8080`

---

## ✅ First Test (2 minutes)

### Overland Mode
1. Click "New Day"
2. See day counter, weather, encounters
3. Click an encounter to expand
4. See description + sparks

### Site Mode
1. Switch to "Site" tab
2. Click ➕ next to "Timers"
3. Add a timer
4. Click "New Turn"
5. Watch timer count down

**Everything working?** You're ready to GM!

---

## 🎯 Key Differences from Streamlit

### Port Number
- **Streamlit:** `http://localhost:8501`
- **NiceGUI:** `http://localhost:8080`

### Refresh Behavior
- **Streamlit:** Entire page reloads
- **NiceGUI:** Only changed sections refresh

### Spacing
- **Streamlit:** Fighting CSS constantly
- **NiceGUI:** Perfect control, works as expected

---

## 💡 Pro Tips

### Overland Mode
- Change season/zone anytime
- Use overlays for mixed terrain
- Click 🔄 on individual encounters
- Expand multiple encounters at once

### Site Mode
- Set timers for torches, spells, etc.
- Expired timers show ⚠️ in red
- Encounters auto-advance each turn

### General
- Check `logs/TCControlPanel.log` for details
- Use `--verbose` flag for console output
- Customize data files in `Data/` folder

---

## 🐛 Quick Troubleshooting

**Won't start?**
```bash
pip install --upgrade nicegui
python app.py
```

**Port in use?**
Edit `app.py`, change `port=8080` to `port=8081`

**Data not loading?**
Check you're in `torchcrawl_nicegui/` directory

**Encounters not expanding?**
Hard refresh browser: Ctrl+F5

---

## 📚 Documentation

- **README.md** - Complete guide
- **logs/TCControlPanel.log** - Runtime logs
- **Data/** - All customizable game data

---

## 🎉 You're Done!

**The spacing issues are GONE.**
**The CSS fighting is OVER.**
**Your GM tool just works.**

Start generating content and enjoy! 🎲
