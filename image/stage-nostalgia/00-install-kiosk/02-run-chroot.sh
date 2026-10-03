#!/bin/bash -e

APP=/home/pi/nostalgia-tv

if grep -R -n -E "YouTubeClient|yt-dlp|yt_dlp|src/youtube|src\\.youtube" "${APP}"; then
	echo "YouTube code is on the image install path" >&2
	exit 1
fi

python3 -c 'import json; cfg=json.load(open("/home/pi/nostalgia-tv/data/plex_config.json", encoding="utf-8")); assert not cfg.get("token"), "Plex token must stay empty in the image"; assert cfg.get("use_demo_mode") is False, "Demo mode must be off in the image"'

python3 -m venv --system-site-packages --without-pip "${APP}/venv"
chown -R pi:pi "${APP}"
chown pi:pi /media/library

for GRP in video render input seat; do
	getent group "${GRP}" >/dev/null || groupadd --system "${GRP}"
done
usermod -aG video,render,input,seat pi
usermod -p '!' pi

install -d /etc/systemd/system/multi-user.target.wants
ln -sfn /etc/systemd/system/nostalgia-tv.service \
	/etc/systemd/system/multi-user.target.wants/nostalgia-tv.service
ln -sfn /etc/systemd/system/nostalgia-mount-library.service \
	/etc/systemd/system/multi-user.target.wants/nostalgia-mount-library.service

if [ -f /usr/lib/systemd/system/seatd.service ]; then
	ln -sfn /usr/lib/systemd/system/seatd.service \
		/etc/systemd/system/multi-user.target.wants/seatd.service
elif [ -f /lib/systemd/system/seatd.service ]; then
	ln -sfn /lib/systemd/system/seatd.service \
		/etc/systemd/system/multi-user.target.wants/seatd.service
else
	echo "seatd unit is missing" >&2
	exit 1
fi

ln -sfn /dev/null /etc/systemd/system/ssh.service
ln -sfn /dev/null /etc/systemd/system/ssh.socket
ln -sfn /dev/null /etc/systemd/system/getty@tty1.service

test -x "${APP}/venv/bin/python"
test -f "${APP}/main.py"
test ! -e "${APP}/src/youtube"
test ! -e "${APP}/server.py"
test ! -e /usr/bin/yt-dlp
test ! -e /usr/local/bin/yt-dlp
