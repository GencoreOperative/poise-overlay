# Phase 3: Poise State Model

## Overview

The poise timeline is computed **per-millisecond** across the full video duration. At each tick the model applies hits, then evaluates regeneration, producing a single `(ms, poise)` value written to the output file.

---

## Parameters

| Parameter | CLI flag | Description |
|---|---|---|
| `max_poise` | `--boss-poise` | Poise ceiling; poise is always ≤ this value |
| `regen_timer` | `--regen-timer` | Seconds after the **most recent hit** before regen begins |
| `regen_rate` | `--regen-rate` | Poise recovered per second once regen is active |

---

## State Variables

| Variable | Initial value | Updated when |
|---|---|---|
| `poise` | `max_poise` | Hit received or regen tick |
| `last_hit_ms` | `-∞` | Each time a hit is processed |
| `poise_at_last_hit` | `max_poise` | Each time a hit is processed |

---

## Per-Millisecond Logic

For every millisecond `ms` from `0` to `last_hit_time + 10 000`:

```
1. HIT CHECK
   If a hit is recorded at exactly this ms:
     poise           = max(0, poise - damage)
     poise_at_last_hit = poise          ← snapshot taken *after* damage applied
     last_hit_ms     = ms

2. REGEN CHECK
   time_since_hit = ms - last_hit_ms
   If time_since_hit >= regen_timer_ms:
     regen_duration = time_since_hit - regen_timer_ms
     poise = min(max_poise, poise_at_last_hit + regen_duration * regen_rate_per_ms)

3. RECORD
   Append (ms, poise) to timeline
```

> **Key detail:** Regen is computed as an absolute offset from `poise_at_last_hit`, not
> accumulated incrementally. This prevents floating-point drift and means the value at any
> tick is fully determined by `poise_at_last_hit`, `last_hit_ms`, and the current `ms`.

---

## State Diagram

```
         ┌──────────────────────────────────────────────┐
         │               FULL                           │
         │        poise == max_poise                    │
         └──────────────┬───────────────────────────────┘
                        │ hit received
                        ▼
         ┌──────────────────────────────────────────────┐
         │            DAMAGED / WAITING                 │
         │  time_since_hit < regen_timer                │◄──── hit received (resets timer)
         │  poise held constant                         │
         └──────────────┬───────────────────────────────┘
                        │ time_since_hit >= regen_timer
                        ▼
         ┌──────────────────────────────────────────────┐
         │            REGENERATING                      │
         │  poise rising at regen_rate/sec from         │◄──── hit received (resets to DAMAGED)
         │  poise_at_last_hit baseline                  │
         └──────────────┬───────────────────────────────┘
                        │ poise reaches max_poise
                        └────────────────────────────► FULL
```

---

## Transition Rules

| From | Event | To | Effect |
|---|---|---|---|
| Any | Hit received | DAMAGED / WAITING | `poise -= damage` (floor 0); `poise_at_last_hit` and `last_hit_ms` updated |
| DAMAGED / WAITING | `time_since_hit >= regen_timer` | REGENERATING | Regen calculation activates |
| REGENERATING | Hit received | DAMAGED / WAITING | Timer resets; new `poise_at_last_hit` snapshot taken at reduced poise |
| REGENERATING | `poise == max_poise` | FULL | Regen capped by `min(max_poise, …)` |
| FULL | Hit received | DAMAGED / WAITING | Normal hit processing |

---

## Important Behaviours

### Regen timer always resets on hit
Each new hit restarts the `regen_timer` countdown from zero. Rapid consecutive hits keep the boss perpetually in the **WAITING** state, delaying recovery entirely.

### Hit and regen on the same millisecond
The hit check runs **before** the regen check within the same tick. If a hit occurs at `ms = T`, `time_since_hit` evaluates to `0`, which is always less than `regen_timer_ms` (assumed > 0), so regen never fires on the same tick as a hit.

### Only one hit processed per millisecond
The parser converts timestamps from `MM:SS` (1-second resolution), so two hits annotated at the same second land on the same millisecond value. The current implementation processes **only the first** hit at any given millisecond; the second would be silently skipped. Annotating distinct seconds avoids this.

### Poise floor and ceiling
- Floor: `max(0, poise - damage)` — poise cannot go negative.
- Ceiling: `min(max_poise, …)` — poise cannot exceed the boss's maximum.

---

## Example (Gideon, default settings)

```
max_poise   = 47
regen_timer = 3.85 s  (3850 ms)
regen_rate  = 13 poise/sec  (0.013 poise/ms)

t=0 ms      poise = 47.0   (FULL)
t=23000 ms  hit −18.72     poise = 28.28  → DAMAGED/WAITING
t=26850 ms  regen starts   poise climbs from 28.28 at 0.013/ms
t=26851 ms                 poise ≈ 28.293
...
t=30840 ms                 poise ≈ 28.28 + (30840−26850)*0.013 = 28.28 + 51.87 → capped at 47.0  → FULL
```
