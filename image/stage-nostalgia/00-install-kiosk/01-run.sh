#!/bin/bash -e

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

install -d "${ROOTFS_DIR}/home/pi/nostalgia-tv"
python3 "${REPO_ROOT}/image/install_payload.py" \
	--repo "${REPO_ROOT}" \
	--dest "${ROOTFS_DIR}/home/pi/nostalgia-tv"

install -d "${ROOTFS_DIR}/etc/systemd/system"
install -m 644 "${REPO_ROOT}/image/rootfs/etc/systemd/system/nostalgia-tv.service" \
	"${ROOTFS_DIR}/etc/systemd/system/nostalgia-tv.service"
install -m 644 "${REPO_ROOT}/image/rootfs/etc/systemd/system/nostalgia-mount-library.service" \
	"${ROOTFS_DIR}/etc/systemd/system/nostalgia-mount-library.service"

install -d "${ROOTFS_DIR}/etc/udev/rules.d"
install -m 644 "${REPO_ROOT}/image/rootfs/etc/udev/rules.d/99-nostalgia-library.rules" \
	"${ROOTFS_DIR}/etc/udev/rules.d/99-nostalgia-library.rules"

install -d "${ROOTFS_DIR}/etc/sudoers.d"
install -m 440 "${REPO_ROOT}/image/rootfs/etc/sudoers.d/nostalgia-kiosk" \
	"${ROOTFS_DIR}/etc/sudoers.d/nostalgia-kiosk"

install -d "${ROOTFS_DIR}/usr/local/sbin"
install -m 755 "${REPO_ROOT}/image/rootfs/usr/local/sbin/nostalgia-mount-library" \
	"${ROOTFS_DIR}/usr/local/sbin/nostalgia-mount-library"
install -m 755 "${REPO_ROOT}/image/rootfs/usr/local/sbin/nostalgia-set-timezone" \
	"${ROOTFS_DIR}/usr/local/sbin/nostalgia-set-timezone"

install -d -m 755 "${ROOTFS_DIR}/media/library"
