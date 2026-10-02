# Smart TV App Store Submission & Certification Manual
### Targets: LG Content Store (webOS 22, 23, 24) & Samsung SmartTV App Store (Tizen 6.5, 7.0, 8.0)

---

## 1. Store Review Strategy: The Companion Broadcast Model

> [!CRITICAL]
> **Copyright & Content Rights (The #1 Rejection Cause)**:
> Both LG and Samsung conduct human and automated reviews. If an app listing includes trademarks (e.g. Cartoon Network, Nickelodeon, Sega, Nintendo) or unlicensed commercial media (cartoons, feature films), it is rejected under Samsung Policy **"Defect: Copyright Infringement"** or LG **"Content IP Infringement"**.

### The Solution:
Submit Nostalgia TV as a **Self-Hosted Broadcast Companion Player**:
* **App Description**: "A retro television experience and live stream viewer designed to connect to your personal Nostalgia TV home server."
* **First Boot Behavior**: Launches in a **Zero-Copyright state** showing an authentic 1990s SMPTE color bar test signal, simulated CRT static with Web Audio noise, and an onboarding prompt to connect to the user's server or demo stream.
* **Store Screenshots**: Show the SMPTE test pattern, the Prevue TV guide layout with generic labels ("Station ID", "Local Broadcast", "Public Domain Features"), and the CRT filter toggles.

---

## 2. LG Content Store Submission (webOS 22, 23, 24)

### Portal: [LG Seller Lounge](https://seller.lgappstv.com/)

### Step 1: Create an LG Developer Account
1. Go to [LG Seller Lounge](https://seller.lgappstv.com/) and register.
2. Complete developer verification (Individual or Corporate).

### Step 2: Build the Production Package
Run the automated packaging tool:
```bash
python3 scripts/build_smart_tv.py
```
This generates: `dist/lg/org.nostalgiatv.app_1.0.0_all.ipk`.

### Step 3: Local Sideload & Device Testing
Before submitting, test on a physical LG TV:
1. On your LG TV, install the **Developer Mode** app from the LG Content Store.
2. Launch Dev Mode, log in with your LG credentials, and enable:
   * **Dev Mode Status**: ON
   * **Key Server**: ON
3. Note the TV's IP address and Passphrase displayed on screen.
4. On your computer:
   ```bash
   npm install -g @webosose/ares-cli
   ares-setup-device --add mytv -i ip=<TV_IP> -p 9922 -u prisoner
   ares-novacom --device mytv --getkey
   # Enter the passphrase shown on your TV screen
   ares-install dist/lg/org.nostalgiatv.app_1.0.0_all.ipk -d mytv
   ares-launch org.nostalgiatv.app -d mytv
   ```

### Step 4: Submission in LG Seller Lounge
1. Log into LG Seller Lounge > **App Management** > **Add New App**.
2. **Basic Information**:
   * **App Name**: Nostalgia TV
   * **App ID**: `org.nostalgiatv.app`
   * **Category**: Entertainment / Video
   * **Price**: Free
3. **Upload Package**:
   * Upload `dist/lg/org.nostalgiatv.app_1.0.0_all.ipk`.
4. **Target Models**:
   * Select webOS 22 (2022), webOS 23 (2023), and webOS 24 (2024–2025).
5. **Assets**:
   * App Icon: `platforms/webos/icon.png` (80x80)
   * Large Icon: `platforms/webos/largeIcon.png` (130x130)
   * Splash Screen: `platforms/webos/splash.png` (1920x1080)
   * Screenshots: Minimum 3 screenshots at 1920x1080 (PNG/JPG).
6. **Reviewer Notes (Crucial)**:
   > *"Nostalgia TV is an open-source companion player for self-hosted broadcast servers. For testing without a local server running, the app launches directly into an authentic SMPTE color bar test pattern and demo mode. To test live streaming, connect to any HTTP video endpoint via the in-app Settings menu."*

---

## 3. Samsung SmartTV App Store Submission (Tizen 6.5, 7.0, 8.0)

### Portal: [Samsung SmartTV Seller Office](https://seller.samsungelm.com/)

### Step 1: Create a Samsung Partner / Developer Account
1. Register at [Samsung SmartTV Seller Office](https://seller.samsungelm.com/).
2. Apply for public developer or partner status.

### Step 2: Generate Samsung Certificates (Author & Distributor)
Samsung requires all store `.wgt` packages to be cryptographically signed:
1. Download and install **Tizen Studio with TV Extension**.
2. Open **Tizen Certificate Manager** (`tools/certificate-manager/`).
3. Click **+** > Select **Samsung Certificate**:
   * **Author Certificate**: Sign in with your Samsung account to create your personal author key.
   * **Distributor Certificate**: Select **Samsung Partner** or **Public**, enter your test TV DUIDs (Device Unique IDs).
4. Save profile as `default`.

### Step 3: Package & Sign `.wgt`
```bash
# Package with Tizen CLI and your signed certificate profile:
tizen package -t wgt -s default -- build/stage_tizen/
```
The output file is `NostalgiaTV.wgt`.

### Step 4: Sideload & Test on Samsung TV
1. On your Samsung TV:
   * Go to **Smart Hub** > **Apps**.
   * On the remote, press `1` `2` `3` `4` `5` to open **Developer Mode**.
   * Turn Developer Mode **ON** and enter your computer's IP address.
   * Restart the TV (hold Power button until Samsung logo reappears).
2. Connect from computer:
   ```bash
   sdb connect <TV_IP>
   tizen install -n NostalgiaTV.wgt -t <TV_DUID>
   ```

### Step 5: Submission in Samsung Seller Office
1. Navigate to **Applications** > **Create Application**.
2. **App Type**: HTML5 (Web Application).
3. **Upload**: Upload signed `NostalgiaTV.wgt`.
4. **Target Model Years**:
   * Check 2022 (Tizen 6.5), 2023 (Tizen 7.0), and 2024 / 2025 (Tizen 8.0).
5. **App Information**:
   * App Title: Nostalgia TV
   * Description: Retro CRT TV companion player.
   * Icon: 117x117 PNG (`platforms/tizen/icon.png`).
   * Screenshots: 4 screenshots (1920x1080).
6. **Pre-Test Self-Checklist (Mandatory)**:
   * Confirm physical remote Return key triggers exit dialog (`tizenhwkey` / 10009).
   * Confirm screensaver is inhibited (`tizen.power.request`).
   * Confirm app renders initial view within 3 seconds.

---

## 4. Pre-Certification Verification Matrix

| Test Case | webOS Requirement | Tizen Requirement | Implemented In |
| :--- | :--- | :--- | :--- |
| **D-Pad Navigation** | All controls navigable via 4-way arrows | All controls navigable via 4-way arrows | `tv/tv-adapter.js` (`handleModalKey`) |
| **Physical Back Key** | Must handle keyCode `461` / `GoBack` | Must handle `tizenhwkey` (`10009`) | `tv/tv-adapter.js` (`handleBackNavigation`) |
| **Exit Flow** | Exit prompt or return to Launcher | Explicit `tizen.application.exit()` | `tv/index.html` (`exit-modal`) |
| **Channel +/- Keys** | Handled via `ChannelUp` / `ChannelDown` | Registered via `registerKey()` | `tv/tv-adapter.js` (`registerTVKeys`) |
| **Screensaver** | Video playback must not trigger TV sleep | `tizen.power.request('SCREEN', 'SCREEN_NORMAL')` | `tv/tv-adapter.js` (`initPowerManagement`) |
| **Audio Autoplay** | Prompt user to interact before sound | Prompt user to interact before sound | `tv/index.html` (`unmute-banner`) |
| **Safe Zones** | 5% overscan margin (4vw/4vh) | 5% overscan margin (4vw/4vh) | `tv/tv-style.css` (`var(--safe-padding-*)`) |
| **Offline Resilience** | Must show error/demo, not crash | Must show error/demo, not crash | `tv/index.html` (`activateSMPTEDemo`) |
