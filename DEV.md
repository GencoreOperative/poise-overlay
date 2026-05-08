# Elden Ring Boss Poise Overlay System

The ambition for this project is to create a video driven model of the hidden Elden Ring boss poise meter. The goal is to calculate the poise damage the player is inflicting and then overlay that on the video so that we can understand how the poise meter changes throughout the match.

The project will work entirely based on a gameplay recording. Using the health bar, and additional information about the boss, weapon, and attack types, we can model the poise meter.

# Phases

The project will be broken up into three phases.
- Phase 1: Extraction of the health bar pixel data from the video
- Phase 2: Identification of the hit-data events from the video frames
- Phase 3: Calculation and generation of the poise bar information
- Phase 4: Conversion of the poise bar level into video overlay

# Phase 1

An FFMPEG command that will crop a gameplay video to just the health bar, and then convert the video into frame-by-frame images at a fixed frame rate, for example, 30 frames per second.

# Phase 2

A script that will examine the health bar in each frame and generate an output that captures the timestamp (MM:SS) for each hit event.

For example, two hits observed at 1 second and 3 seconds would look like this:
```
00:01
00:03
```
The user will then need to annotate this output to include the poise damage value that they delivered for each hit event. The user will be responsible for looking this information up.

# Phase 3

Now we will create a poise modelling script. This script will be given the following inputs:
- annotated hit-data file
- Boss total poise value
- Boss poise-regen value

With this information, the script must output, for each millisecond value, the calculated poise of the boss. For example:
```
1 120
2 120
3 120
...
1000 80
1001 80
1002 80
```

# Phase 4
The conversion of the millisecond poise calculation into a video overlay that will be shown on the video.
The recommendation is that we use an image generation capability to create new transparent frames with the poise bar rendered onto each frame.

Then the frames can be converted using FFMPEG into a video.
Finally, this video can then be overlayed onto the original video using FFMPEG.