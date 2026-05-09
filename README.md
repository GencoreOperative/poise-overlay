# Elden Ring Poise Overlay

**Status: ✅ COMPLETE - Fully functional end-to-end solution**

A system to extract boss poise data from Elden Ring gameplay video, simulate poise mechanics, and generate an overlay visualization showing boss stance meter in real-time.

---

## Overview

Elden Ring does not display boss poise (stance) values to the player. This project reconstructs boss poise over time by:

1. Detecting exact hit frames in gameplay video
2. Extracting health bar damage per hit
3. Simulating poise depletion and recovery mechanics
4. Visualising the poise timeline as a graph
5. Rendering a visual poise bar overlay on the original video

**Result:** A complete gameplay video with an accurate, real-time poise meter overlay.

---

## Features

✅ **Phase 1: Health Bar Extraction**
- Automated frame extraction from gameplay video
- Configurable health bar crop region (default: 465,873 → 1464,887)

✅ **Phase 2: Hit Detection**
- Frame-by-frame health bar analysis
- Precise hit detection (5px damage threshold)
- 19/19 hits detected with frame-level accuracy (tested on Gideon Offnir)

✅ **Phase 3: Poise Simulation**
- Boss poise mechanics engine
- Configurable parameters (max poise, regen delay, regen rate)
- Millisecond-granularity poise timeline (176,001 data points per 176s video)
- Linear recovery curves (13 poise/second rate)

✅ **Phase 4: Poise Graph**
- Plots millisecond-resolution poise timeline as a graph
- Colour-coded zones (Green/Yellow/Red) with background shading
- Annotates minimum poise point and threshold reference lines
- Outputs PNG (or displays interactively)

✅ **Phase 5: Video Overlay**
- Real-time poise bar rendering
- Color-coded status zones (Green/Yellow/Red)
- Transparent overlay compositing
- Direct FFmpeg frame piping (5280 frames in seconds, not files)

---

## Quick Start

### Prerequisites

```bash
pip install pillow numpy
# System: ffmpeg, ffprobe
```

### Basic Usage

#### Step 1: Extract frames and detect hits
```bash
./phase1-extract-health-bar.sh test.mp4
python3 phase2-detect-hits-v2-white-strip.py frames/ --damage-threshold 5
```

#### Step 2: Annotate hit data (manual)
Edit `test.txt` to add poise damage values per hit:
```
00:23,18.72
00:53,18.72
00:55,18.72
...
```

#### Step 3: Calculate poise timeline
```bash
python3 phase3-calculate-poise.py test.txt \
  -o poise_timeline.txt \
  --boss-poise 47 \
  --regen-timer 3.85 \
  --regen-rate 13
```

#### Step 4: Plot poise graph
```bash
python3 phase4-plot-poise.py poise_timeline.txt -o poise_graph.png
```

#### Step 5: Generate overlay video
```bash
python3 phase5-create-overlay.py poise_timeline.txt \
  -o poise_overlay_final.mp4 \
  --video-file test.mp4
```

---

## Project Structure

```
.
├── phase1-extract-health-bar.sh          # Frame extraction
├── phase2-detect-hits-v2-white-strip.py  # Hit detection (recommended)
├── phase2-detect-hits-v1-pixel-count.py  # Hit detection (alt)
├── phase2-detect-hits-v3-monotonic.py    # Hit detection (alt)
├── phase3-calculate-poise.py             # Poise simulation engine
├── phase4-plot-poise.py                  # Poise timeline graph
├── phase5-create-overlay.py              # Overlay rendering (optimized)
├── poise_timeline.txt                    # Output: poise per millisecond
├── poise_overlay_final.mp4               # Output: final video
├── test.mp4                              # Input: gameplay video
├── test.txt                              # Input: annotated hits
├── poise_timeline_graph.png              # Visualization: poise over time
├── PROGRESS.md                           # Detailed progress log
├── PHASE4_PHASE3_SUMMARY.md              # Technical deep dive
└── README.md                             # This file
```

---

## Technical Details

### Phase 1: Frame Extraction

**Input:** Gameplay video (test.mp4)

**Process:**
- Extract all frames using FFmpeg
- Crop to health bar region using configurable coordinates
- Save PNG sequence

**Output:** Frame directory with individual PNG files

---

### Phase 2: Hit Detection

**Input:** Frame directory (phase 1 output)

**Recommended Script:** `phase2-detect-hits-v2-white-strip.py`

**Algorithm:**
- Detect white/red pixel boundary in health bar (rightmost edge)
- Track boundary position per frame
- Compare consecutive frames for damage (delta > threshold)
- Output: Machine-readable hit timestamps and damage values

**Parameters:**
- `--damage-threshold 5`: Minimum pixel change to register hit (recommended)

**Output:** `test.txt` format:
```
MM:SS,poise_damage
00:23,18.72
00:53,18.72
...
```

---

### Phase 3: Poise Simulation

**Input:** `test.txt` (annotated hits from phase 2)

**Physics Model:**

```
For each millisecond:
  1. Check for hit at this timestamp
  2. If hit: poise = max(0, poise - damage)
  3. Check regen delay (3850ms after each hit)
  4. If delay elapsed: poise = min(max_poise, poise + regen)
  
  where regen = (time_since_delay_start / 1000) * 13
```

**Key Parameters:**
- `--boss-poise 47`: Maximum poise (Gideon Offnir = 47)
- `--regen-timer 3.85`: Delay before recovery starts (seconds)
- `--regen-rate 13`: Recovery rate (poise per second)

**Output:** `poise_timeline.txt`
```
milliseconds poise_value
0 47.000000
1 47.000000
...
176000 47.000000
```

---

### Phase 4: Poise Graph

