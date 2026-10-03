# Nostalgia TV image

The commercial artifact is a flashable Raspberry Pi OS image. `scripts/setup_kiosk.sh` is a developer installer for a Pi you already administer. It is not this image.

One command builds the image:

```bash
sudo ./image/build-image.sh
```

The image is large, so it is not committed. The command writes it under `image/deploy/`. pi-gen is cloned at commit `4d8ee447dd3d37e8b0ef8752e460d9082d9d435d` (arm64, Debian Trixie) into `image/.pi-gen/`.

The build account password is generated when the command runs, written only to the gitignored file `image/pi-gen.local.config`, and then replaced with a locked password on the image. SSH is disabled. No Plex token is written into the image or this repo.

The image boots `nostalgia-tv.service`, which starts `main.py` under cage. The install path is an allowlist: the kiosk, Plex, HDMI CEC, and local files. YouTube, `yt-dlp`, `server.py`, and the web harness are not copied. The stage fails if those show up on the image.

Buyers follow `docs/FLASH.md`.
