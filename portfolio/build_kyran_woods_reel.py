#!/usr/bin/env python3
"""Builds the Kyran Woods video portfolio reel (1080x1920, 9:16).

Structure:
  1. Event recap  - the "Raise the Bar" recap (Kyran's example), with the name title on top
  2. Live sets    - stage / outdoor / pop-up DJ footage
  3. Studio       - cinematic studio DJ sessions
  4. Podcasts & interviews - the 1080p sit-down series + CTV "Festival Season" interviews
  5. Outro card

Audio: the recap's own track for section 1, then the DJ_154 live house set (123 BPM)
for the montage. Montage cuts land on 4-beat boundaries.

Usage: python3 portfolio/build_kyran_woods_reel.py RECAP.mov [OUT.mp4]
"""
from __future__ import annotations
import subprocess, sys, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RECAP = Path(sys.argv[1])
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "portfolio/Kyran_Woods_Portfolio_Reel.mp4"

W, H, FPS = 1080, 1920, 30
BEAT = 60 / 123            # DJ_154 tempo
BAR = 4 * BEAT             # one cut every 4 beats (~1.95s)
MUSIC_FILE, MUSIC_START = REPO / "DJ_154.mp4", 0.44   # first downbeat of the set
RECAP_LEN = 24.6           # stop before the recap's "to be continued" card
OUTRO_LEN = 2 * BAR

SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# (label shown on first shot of the section, [(clip, start_seconds, length_in_bars)])
SECTIONS = [
    ("LIVE SETS", [
        ("DJ_153", 8, 1), ("DJ_154", 34, 1), ("DJ_155", 12, 1),
        ("DJ_164", 4.5, 1), ("DJ_165", 17, 1), ("DJ_170", 13, 1),
    ]),
    ("STUDIO SESSIONS", [
        ("DJ_32", 20, 1), ("DJ_31", 8, 1), ("DJ_40", 2, 1), ("DJ_41", 43, 1),
        ("DJ_63", 27, 1), ("DJ_64", 14, 1), ("DJ_24", 31.5, 1), ("DJ_131", 13, 1),
    ]),
    ("PODCASTS  &  INTERVIEWS", [
        ("ORBIT_Day12", 6, 2), ("Manager_Day20", 1, 1), ("MC_Day_01", 5.5, 1),
        ("DJ_189", 29, 1), ("DJ_192", 26, 1), ("DJ_199", 36, 1),
    ]),
]

GRADE = ("eq=contrast=1.06:saturation=1.05,"
         "vignette=angle=PI/5")


def cover():
    return (f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={W}:{H},unsharp=5:5:0.4,setsar=1,fps={FPS}")


def esc(t: str) -> str:
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def label(text: str, dur: float) -> str:
    """Small spaced caps chapter label, lower third, fades in/out."""
    a = f"if(lt(t,0.25),t/0.25,if(gt(t,{dur-0.3}),({dur}-t)/0.3,1))"
    return (f",drawbox=x=(iw-560)/2:y=ih*0.80-8:w=560:h=2:color=white@0.7:t=fill:enable='lt(t,{dur})',"
            f"drawtext=fontfile={SANS}:text='{esc(' '.join(text))}':fontsize=30:fontcolor=white:"
            f"alpha='{a}':x=(w-text_w)/2:y=h*0.80+18:shadowcolor=black@0.6:shadowx=2:shadowy=2")


def title(line1: str, line2: str, start: float, dur: float) -> str:
    a = f"if(lt(t-{start},0.6),(t-{start})/0.6,if(gt(t,{start+dur-0.6}),({start+dur}-t)/0.6,1))"
    en = f"enable='between(t,{start},{start+dur})'"
    return (f",drawtext=fontfile={SERIF}:text='{esc(line1)}':fontsize=92:fontcolor=white:alpha='{a}':"
            f"x=(w-text_w)/2:y=h*0.44:shadowcolor=black@0.7:shadowx=3:shadowy=3:{en},"
            f"drawtext=fontfile={SANS}:text='{esc(line2)}':fontsize=30:fontcolor=white@0.9:alpha='{a}':"
            f"x=(w-text_w)/2:y=h*0.44+130:shadowcolor=black@0.7:shadowx=2:shadowy=2:{en}")


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="kw_reel_"))
    segs = []

    # 1. recap with name title
    seg = tmp / "000_recap.mp4"
    vf = cover() + "," + GRADE + title("K Y R A N   W O O D S", "D I R E C T O R   ·   V I D E O G R A P H E R   ·   E D I T O R", 0.3, 3.4) \
        + f",fade=t=in:st=0:d=0.5"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(RECAP), "-t", str(RECAP_LEN), "-vf", vf, "-an",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(seg)])
    segs.append(seg)

    # 2-4. beat-cut montage
    i = 1
    for sec_label, shots in SECTIONS:
        for n, (clip, ss, bars) in enumerate(shots):
            dur = bars * BAR
            vf = cover() + "," + GRADE + (label(sec_label, min(dur, 1.9)) if n == 0 else "")
            seg = tmp / f"{i:03d}_{clip}.mp4"
            run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-i", str(REPO / f"{clip}.mp4"),
                 "-t", f"{dur:.4f}", "-vf", vf, "-an", "-r", str(FPS),
                 "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(seg)])
            segs.append(seg)
            i += 1

    # 5. outro: last stage shot, blurred so its burned-in lyrics don't fight the name card
    seg = tmp / f"{i:03d}_outro.mp4"
    vf = (cover() + "," + GRADE + ",boxblur=18:2,eq=brightness=-0.18"
          + title("K Y R A N   W O O D S", "S H O T   ·   G R A D E D   ·   E D I T E D", 0.2, OUTRO_LEN - 0.2)
          + f",fade=t=out:st={OUTRO_LEN-0.9}:d=0.9")
    run(["ffmpeg", "-v", "error", "-y", "-ss", "50", "-i", str(REPO / "DJ_154.mp4"), "-t", f"{OUTRO_LEN:.4f}",
         "-vf", vf, "-an", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", str(seg)])
    segs.append(seg)

    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{s}'\n" for s in segs))
    video = tmp / "video.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(video)])

    montage_len = sum(b for _, shots in SECTIONS for _, _, b in shots) * BAR + OUTRO_LEN
    total = RECAP_LEN + montage_len
    # recap audio -> short crossfade -> live house set, fade out on the outro
    af = (f"[1:a]atrim=0:{RECAP_LEN+0.3},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,"
          f"afade=t=in:st=0:d=0.4[a0];"
          f"[2:a]atrim={MUSIC_START}:{MUSIC_START+montage_len+0.3},asetpts=PTS-STARTPTS,"
          f"aformat=sample_rates=48000:channel_layouts=stereo,volume=1.15[a1];"
          f"[a0][a1]acrossfade=d=0.3:c1=tri:c2=tri,afade=t=out:st={total-1.6:.3f}:d=1.6,"
          f"loudnorm=I=-14:TP=-1.0:LRA=11[a]")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(RECAP), "-i", str(MUSIC_FILE),
         "-filter_complex", af, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-t", f"{total:.3f}", "-movflags", "+faststart", str(OUT)])
    print(f"wrote {OUT}  ({total:.1f}s)")


if __name__ == "__main__":
    main()
