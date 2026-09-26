# CMW Beat VJ

Plays the clips in this repo full screen and **cuts between them on the beat** of whatever you're playing in Serato. It also adds beat effects (flash, zoom pulse, color hits, stutter, strobe) and a CMW logo. Run it on your DJ laptop, then AirPlay it or send it over HDMI to a TV or projector.

It runs in a browser. The only thing to install is [Node.js](https://nodejs.org) (18 or newer).

## Start it

```bash
node vj/server.js
```

Then open **http://localhost:8080** in Chrome (or Safari on a Mac). By default it uses every `.mp4` in the repo root. To use another folder, run `CLIPS_DIR=/path/to/folder node vj/server.js`, or click **Load folder…** in the panel.

## Syncing to Serato: pick one

### A. Ableton Link (tightest, follows Serato's beat grid)
1. Download **Carabiner** from https://github.com/Deep-Symmetry/carabiner/releases (free, open source, has Mac and Windows builds) and run it. It's a small bridge that lets the browser see Link.
2. In Serato DJ Pro, turn on **Ableton Link** (Setup, then the Link/sync settings; you need a Serato version that supports Link).
3. In the VJ panel, choose **Sync → Link**. The status should read `Locked to Link · 1 peer`.
4. Press **Enter** on a downbeat once so beat 1 of the bar lines up.

### B. Audio (no extra apps)
Choose **Sync → Audio** and allow microphone access. It listens for the kick drum.
- Easiest: the laptop mic picking up the speakers.
- Cleaner: route Serato's output back in. On Mac use [BlackHole](https://github.com/ExistentialAudio/BlackHole) (free) or your controller's record/booth input. On Windows use "Stereo Mix" or VB-Cable. Then pick that device under **Input**.
- Adjust **Sensitivity** until the dots bounce with the kick.

### C. Tap
Tap **Space** on the beat 4 or more times. Press **Enter** on the "1".

## Getting it on the TV

- **AirPlay:** open Control Center, then Screen Mirroring, then pick your Apple TV. Choosing "Use as separate display" and moving the browser window onto the TV works best. Press **F** for fullscreen and **H** to hide the panel.
- **HDMI:** plug in and fullscreen the page on that screen. HDMI has much less delay than AirPlay.

**AirPlay adds delay** (usually 100–300 ms), so the picture lands a bit late. Drag the **Latency** slider up until the cuts and flashes hit exactly on the kick as you see them on the TV. Around 150–250 ms is typical for AirPlay and 0–40 ms for HDMI.

## Controls

| Key | Action |
|---|---|
| `Space` | Tap tempo |
| `Enter` | Set "now" as beat 1 of the bar |
| `N` | Cut to the next clip now |
| `S` (hold) | Strobe |
| `B` | Blackout on/off |
| `I` | Invert colors |
| `T` | Stutter on/off (jumps back to the cue point every half beat) |
| `1`–`5` | Cut every 1 / 2 / 4 / 8 / 16 beats |
| `F` | Fullscreen |
| `H` | Hide/show panel (it also hides after 3 s without moving the mouse) |

In the panel:
- **Clips:** turn clip groups on or off (DJ, AI, ORBIT_Day, MC_Day, Manager_Day).
- **Framing:** "Fit + blur" shows vertical reels whole with a blurred fill on the sides. "Fill / crop" zooms in to fill the screen.
- **Logo:** type text or use an image.

Your settings are remembered in the browser.
