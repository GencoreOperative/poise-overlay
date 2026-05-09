#!/bin/bash

# Wrapper: Phase 3 + Phase 4 + Phase 5
# Given annotated hit-data, simulate poise, plot the timeline graph, and
# composite a poise bar overlay onto the original video.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] <hits_file> <video_file>

Simulate poise, plot the timeline, and generate an overlay video (Phase 3–5).

REQUIRED OPTIONS:
  --boss-poise N         Boss maximum poise value (e.g. 47 for Gideon Offnir)
  --regen-timer N        Seconds before poise recovery starts (e.g. 3.85)
  --regen-rate N         Poise recovered per second (e.g. 13)

OPTIONAL:
  -o, --output FILE      Output video file (default: <video_stem>-overlay.mp4)
  --stagger-window N     Seconds poise stays at 0 after stagger before resetting (default: 6.0)
  --fps N                Video frame rate (default: 30)
  --keep-timeline        Keep the intermediate poise timeline file
  --help                 Show this help

EXAMPLE:
  $(basename "$0") boss_fight-hits.txt boss_fight.mp4 \\
      --boss-poise 47 --regen-timer 3.85 --regen-rate 13

  # With stagger reset modelling:
  $(basename "$0") boss_fight-hits.txt boss_fight.mp4 \\
      --boss-poise 120 --regen-timer 3.85 --regen-rate 13 --stagger-window 3.0
EOF
}

HITS_FILE=""
VIDEO_FILE=""
OUTPUT_FILE=""
BOSS_POISE=""
REGEN_TIMER=""
REGEN_RATE=""
STAGGER_WINDOW=""
FPS=30
KEEP_TIMELINE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --boss-poise)    BOSS_POISE="$2";      shift 2 ;;
        --regen-timer)   REGEN_TIMER="$2";     shift 2 ;;
        --regen-rate)    REGEN_RATE="$2";      shift 2 ;;
        --stagger-window) STAGGER_WINDOW="$2"; shift 2 ;;
        -o|--output)     OUTPUT_FILE="$2";     shift 2 ;;
        --fps)           FPS="$2";          shift 2 ;;
        --keep-timeline) KEEP_TIMELINE=true; shift ;;
        --help)          usage; exit 0 ;;
        -*)  echo "Unknown option: $1"; usage; exit 1 ;;
        *)
            if [[ -z "$HITS_FILE" ]]; then
                HITS_FILE="$1"
            elif [[ -z "$VIDEO_FILE" ]]; then
                VIDEO_FILE="$1"
            else
                echo "Unexpected argument: $1"; usage; exit 1
            fi
            shift ;;
    esac
done

# Validate required args
ERRORS=()
[[ -z "$HITS_FILE" ]]   && ERRORS+=("Missing: <hits_file>")
[[ -z "$VIDEO_FILE" ]]  && ERRORS+=("Missing: <video_file>")
[[ -z "$BOSS_POISE" ]]  && ERRORS+=("Missing: --boss-poise")
[[ -z "$REGEN_TIMER" ]] && ERRORS+=("Missing: --regen-timer")
[[ -z "$REGEN_RATE" ]]  && ERRORS+=("Missing: --regen-rate")

if [[ ${#ERRORS[@]} -gt 0 ]]; then
    for e in "${ERRORS[@]}"; do echo "Error: $e"; done
    echo ""
    usage
    exit 1
fi

[[ ! -f "$HITS_FILE" ]]  && { echo "Error: Hits file not found: $HITS_FILE";  exit 1; }
[[ ! -f "$VIDEO_FILE" ]] && { echo "Error: Video file not found: $VIDEO_FILE"; exit 1; }

VIDEO_STEM="${VIDEO_FILE%.*}"
if [[ -z "$OUTPUT_FILE" ]]; then
    OUTPUT_FILE="${VIDEO_STEM}-overlay.mp4"
fi

# Derive intermediate file names alongside the output
OUT_DIR=$(dirname "$OUTPUT_FILE")
OUT_STEM=$(basename "${OUTPUT_FILE%.*}")
TIMELINE_FILE="${OUT_DIR}/${OUT_STEM}-timeline.txt"
GRAPH_FILE="${OUT_DIR}/${OUT_STEM}-graph.png"

echo "╔══════════════════════════════════════╗"
echo "║  Elden Ring Poise — Overlay Creator  ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "Hits file   : $HITS_FILE"
echo "Video       : $VIDEO_FILE"
echo "Boss poise  : $BOSS_POISE"
echo "Regen timer : ${REGEN_TIMER}s"
echo "Regen rate  : $REGEN_RATE poise/s"
[[ -n "$STAGGER_WINDOW" ]] && echo "Stagger win : ${STAGGER_WINDOW}s"
echo "Output      : $OUTPUT_FILE"
echo ""

# ── Phase 3: calculate poise timeline ────────────────────────────────────────
echo "▶ Phase 3: Calculating poise timeline…"
PHASE3_ARGS=("$HITS_FILE" -o "$TIMELINE_FILE" --boss-poise "$BOSS_POISE" --regen-timer "$REGEN_TIMER" --regen-rate "$REGEN_RATE")
[[ -n "$STAGGER_WINDOW" ]] && PHASE3_ARGS+=(--stagger-window "$STAGGER_WINDOW")
python3 "$SCRIPT_DIR/phase3-calculate-poise.py" "${PHASE3_ARGS[@]}"
echo ""

# ── Phase 4: plot poise graph ─────────────────────────────────────────────────
echo "▶ Phase 4: Plotting poise graph…"
python3 "$SCRIPT_DIR/phase4-plot-poise.py" \
    "$TIMELINE_FILE" \
    -o "$GRAPH_FILE" \
    --max-poise "$BOSS_POISE"
echo ""

# ── Phase 5: generate overlay video ──────────────────────────────────────────
echo "▶ Phase 5: Generating overlay video…"
python3 "$SCRIPT_DIR/phase5-create-overlay.py" \
    "$TIMELINE_FILE" \
    -o "$OUTPUT_FILE" \
    --video-file "$VIDEO_FILE" \
    --fps "$FPS" \
    --max-poise "$BOSS_POISE"
echo ""

# Optionally clean up timeline file
if [[ "$KEEP_TIMELINE" == false ]]; then
    rm -f "$TIMELINE_FILE"
    echo "ℹ Timeline file removed (use --keep-timeline to retain it)"
fi

echo ""
echo "✓ Complete!"
echo "  Graph  : $GRAPH_FILE"
echo "  Video  : $OUTPUT_FILE"
