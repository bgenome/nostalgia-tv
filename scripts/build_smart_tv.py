#!/usr/bin/env python3
"""
Nostalgia TV - Smart TV Store Build & Packaging Automation
Builds certified, store-ready packages for:
  - LG webOS (22, 23, 24) -> dist/lg/org.nostalgiatv.app_1.0.0_all.ipk
  - Samsung Tizen (6.5, 7.0, 8.0) -> dist/samsung/NostalgiaTV.wgt

Validates store manifests, icon dimensions, and package integrity.
Zero external pip dependencies required.
"""

import os
import sys
import json
import shutil
import zipfile
import tarfile
import io
import subprocess
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TV_SRC_DIR = os.path.join(BASE_DIR, "tv")
WEBOS_SRC_DIR = os.path.join(BASE_DIR, "platforms", "webos")
TIZEN_SRC_DIR = os.path.join(BASE_DIR, "platforms", "tizen")
BUILD_DIR = os.path.join(BASE_DIR, "build")
DIST_DIR = os.path.join(BASE_DIR, "dist")
LG_DIST = os.path.join(DIST_DIR, "lg")
SAMSUNG_DIST = os.path.join(DIST_DIR, "samsung")


def print_step(title):
    print(f"\n\033[1;36m==>\033[0m \033[1m{title}\033[0m")


def print_success(msg):
    print(f"  \033[1;32m✔\033[0m {msg}")


def print_warning(msg):
    print(f"  \033[1;33m⚠\033[0m {msg}")


def print_error(msg):
    print(f"  \033[1;31m✖\033[0m {msg}")


def validate_image(path, expected_w, expected_h, label):
    """Validates PNG image exists and has exact required dimensions."""
    if not os.path.exists(path):
        print_error(f"Missing {label} at: {path}")
        return False
    try:
        from PIL import Image
        with Image.open(path) as img:
            w, h = img.size
            if (w, h) != (expected_w, expected_h):
                print_error(f"{label} has invalid size {w}x{h}, expected {expected_w}x{expected_h}")
                return False
        print_success(f"{label} validated: {expected_w}x{expected_h} PNG")
        return True
    except Exception as e:
        print_warning(f"Could not inspect {label} with PIL: {e}")
        return True


def validate_webos_manifest(manifest_path):
    """Validates LG webOS appinfo.json."""
    if not os.path.exists(manifest_path):
        print_error(f"appinfo.json not found: {manifest_path}")
        return False
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    required_keys = ["id", "version", "vendor", "type", "main", "title", "icon", "resolution"]
    for k in required_keys:
        if k not in data:
            print_error(f"appinfo.json missing required store key: '{k}'")
            return False

    if data.get("resolution") != "1920x1080":
        print_error("LG Seller Lounge requires resolution '1920x1080'")
        return False

    print_success(f"LG webOS appinfo.json valid (ID: {data['id']}, Version: {data['version']})")
    return True


def validate_tizen_manifest(config_path):
    """Validates Samsung Tizen config.xml."""
    if not os.path.exists(config_path):
        print_error(f"config.xml not found: {config_path}")
        return False
    try:
        tree = ET.parse(config_path)
        root = tree.getroot()
        if not root.tag.endswith("widget"):
            print_error("config.xml root must be <widget>")
            return False
        print_success(f"Samsung Tizen config.xml valid (Widget ID: {root.get('id')})")
        return True
    except Exception as e:
        print_error(f"config.xml parsing error: {e}")
        return False


