#!/bin/bash

# Phase 1: Extract Health Bar from Elden Ring Gameplay Video
# This script crops a gameplay video to the health bar region and extracts frames

set -euo pipefail

usage() {
    cat << EOF
Usage: $0 [OPTIONS] <video_file>

Extract health bar frames from an Elden Ring gameplay video.

OPTIONS:
  -o, --output DIR       Output directory for frames (default: ./frames)
  -r, --rate FPS         Frame rate to extract (default: 30)
  -x, --crop-x X         X coordinate of crop region (default: 0)
  -y, --crop-y Y         Y coordinate of crop region (default: 0)
  -w, --crop-w WIDTH     Width of crop region (default: full width)
  -h, --crop-h HEIGHT    Height of crop region (default: 100)
  --help                 Show this help message

EXAMPLE:
  # Extract health bar at 30 fps (common for 1080p Elden Ring)
  $0 -x 50 -y 40 -w 400 -h 60 -o frames gameplay.mp4

  # For 1920x1080 video with UI at top-left:
  $0 -x 0 -y 0 -w 1920 -h 100 -o frames gameplay.mp4
EOF
}

# Default values (Elden Ring boss health bar position for 1920x1080)
OUTPUT_DIR="./frames"
FRAME_RATE=30
CROP_X=465
CROP_Y=873
CROP_W=999
CROP_H=7
VIDEO_FILE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -r|--rate)
            FRAME_RATE="$2"
            shift 2
            ;;
        -x|--crop-x)
            CROP_X="$2"
            shift 2
            ;;
        -y|--crop-y)
            CROP_Y="$2"
            shift 2
            ;;
        -w|--crop-w)
            CROP_W="$2"
            shift 2
            ;;
        -h|--crop-h)
            CROP_H="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            VIDEO_FILE="$1"
            shift
            ;;
    esac
done

if [[ -z "$VIDEO_FILE" ]]; then
    echo "Error: No video file specified"
    usage
    exit 1
fi

if [[ ! -f "$VIDEO_FILE" ]]; then
    echo "Error: Video file not found: $VIDEO_FILE"
    exit 1
fi

# Get video dimensions if crop width not specified
if [[ -z "$CROP_W" ]]; then
    CROP_W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of default=noprint_wrappers=1:nokey=1 "$VIDEO_FILE")
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "Extracting health bar from: $VIDEO_FILE"
echo "Video resolution: $CROP_W x $CROP_H (crop from [$CROP_X, $CROP_Y])"
echo "Frame rate: $FRAME_RATE fps"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Extract frames using FFMPEG
# The crop filter format is: crop=width:height:x:y
ffmpeg -i "$VIDEO_FILE" \
    -vf "crop=$CROP_W:$CROP_H:$CROP_X:$CROP_Y,fps=$FRAME_RATE" \
    -q:v 2 \
    "$OUTPUT_DIR/frame_%06d.png"

echo ""
echo "✓ Health bar extraction complete!"
frame_count=$(ls "$OUTPUT_DIR"/frame_*.png 2>/dev/null | wc -l)
echo "✓ Extracted $frame_count frames to $OUTPUT_DIR"
