#!/usr/bin/env python3

"""
Plot poise timeline from Phase 3 output.

Usage:
  python3 plot-poise.py <poise_file> [-o output.png] [--max-poise N]
"""

import sys
import argparse
from pathlib import Path


def load_timeline(path):
    """Load ms->poise values, downsampling to one point per second."""
    seconds = {}
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            ms = int(parts[0])
            poise = float(parts[1])
            sec = ms // 1000
            # Keep first value seen per second (= value at that exact second)
            if sec not in seconds:
                seconds[sec] = poise
    return seconds


def main():
    parser = argparse.ArgumentParser(description='Plot poise timeline')
    parser.add_argument('poise_file', help='Phase 3 poise output file')
    parser.add_argument('-o', '--output', help='Save plot to file (PNG/SVG/etc). '
                        'If omitted, displays interactively.')
    parser.add_argument('--max-poise', type=float, default=None,
                        help='Override max poise for y-axis (auto-detected if omitted)')
    args = parser.parse_args()

    try:
        import matplotlib
        import matplotlib.pyplot as plt
        import matplotlib.ticker as ticker
    except ImportError:
        print("matplotlib is required: pip install matplotlib", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {args.poise_file}...", file=sys.stderr)
    data = load_timeline(args.poise_file)

    if not data:
        print("No data found.", file=sys.stderr)
        sys.exit(1)

    times = sorted(data)
    poise_vals = [data[t] for t in times]

    max_poise = args.max_poise or max(poise_vals)
    duration_sec = max(times)

    # ── Figure ──────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(16, 5))

    ax.plot(times, poise_vals, linewidth=1.2, color='#4fc3f7', zorder=2)
    ax.fill_between(times, poise_vals, alpha=0.25, color='#4fc3f7', zorder=1)

    # Horizontal reference lines at 33% and 66%
    ax.axhline(max_poise * 0.66, color='yellow', linewidth=0.7, linestyle='--', alpha=0.6)
    ax.axhline(max_poise * 0.33, color='red',    linewidth=0.7, linestyle='--', alpha=0.6)

    # ── Axes ────────────────────────────────────────────────────────────────
    ax.set_ylim(0, max_poise * 1.05)
    ax.set_xlim(0, duration_sec)

    # X-axis: MM:SS labels
    def fmt_time(x, _):
        x = int(x)
        return f"{x // 60:02d}:{x % 60:02d}"

    ax.xaxis.set_major_locator(ticker.MultipleLocator(30))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(10))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(fmt_time))

    ax.yaxis.set_major_locator(ticker.MultipleLocator(max(1, round(max_poise / 10))))
    ax.grid(axis='both', which='major', alpha=0.2)
    ax.grid(axis='x', which='minor', alpha=0.08)

    ax.set_xlabel('Time', fontsize=11)
    ax.set_ylabel('Poise', fontsize=11)
    ax.set_title(f'Poise Timeline — {Path(args.poise_file).name}', fontsize=13)

    # Colour the background zones
    ax.axhspan(0,                max_poise * 0.33, alpha=0.04, color='red')
    ax.axhspan(max_poise * 0.33, max_poise * 0.66, alpha=0.04, color='yellow')
    ax.axhspan(max_poise * 0.66, max_poise * 1.05, alpha=0.04, color='green')

    # Annotate min poise value
    min_poise = min(poise_vals)
    min_sec   = times[poise_vals.index(min_poise)]
    ax.annotate(
        f'min {min_poise:.1f}',
        xy=(min_sec, min_poise),
        xytext=(min_sec + max(1, duration_sec // 40), min_poise + max_poise * 0.05),
        arrowprops=dict(arrowstyle='->', color='white', lw=0.8),
        color='white', fontsize=9,
    )

    fig.patch.set_facecolor('#1e1e2e')
    ax.set_facecolor('#1e1e2e')
    ax.tick_params(colors='#cccccc')
    ax.xaxis.label.set_color('#cccccc')
    ax.yaxis.label.set_color('#cccccc')
    ax.title.set_color('#eeeeee')
    for spine in ax.spines.values():
        spine.set_edgecolor('#444466')

    plt.tight_layout()

    if args.output:
        plt.savefig(args.output, dpi=150, bbox_inches='tight')
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        plt.show()


if __name__ == '__main__':
    main()
