import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_installer():
    path = ROOT / "image" / "install_payload.py"
    spec = importlib.util.spec_from_file_location("install_payload", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestImagePayload(unittest.TestCase):
    def test_install_excludes_youtube_and_tokens(self):
        installer = _load_installer()
        dest = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, dest, ignore_errors=True)
        installer.install_app(str(ROOT), dest)

        self.assertTrue(os.path.exists(os.path.join(dest, "main.py")))
        self.assertTrue(os.path.exists(os.path.join(dest, "src", "plex", "client.py")))
        self.assertTrue(os.path.exists(os.path.join(dest, "src", "remote", "listener.py")))
        self.assertFalse(os.path.exists(os.path.join(dest, "src", "youtube")))
        self.assertFalse(os.path.exists(os.path.join(dest, "server.py")))
        self.assertFalse(os.path.exists(os.path.join(dest, "web")))

        with open(os.path.join(dest, "data", "plex_config.json"), encoding="utf-8") as handle:
            plex = json.load(handle)
        self.assertEqual(plex["token"], "")
        self.assertIs(plex["use_demo_mode"], False)

        for root, _dirs, files in os.walk(dest):
            for name in files:
                text = Path(os.path.join(root, name)).read_text(encoding="utf-8", errors="replace")
                self.assertNotIn("YouTubeClient", text)
                self.assertNotIn("yt-dlp", text)
                self.assertNotIn("yt_dlp", text)
                self.assertNotIn("src/youtube", text)

    def test_recipe_is_a_kiosk_image_without_ssh_or_youtube(self):
        config = (ROOT / "image" / "pi-gen.config").read_text(encoding="utf-8")
        self.assertIn("ENABLE_SSH='0'", config)
        self.assertNotIn("FIRST_USER_PASS", config)
        self.assertIn("trixie", config)

        script = (ROOT / "image" / "build-image.sh").read_text(encoding="utf-8")
        self.assertIn("secrets.token_hex", script)
        self.assertIn("unset PASS", script)
        self.assertIn("4d8ee447dd3d37e8b0ef8752e460d9082d9d435d", script)
        self.assertIn("sudo ./image/build-image.sh", (ROOT / "image" / "README.md").read_text(encoding="utf-8"))

        packages = (ROOT / "image" / "stage-nostalgia" / "00-install-kiosk" / "00-packages-nr").read_text(encoding="utf-8")
        self.assertIn("cage", packages)
        self.assertIn("cec-utils", packages)
        self.assertIn("python3-pyqt6", packages)
        self.assertNotIn("yt-dlp", packages)
        self.assertNotIn("youtube", packages.lower())

        service = (ROOT / "image" / "rootfs" / "etc" / "systemd" / "system" / "nostalgia-tv.service").read_text(encoding="utf-8")
        self.assertIn("User=pi", service)
        self.assertIn("/home/pi/nostalgia-tv/venv/bin/python /home/pi/nostalgia-tv/main.py", service)
        self.assertIn("/usr/bin/cage -s --", service)

        guide = (ROOT / "docs" / "FLASH.md").read_text(encoding="utf-8")
        self.assertNotIn("-", guide)
        self.assertNotIn("\u2013", guide)
        self.assertNotIn("\u2014", guide)
        self.assertNotIn("ssh", guide.lower())
        for word in ("download", "flash", "insert", "hdmi", "plex"):
            self.assertIn(word, guide.lower())

    def test_stage_scripts_parse(self):
        scripts = [
            ROOT / "image" / "build-image.sh",
            ROOT / "image" / "stage-nostalgia" / "prerun.sh",
            ROOT / "image" / "stage-nostalgia" / "00-install-kiosk" / "01-run.sh",
            ROOT / "image" / "stage-nostalgia" / "00-install-kiosk" / "02-run-chroot.sh",
            ROOT / "image" / "rootfs" / "usr" / "local" / "sbin" / "nostalgia-mount-library",
            ROOT / "image" / "rootfs" / "usr" / "local" / "sbin" / "nostalgia-set-timezone",
        ]
        for script in scripts:
            subprocess.check_call(["bash", "-n", str(script)])
        chroot_script = (ROOT / "image" / "stage-nostalgia" / "00-install-kiosk" / "02-run-chroot.sh").read_text(encoding="utf-8")
        self.assertNotIn("<<", chroot_script)


if __name__ == "__main__":
    unittest.main()
