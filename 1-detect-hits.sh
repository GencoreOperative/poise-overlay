#!/bin/bash

# Wrapper: Phase 1 + Phase 2
# Extract health bar frames from a video, detect hit events, and write a hit-data file.
# The user must then annotate the hit-data file with poise damage values before running
# create-overlay.sh.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] <video_file>

Detect boss hit events from an Elden Ring gameplay video (Phase 1 + Phase 2).

Extracts health bar frames, analyses them for hits, and writes a hit-data file.
You must annotate the hit-data file with poise damage values before running
create-overlay.sh.

OPTIONS:
  -o, --output FILE      Hit-data output file (default: <video_stem>-hits.txt)
  --fps N                Frame extraction rate (default: 30)
  --help                 Show this help

EXAMPLE:
  $(basename "$0") boss_fight.mp4
  # → writes boss_fight-hits.txt, then edit it to add damage values:
  #   00:23,18.72
  #   00:47,18.72
  $(basename "$0") boss_fight.mp4 -o my_hits.txt
EOF
}

FPS=30
VIDEO_FILE=""
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)   OUTPUT_FILE="$2"; shift 2 ;;
        --fps)         FPS="$2";         shift 2 ;;
        --help)        usage; exit 0 ;;
        -*) echo "Unknown option: $1"; usage; exit 1 ;;
        *)  VIDEO_FILE="$1"; shift ;;
    esac
done

if [[ -z "$VIDEO_FILE" ]]; then
    echo "Error: No video file specified."
    usage
    exit 1
fi

if [[ ! -f "$VIDEO_FILE" ]]; then
    echo "Error: Video file not found: $VIDEO_FILE"
    exit 1
fi

VIDEO_STEM="${VIDEO_FILE%.*}"
if [[ -z "$OUTPUT_FILE" ]]; then
    OUTPUT_FILE="${VIDEO_STEM}-hits.txt"
fi

# Temp dir for frames — always cleaned up on exit
FRAMES_DIR=$(mktemp -d)
trap 'echo "Cleaning up frames…"; rm -rf "$FRAMES_DIR"' EXIT

echo "╔══════════════════════════════════════╗"
echo "║  Elden Ring Poise — Hit Detection    ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "Video : $VIDEO_FILE"
echo "Output: $OUTPUT_FILE"
echo "FPS   : $FPS"
echo ""

# ── Phase 1: extract health bar frames ──────────────────────────────────────
echo "▶ Phase 1: Extracting health bar frames…"
bash "$SCRIPT_DIR/phase1-extract-health-bar.sh" \
    -o "$FRAMES_DIR" \
    -r "$FPS" \
    "$VIDEO_FILE"
echo ""

# ── Phase 2: detect hits ─────────────────────────────────────────────────────
echo "▶ Phase 2: Detecting hit events…"
python3 "$SCRIPT_DIR/phase2-detect-hits.py" \
    "$FRAMES_DIR" \
    -o "$OUTPUT_FILE"
echo ""

HIT_COUNT=$(grep -c '.' "$OUTPUT_FILE" 2>/dev/null || echo 0)
echo "✓ Done — $HIT_COUNT hit(s) detected."
echo ""
echo "Next step: annotate $OUTPUT_FILE with poise damage values, then run:"
echo "  2-create-overlay.sh $OUTPUT_FILE $VIDEO_FILE --boss-poise <N> --regen-timer <N> --regen-rate <N>"
