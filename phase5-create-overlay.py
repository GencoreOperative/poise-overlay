#!/usr/bin/env python3

"""
Phase 4 Optimized: Create visual poise bar overlay and composite with original video.

This script:
1. Reads poise timeline (millisecond-by-millisecond poise values)
2. Generates overlay frames in memory
3. Pipes frames directly to FFmpeg (no disk I/O for PNG files)
4. Overlays poise bar video onto original gameplay video

Much faster than generating 5000+ PNG files to disk.
"""

import sys
import argparse
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io


def load_poise_timeline(poise_file):
    """Load poise timeline (ms poise_level per line)."""
    timeline = {}
    with open(poise_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            ms = int(parts[0])
            poise = float(parts[1])
            timeline[ms] = poise
    return timeline


def create_poise_bar_frame(width, height, current_poise, max_poise, frame_num):
    """
    Create a transparent frame with poise bar visualization.
    Returns: PIL Image with transparency (RGBA)
    """
    frame = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)
    
    # Poise bar configuration
    bar_x = 50
    bar_y = height - 50  # Moved up 50px (was height - 100)
    bar_width = int((width - 100) * 2 / 3)  # Shortened by 1/3rd
    bar_height = 40
    
    # Calculate poise percentage
    pct = max(0, min(100, (current_poise / max_poise) * 100))
    
    # Color based on poise level
    if pct > 66:
        bar_color = (0, 255, 0, 200)  # Green - healthy
        text_color = (0, 255, 0, 255)
    elif pct > 33:
        bar_color = (255, 255, 0, 200)  # Yellow - medium
        text_color = (255, 255, 0, 255)
    else:
        bar_color = (255, 0, 0, 200)  # Red - low
        text_color = (255, 0, 0, 255)
    
    # Draw background box
    draw.rectangle(
        [(bar_x - 5, bar_y - 5), (bar_x + bar_width + 5, bar_y + bar_height + 5)],
        outline=(255, 255, 255, 200),
        width=2
    )
    
    # Draw poise bar
    filled_width = int(bar_width * pct / 100)
    draw.rectangle(
        [(bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height)],
        fill=bar_color
    )
    
    # Draw remaining bar (empty)
    draw.rectangle(
        [(bar_x + filled_width, bar_y), (bar_x + bar_width, bar_y + bar_height)],
        fill=(50, 50, 50, 100)
    )
    
    # Draw text: "POISE: 28.3 / 47"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    text = f"POISE: {current_poise:.1f} / {max_poise:.0f}"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = bar_x + (bar_width - text_width) // 2
    text_y = bar_y + (bar_height - 24) // 2
    
    draw.text((text_x, text_y), text, fill=text_color, font=font)
    
    # Draw timestamp
    try:
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        font_small = ImageFont.load_default()
    
    mm = (frame_num * 1000 // 60) // 60000
    ss = ((frame_num * 1000 // 60) % 60000) // 1000
    timestamp = f"{mm:02d}:{ss:02d}"
    
    draw.text((bar_x, bar_y - 40), timestamp, fill=(200, 200, 200, 255), font=font_small)
    
    return frame


def frame_to_bytes(image):
    """Convert PIL Image to raw RGBA bytes for FFmpeg stdin."""
    # Keep RGBA format to preserve alpha channel for transparency
    return image.tobytes()


def main():
    parser = argparse.ArgumentParser(
        description='Phase 5: Create poise bar overlay and composite with video',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
EXAMPLES:
  # Composite with original video (frames piped directly to FFmpeg)
  %(prog)s poise_timeline.txt -o output.mp4 --video-file test.mp4
        '''
    )
    
    parser.add_argument('poise_file', help='Poise timeline file (from Phase 3)')
    parser.add_argument('-o', '--output', required=True, help='Output video file')
    parser.add_argument('--video-file', required=True, help='Original video file for dimensions and compositing')
    parser.add_argument('--fps', type=int, default=30, help='Frame rate (default: 30)')
    parser.add_argument('--max-poise', type=float, default=None,
                        help='Maximum poise value for bar scaling (default: auto-detected from timeline)')
    
    args = parser.parse_args()
    
    try:
        # Load poise timeline
        print(f"Loading poise timeline from {args.poise_file}...", file=sys.stderr)
        timeline = load_poise_timeline(args.poise_file)
        
        if not timeline:
            print("✗ No poise data found", file=sys.stderr)
            sys.exit(1)
        
        max_time = max(timeline.keys())
        max_frames = int(max_time / 1000 * args.fps)
        
        print(f"✓ Loaded {len(timeline)} poise values (duration: {max_time/1000:.1f}s)", file=sys.stderr)
        
        # Get video dimensions
        print(f"Getting video dimensions from {args.video_file}...", file=sys.stderr)
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height', '-of', 'csv=p=0',
             args.video_file],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            print(f"✗ Error reading video: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        
        width, height = map(int, result.stdout.strip().split(','))
        print(f"✓ Video dimensions: {width}x{height}", file=sys.stderr)
        
        # Generate overlay frames and pipe to FFmpeg
        print(f"\nGenerating and piping {max_frames} overlay frames to FFmpeg...", file=sys.stderr)
        
        max_poise = args.max_poise if args.max_poise is not None else max(timeline.values())
        print(f"✓ Max poise: {max_poise:.1f}", file=sys.stderr)
        
        # Start FFmpeg process for overlay video creation (use MOV container for alpha)
        overlay_video_mov = Path(args.output).parent / f"{Path(args.output).stem}_overlay.mov"
        
        ffmpeg_overlay_cmd = [
            'ffmpeg', '-y',
            '-f', 'rawvideo',
            '-pix_fmt', 'rgba',
            '-s', f'{width}x{height}',
            '-framerate', str(args.fps),
            '-i', 'pipe:',
            '-c:v', 'qtrle',
            str(overlay_video_mov)
        ]
        
        overlay_proc = subprocess.Popen(
            ffmpeg_overlay_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=None  # pass FFmpeg output directly to terminal
        )
        
        try:
            for frame_num in range(max_frames):
                if (frame_num + 1) % 500 == 0:
                    print(f"  Frame {frame_num + 1}/{max_frames}", file=sys.stderr)
                
                # Get poise value for this frame
                frame_ms = int(frame_num * 1000 / args.fps)
                
                if frame_ms in timeline:
                    current_poise = timeline[frame_ms]
                else:
                    prev_ms = max([ms for ms in timeline.keys() if ms <= frame_ms], default=0)
                    if prev_ms in timeline:
                        current_poise = timeline[prev_ms]
                    else:
                        current_poise = max_poise
                
                # Create frame and convert to bytes
                frame = create_poise_bar_frame(width, height, current_poise, max_poise, frame_num)
                frame_bytes = frame_to_bytes(frame)
                
                # Write to FFmpeg stdin
                overlay_proc.stdin.write(frame_bytes)
            
            overlay_proc.stdin.close()
            overlay_proc.wait()
            
            if overlay_proc.returncode != 0:
                print(f"✗ Error creating overlay video (see FFmpeg output above)", file=sys.stderr)
                sys.exit(1)
            
            print(f"✓ Created overlay video: {overlay_video_mov}", file=sys.stderr)
            
        except Exception as e:
            overlay_proc.kill()
            raise e
        
        # Composite: overlay poise video onto original
        print(f"Compositing overlay onto original video: {args.output}", file=sys.stderr)
        
        result = subprocess.run([
            'ffmpeg', '-y',
            '-i', args.video_file,
            '-i', str(overlay_video_mov),
            '-filter_complex', '[0:v][1:v]overlay=0:0[out]',
            '-map', '[out]', '-map', '0:a', '-c:a', 'aac',
            args.output
        ], stdout=subprocess.DEVNULL)
        
        if result.returncode != 0:
            print(f"✗ Error compositing video (see FFmpeg output above)", file=sys.stderr)
            sys.exit(1)
        
        print(f"✓ Composited video saved to: {args.output}", file=sys.stderr)
        
        overlay_video_mov.unlink()
        print(f"✓ Cleaned up temporary overlay: {overlay_video_mov}", file=sys.stderr)
        print("\n✓ Phase 5 complete!", file=sys.stderr)
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
