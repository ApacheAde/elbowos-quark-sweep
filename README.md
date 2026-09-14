# Quark Sweep

Full-colour neon minesweeper for **ElbowOS**. Uncover safe quarks, flag unstable cores, chase a score.

Featured account: [x.com/ElbowOS](https://x.com/ElbowOS)

## Play

```bash
python3 -m pip install -r requirements.txt
python3 quark_sweep.py --play
```

Controls: arrows / WASD move cursor · Space / click reveal · F or right-click flag · R reset · Esc quit.

## Record a 9:16 reel

```bash
SDL_VIDEODRIVER=dummy python3 quark_sweep.py --record
```

Writes `/home/workdir/artifacts/QUARK_SWEEP_ElbowOS.mp4` (1080×1920, 15s, 30fps, H.264).

## Reel

Google Drive: https://drive.google.com/file/d/1sB-hl3mLno3o9QQro-lNDSVv2Bufn1hn/view?usp=drivesdk

Python 3 + pygame. Not a clone of prior ElbowOS cabinet titles.
