#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PI_GEN_URL="https://github.com/RPi-Distro/pi-gen.git"
PI_GEN_COMMIT="4d8ee447dd3d37e8b0ef8752e460d9082d9d435d"
PI_GEN_DIR="${REPO_ROOT}/image/.pi-gen"
LOCAL_CONFIG="${REPO_ROOT}/image/pi-gen.local.config"
DEPLOY_DIR="${REPO_ROOT}/image/deploy"

if [ "$(id -u)" -ne 0 ]; then
	echo "Run as root: sudo ./image/build-image.sh" >&2
	exit 1
fi

bash -n "${REPO_ROOT}/image/stage-nostalgia/prerun.sh"
bash -n "${REPO_ROOT}/image/stage-nostalgia/00-install-kiosk/01-run.sh"
bash -n "${REPO_ROOT}/image/stage-nostalgia/00-install-kiosk/02-run-chroot.sh"
bash -n "${REPO_ROOT}/image/rootfs/usr/local/sbin/nostalgia-mount-library"
bash -n "${REPO_ROOT}/image/rootfs/usr/local/sbin/nostalgia-set-timezone"

python3 "${REPO_ROOT}/image/install_payload.py" \
	--repo "${REPO_ROOT}" \
	--dest /tmp/nostalgia-payload-check
rm -rf /tmp/nostalgia-payload-check

if [ ! -d "${PI_GEN_DIR}/.git" ]; then
	rm -rf "${PI_GEN_DIR}"
	mkdir -p "${PI_GEN_DIR}"
	git -C "${PI_GEN_DIR}" init
	git -C "${PI_GEN_DIR}" remote add origin "${PI_GEN_URL}"
fi
git -C "${PI_GEN_DIR}" fetch --depth 1 origin "${PI_GEN_COMMIT}"
git -C "${PI_GEN_DIR}" checkout --detach FETCH_HEAD
touch "${PI_GEN_DIR}/stage2/SKIP_IMAGES"

chmod +x "${REPO_ROOT}/image/stage-nostalgia/prerun.sh"
chmod +x "${REPO_ROOT}/image/stage-nostalgia/00-install-kiosk/01-run.sh"

umask 077
cp "${REPO_ROOT}/image/pi-gen.config" "${LOCAL_CONFIG}"
PASS="$(python3 -c 'import secrets; print(secrets.token_hex(16))')"
{
	printf "FIRST_USER_PASS='%s'\n" "${PASS}"
	printf "STAGE_LIST=\"stage0 stage1 stage2 %s\"\n" "${REPO_ROOT}/image/stage-nostalgia"
	printf "DEPLOY_DIR='%s'\n" "${DEPLOY_DIR}"
} >> "${LOCAL_CONFIG}"
unset PASS

mkdir -p "${DEPLOY_DIR}"
cd "${PI_GEN_DIR}"
./build.sh -c "${LOCAL_CONFIG}"

echo "Image files:"
find "${DEPLOY_DIR}" -type f \( -name '*.img*' -o -name '*.xz' -o -name '*.zip' \) | sort