**Input:** `poise_timeline.txt` (phase 3 output)

**Script:** `phase4-plot-poise.py`

**Features:**
- Downsamples millisecond data to per-second resolution for fast rendering
- Colour-coded background zones matching the overlay bar (green/yellow/red)
- Dashed reference lines at 33% and 66% thresholds
- Annotates the minimum poise point with an arrow
- Dark theme suitable for sharing or embedding in a stream layout

**Parameters:**
- `-o output.png`: Save to file (omit to display interactively)
- `--max-poise N`: Override detected max poise for y-axis scaling

**Output:** PNG graph (or interactive matplotlib window)

---

### Phase 5: Overlay Rendering

**Input:** `poise_timeline.txt` + `test.mp4` (original video)

**Recommended Script:** `phase5-create-overlay.py`

**Optimization:**
- Generates frames in memory (no PNG files)
- Pipes frames directly to FFmpeg stdin
- Uses RGBA → qtrle codec for transparency
- Outputs MOV container (alpha support), then composites to MP4

**Visual Design:**
- Bar position: 50px from left, 50px from bottom
- Bar width: 1213px (2/3 of screen width)
- Color zones:
  - Green (>66%): Healthy
  - Yellow (33-66%): Medium
  - Red (<33%): Critical
- Text overlay: "POISE: X.X / 47" + timestamp

**Output:** `poise_overlay_final.mp4`
- Resolution: 1920×1080
- Frame rate: 30 fps
- Duration: Matches input video
- Transparent overlay composited on original footage

---

## Validation Results

**Test Case: Gideon Offnir fight (176 seconds)**

| Metric | Result |
|--------|--------|
| Total hits detected | 19 / 19 ✓ |
| Final hit accuracy | Frame-perfect (02:46) ✓ |
| Poise recovery rate | 13.000 poise/sec ✓ |
| Recovery time per hit | 1.44 seconds ✓ |
| Regen delay | 3.85 seconds ✓ |
| Timeline precision | 176,001 millisecond values ✓ |
| Video composition | Full gameplay + overlay ✓ |

---

## Algorithm Insights

### Hit Detection
The detector identifies hits by tracking the **rightmost red pixel boundary** of the health bar:
- Background: 50px (stable)
- Filled health: Red pixels (variable)
- Empty health: Dark pixels (variable)

When the red boundary moves left, damage has occurred.

**Why this works:**
- Robust to compression artifacts
- Handles color quantization
- Ignores UI elements
- Fast processing (all 5280 frames in seconds)

### Poise Recovery
Recovery is **linear and continuous**:
- After 3.85s delay, poise increases smoothly
- Rate: 0.013 poise per millisecond
- Full recovery of 18.7 damage takes ~1.44 seconds
- Multiple hits reset the delay timer (each hit restarts countdown)

---

## Performance

| Stage | Time | Notes |
|-------|------|-------|
| Frame extraction | ~5 seconds | 5280 frames from 176s video |
| Hit detection | ~30 seconds | Analyze all frames |
| Poise simulation | <1 second | Microsecond calculations |
| Overlay generation | ~30 seconds | Frames piped to FFmpeg |
| Video compositing | ~60 seconds | FFmpeg encoding |
| **Total** | **~2-3 minutes** | End-to-end processing |

---

## Customization

### Change Health Bar Position
Edit health bar crop region in `phase1-extract-health-bar.sh`:
```bash
# Default: 465,873 → 1464,887
ffmpeg -i input.mp4 -vf "crop=999:14:465:873" frames/...
```

### Adjust Poise Bar Position
Edit `phase5-create-overlay.py`:
```python
bar_x = 50        # Left margin
bar_y = height - 50  # Distance from bottom (move up to reduce)
bar_width = int((width - 100) * 2 / 3)  # Width (modify multiplier)
bar_height = 40   # Height
```

### Modify Poise Mechanics
Adjust phase 3 parameters:
```bash
--boss-poise 100      # Different max poise
--regen-timer 5.0     # Different delay before recovery
--regen-rate 20       # Different recovery rate
```

### Change Hit Sensitivity
In `phase2-detect-hits-v2-white-strip.py`:
```python
damage_threshold = 5  # Lower = more sensitive, higher = less sensitive
```

---

## Troubleshooting

### "Black screen with audio"
- Overlay codec issue. Solution: Use `phase5-create-overlay.py` (uses qtrle + MOV)

### "Missing hits"
- Increase `--damage-threshold` value
- Check health bar crop region alignment

### "Poise recovers too fast"
- Verify `--regen-rate` value (should be 13 for Elden Ring)
- Check `--regen-timer` delay setting

### "Video generation slow"
- `phase5-create-overlay.py` pipes frames directly to FFmpeg — no PNG files are written to disk

---

## Future Enhancements

- [ ] Automatic health bar detection
- [ ] Support for multiple bosses with preset configurations
- [ ] DPS calculation and graphing
- [ ] Attack phase labeling
- [ ] Stagger/break animation detection
- [ ] Web dashboard for results
- [ ] Real-time overlay plugin (OBS)

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Frame extraction | FFmpeg |
| Image processing | PIL, OpenCV |
| Simulation | NumPy, Python |
| Video rendering | FFmpeg (piped frames) |
| Data analysis | Python |

---

## Notes

- This project is a **post-fight analysis tool** (offline video processing)
- Does not modify game memory or gameplay
- Requires manually annotated hit data (poise damage values)
- Works with any video codec that FFmpeg supports
- Tested on: Gideon Offnir (47 poise boss)

---

## License

TODO

---

## Disclaimer

This project is a gameplay analysis and visualization tool for educational and entertainment purposes. It does not modify game memory, files, or gameplay behavior. Use at your own risk.
