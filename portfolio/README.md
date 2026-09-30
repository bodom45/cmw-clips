# Kyran Woods — Video Portfolio Reel

`Kyran_Woods_Portfolio_Reel.mp4` is a 1080x1920 (9:16) reel that runs 69.5s at 30fps, with AAC audio normalized to about -14 LUFS.

| Section | Footage |
|---|---|
| Title + Event Recaps | "Raise the Bar" recap (`source/raise_the_bar_recap.mov`) |
| Live Sets | DJ_153, DJ_154, DJ_155 (Festival Season stage), DJ_164, DJ_165 (outdoor), DJ_170 (trunk pop-up) |
| Studio Sessions | DJ_32, DJ_31, DJ_40, DJ_41, DJ_63, DJ_64, DJ_24, DJ_131 |
| Podcasts & Interviews | ORBIT_Day12, Manager_Day20, MC_Day_01, DJ_189, DJ_192, DJ_199 (CTV / Festival Season) |
| Outro | Name card over DJ_154 |

Audio: the recap's own track, then the DJ_154 live house set (123 BPM). Montage cuts land every 4 beats.

Rebuild (needs ffmpeg):

    python3 portfolio/build_kyran_woods_reel.py portfolio/source/raise_the_bar_recap.mov