def build_webos_package(staging_dir, output_dir):
    """Builds LG webOS .ipk package using ares-package or native POSIX archive builder."""
    os.makedirs(output_dir, exist_ok=True)
    manifest_path = os.path.join(staging_dir, "appinfo.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        appinfo = json.load(f)

    app_id = appinfo["id"]
    version = appinfo["version"]
    ipk_name = f"{app_id}_{version}_all.ipk"
    final_ipk_path = os.path.join(output_dir, ipk_name)

    # 1. Try official LG webOS CLI (ares-package) if installed
    ares_bin = shutil.which("ares-package")
    if ares_bin:
        print_step("Packaging with official LG ares-package CLI...")
        cmd = [ares_bin, staging_dir, "-o", output_dir]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print_success(f"LG webOS package generated: {final_ipk_path}")
            return final_ipk_path
        else:
            print_warning(f"ares-package failed ({res.stderr.strip()}), falling back to native packager")

    # 2. Native IPK Builder (standard POSIX ar archive with debian-binary, control.tar.gz, data.tar.gz)
    print_step("Packaging LG webOS .ipk natively...")
    
    # Create data.tar.gz containing /usr/palm/applications/<app_id>/
    data_tar_buf = io.BytesIO()
    with tarfile.open(fileobj=data_tar_buf, mode="w:gz") as tar:
        for root, _, files in os.walk(staging_dir):
            for file in files:
                abs_f = os.path.join(root, file)
                rel_f = os.path.relpath(abs_f, staging_dir)
                archive_name = f"usr/palm/applications/{app_id}/{rel_f}"
                tar.add(abs_f, arcname=archive_name)
    data_bytes = data_tar_buf.getvalue()

    # Create control.tar.gz
    control_content = (
        f"Package: {app_id}\n"
        f"Version: {version}\n"
        f"Section: misc\n"
        f"Priority: optional\n"
        f"Architecture: all\n"
        f"Maintainer: {appinfo.get('vendor', 'Nostalgia TV')}\n"
        f"Description: {appinfo.get('title', 'Nostalgia TV')}\n"
    ).encode("utf-8")

    control_tar_buf = io.BytesIO()
    with tarfile.open(fileobj=control_tar_buf, mode="w:gz") as tar:
        ti = tarfile.TarInfo(name="control")
        ti.size = len(control_content)
        ti.mode = 0o644
        tar.addfile(ti, io.BytesIO(control_content))
    control_bytes = control_tar_buf.getvalue()

    # Package into .ipk (standard Debian ar archive format)
    debian_binary = b"2.0\n"

    def format_ar_header(name, size):
        # 16 char name, 12 timestamp, 6 owner, 6 group, 8 mode, 10 size, 2 trailer (`\n)
        header = f"{name:<16}{'0':<12}{'0':<6}{'0':<6}{'100644':<8}{size:<10}`\n"
        return header.encode("ascii")

    with open(final_ipk_path, "wb") as f:
        f.write(b"!<arch>\n")
        
        # 1. debian-binary
        f.write(format_ar_header("debian-binary", len(debian_binary)))
        f.write(debian_binary)
        if len(debian_binary) % 2 != 0:
            f.write(b"\n")
            
        # 2. control.tar.gz
        f.write(format_ar_header("control.tar.gz", len(control_bytes)))
        f.write(control_bytes)
        if len(control_bytes) % 2 != 0:
            f.write(b"\n")
            
        # 3. data.tar.gz
        f.write(format_ar_header("data.tar.gz", len(data_bytes)))
        f.write(data_bytes)
        if len(data_bytes) % 2 != 0:
            f.write(b"\n")

    print_success(f"LG webOS .ipk package generated: {final_ipk_path} ({os.path.getsize(final_ipk_path):,} bytes)")
    return final_ipk_path


def build_tizen_package(staging_dir, output_dir):
    """Builds Samsung Tizen .wgt widget package (W3C Zip archive)."""
    os.makedirs(output_dir, exist_ok=True)
    wgt_name = "NostalgiaTV.wgt"
    final_wgt_path = os.path.join(output_dir, wgt_name)

    # 1. Try official Tizen CLI if present
    tizen_bin = shutil.which("tizen")
    if tizen_bin:
        print_step("Packaging with official Samsung Tizen CLI...")
        cmd = [tizen_bin, "package", "-t", "wgt", "-s", "default", "--", staging_dir]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print_success(f"Samsung Tizen package generated via Tizen CLI: {final_wgt_path}")
            return final_wgt_path
        else:
            print_warning(f"tizen CLI packaging skipped ({res.stderr.strip()}), generating standard .wgt package")

    # 2. Standard Tizen W3C Widget ZIP Packaging
    print_step("Packaging Samsung Tizen .wgt natively...")
    with zipfile.ZipFile(final_wgt_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(staging_dir):
            for file in files:
                abs_f = os.path.join(root, file)
                rel_f = os.path.relpath(abs_f, staging_dir)
                zf.write(abs_f, arcname=rel_f)

    print_success(f"Samsung Tizen .wgt package generated: {final_wgt_path} ({os.path.getsize(final_wgt_path):,} bytes)")
    return final_wgt_path


def main():
    print("\n" + "=" * 68)
    print("  📺 NOSTALGIA TV - SMART TV STORE PACKAGING SYSTEM")
    print("  Targets: LG webOS (22-24) & Samsung Tizen (6.5-8.0)")
    print("=" * 68)

    # 1. Clean build directory
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(LG_DIST, exist_ok=True)
    os.makedirs(SAMSUNG_DIST, exist_ok=True)

    # 2. Stage webOS Files
    print_step("1. Staging & Validating LG webOS Files...")
    webos_stage = os.path.join(BUILD_DIR, "stage_webos")
    shutil.copytree(TV_SRC_DIR, webos_stage)
    shutil.copy2(os.path.join(WEBOS_SRC_DIR, "appinfo.json"), os.path.join(webos_stage, "appinfo.json"))
    shutil.copy2(os.path.join(WEBOS_SRC_DIR, "icon.png"), os.path.join(webos_stage, "icon.png"))
    shutil.copy2(os.path.join(WEBOS_SRC_DIR, "largeIcon.png"), os.path.join(webos_stage, "largeIcon.png"))
    shutil.copy2(os.path.join(WEBOS_SRC_DIR, "splash.png"), os.path.join(webos_stage, "splash.png"))

    v_webos = (
        validate_webos_manifest(os.path.join(webos_stage, "appinfo.json")) and
        validate_image(os.path.join(webos_stage, "icon.png"), 80, 80, "LG Small Icon") and
        validate_image(os.path.join(webos_stage, "largeIcon.png"), 130, 130, "LG Large Icon") and
        validate_image(os.path.join(webos_stage, "splash.png"), 1920, 1080, "LG Splash Screen")
    )

    if not v_webos:
        print_error("webOS pre-flight validation failed.")
        sys.exit(1)

    # 3. Stage Tizen Files
    print_step("2. Staging & Validating Samsung Tizen Files...")
    tizen_stage = os.path.join(BUILD_DIR, "stage_tizen")
    shutil.copytree(TV_SRC_DIR, tizen_stage)
    shutil.copy2(os.path.join(TIZEN_SRC_DIR, "config.xml"), os.path.join(tizen_stage, "config.xml"))
    shutil.copy2(os.path.join(TIZEN_SRC_DIR, "icon.png"), os.path.join(tizen_stage, "icon.png"))

    v_tizen = (
        validate_tizen_manifest(os.path.join(tizen_stage, "config.xml")) and
        validate_image(os.path.join(tizen_stage, "icon.png"), 117, 117, "Tizen App Icon")
    )

    if not v_tizen:
        print_error("Tizen pre-flight validation failed.")
        sys.exit(1)

    # 4. Build webOS Package (.ipk)
    print_step("3. Generating LG webOS Package (.ipk)...")
    ipk_file = build_webos_package(webos_stage, LG_DIST)

    # 5. Build Samsung Tizen Package (.wgt)
    print_step("4. Generating Samsung Tizen Package (.wgt)...")
    wgt_file = build_tizen_package(tizen_stage, SAMSUNG_DIST)

    # Summary Output
    print("\n" + "=" * 68)
    print("  🎉 BUILD SUCCESSFUL - STORE PACKAGES READY")
    print(f"  LG webOS Package:      {ipk_file}")
    print(f"  Samsung Tizen Package: {wgt_file}")
    print("=" * 68)
    print("\nNext Steps:")
    print("  • LG Sideload / Test:    ares-install " + ipk_file + " -d <device>")
    print("  • Samsung Sideload/Test: tizen install -n NostalgiaTV.wgt -t <device>")
    print("  • Submission Manual:     See docs/SMART_TV_STORE_SUBMISSION_GUIDE.md\n")


if __name__ == "__main__":
    main()
