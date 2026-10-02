/**
 * Nostalgia TV - Smart TV Hardware & Platform Bridge Adapter
 * Supports:
 * - Samsung Tizen (6.5, 7.0, 8.0)
 * - LG webOS (22, 23, 24)
 * - Generic Smart TV Browser / Chromium 10-foot runtime
 */

(function (window, document) {
  'use strict';

  const TVAdapter = {
    platform: 'generic', // 'tizen', 'webos', or 'generic'
    serverUrl: '',
    audioCtx: null,
    testToneOsc: null,
    testToneGain: null,
    isMuted: true,
    activeModal: null,

    init() {
      this.detectPlatform();
      this.initStorage();
      this.registerTVKeys();
      this.initPowerManagement();
      this.initSpatialNavigation();
      console.log(`[NostalgiaTV] TVAdapter initialized for platform: ${this.platform}`);
    },

    detectPlatform() {
      const ua = navigator.userAgent || '';
      if (window.tizen || ua.indexOf('Tizen') > -1 || ua.indexOf('SmartTV') > -1 && ua.indexOf('Samsung') > -1) {
        this.platform = 'tizen';
      } else if (window.webOS || ua.indexOf('Web0S') > -1 || ua.indexOf('webOS') > -1 || ua.indexOf('LG NetCast') > -1) {
        this.platform = 'webos';
      } else {
        this.platform = 'generic';
      }
    },

    initStorage() {
      // If loaded from HTTP server, default to that host; otherwise load from localStorage
      const saved = localStorage.getItem('nostalgia_server_url');
      if (saved) {
        this.serverUrl = saved.replace(/\/+$/, '');
      } else if (window.location.protocol.startsWith('http')) {
        this.serverUrl = window.location.origin;
        localStorage.setItem('nostalgia_server_url', this.serverUrl);
      } else {
        this.serverUrl = 'http://192.168.1.100:8080';
      }
    },

    setServerUrl(url) {
      if (!url) return;
      let cleanUrl = url.trim().replace(/\/+$/, '');
      if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
        cleanUrl = 'http://' + cleanUrl;
      }
      this.serverUrl = cleanUrl;
      localStorage.setItem('nostalgia_server_url', this.serverUrl);
    },

    getServerUrl() {
      return this.serverUrl;
    },

    /* ================= Tizen & webOS Key Registration ================= */
    registerTVKeys() {
      // 1. Samsung Tizen Key Registration
      if (this.platform === 'tizen' && window.tizen && window.tizen.tvinputdevice) {
        const tizenKeys = [
          'ChannelUp', 'ChannelDown',
          'MediaPlayPause', 'MediaPlay', 'MediaPause',
          '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
          'Info'
        ];
        tizenKeys.forEach(key => {
          try {
            window.tizen.tvinputdevice.registerKey(key);
          } catch (e) {
            // Ignore if key registration not supported on specific firmware
          }
        });
      }

      // 2. Global Keydown Listener
      window.addEventListener('keydown', (e) => this.handleGlobalKeyDown(e));
    },

    /* ================= Power & Screensaver Management ================= */
    initPowerManagement() {
      // Inhibit screensaver while video is broadcasting
      if (this.platform === 'tizen' && window.tizen && window.tizen.power) {
        try {
          window.tizen.power.request('SCREEN', 'SCREEN_NORMAL');
        } catch (e) {
          console.warn('[NostalgiaTV] Tizen power request failed', e);
        }
      }
    },

    /* ================= Exit Application Protocol ================= */
    exitApp() {
      if (this.platform === 'tizen' && window.tizen && window.tizen.application) {
        try {
          window.tizen.application.getCurrentApplication().exit();
          return;
        } catch (e) {}
      } else if (this.platform === 'webos' && window.webOS && window.webOS.platformBack) {
        try {
          window.webOS.platformBack();
          return;
        } catch (e) {}
      }
      // Browser fallback
      window.close();
    },

    /* ================= Key Event Dispatcher ================= */
    handleGlobalKeyDown(e) {
      const keyCode = e.keyCode;
      const keyName = e.key;

      // Unlock AudioContext on any physical key interaction
      this.initAudioContext();

      // 1. Check for Smart TV Back Key
      // Tizen HW Back: 10009 | webOS Back: 461 | Standard: 27 (Escape), 8 (Backspace)
      if (keyCode === 10009 || keyCode === 461 || keyCode === 27 || keyName === 'GoBack') {
        e.preventDefault();
        this.handleBackNavigation();
        return;
      }

      // 2. Modal Navigation Trapping
      if (this.activeModal) {
        this.handleModalKey(e);
        return;
      }

      // 3. Channel Up / Down Keys (Physical Remote Keys)
      // Tizen/webOS ChannelUp: 33 (PageUp) / 'ChannelUp' | ChannelDown: 34 (PageDown) / 'ChannelDown'
      if (keyCode === 33 || keyName === 'ChannelUp' || keyName === 'ArrowUp') {
        e.preventDefault();
        if (window.channelUp) window.channelUp();
        return;
      }

      if (keyCode === 34 || keyName === 'ChannelDown' || keyName === 'ArrowDown') {
        e.preventDefault();
        if (window.channelDown) window.channelDown();
        return;
      }

      // 4. Numeric Tuning Keys (0 - 9)
      if (keyCode >= 48 && keyCode <= 57) {
        const num = keyCode - 48;
        if (window.tuneChannel && num >= 1 && num <= 9) {
          window.tuneChannel(num);
        }
        return;
      }

      // 5. Left Arrow: Open Quick HUD / Guide | Right Arrow: Open Server Settings
      if (keyName === 'ArrowLeft') {
        e.preventDefault();
        if (window.toggleGuide) window.toggleGuide();
        return;
      }

      if (keyName === 'ArrowRight') {
        e.preventDefault();
        this.openModal('settings-modal');
        return;
      }

      // 6. Enter / OK Button
      if (keyName === 'Enter' || keyCode === 13) {
        if (this.isMuted) {
          this.toggleMute();
        } else if (window.showChannelOSD) {
          window.showChannelOSD();
        }
      }
    },

    handleBackNavigation() {
      if (this.activeModal) {
        this.closeModal(this.activeModal);
      } else if (window.isGuideActive && window.isGuideActive()) {
        window.closeGuide();
      } else {
        // Show Exit Dialog (Mandatory for Tizen / webOS Store Certification)
        this.openModal('exit-modal');
      }
    },

    /* ================= 10-Foot Spatial Navigation ================= */
    initSpatialNavigation() {
      // Focus tracking inside dialogs
    },

    openModal(id) {
      const el = document.getElementById(id);
      if (!el) return;
      el.classList.add('open');
      this.activeModal = id;

      // Focus first focusable item
      const focusable = el.querySelectorAll('.nav-focusable');
      if (focusable.length > 0) {
        focusable[0].focus();
      }
    },

    closeModal(id) {
      const el = document.getElementById(id || this.activeModal);
      if (!el) return;
      el.classList.remove('open');
      this.activeModal = null;
      document.body.focus();
    },

    handleModalKey(e) {
      const modal = document.getElementById(this.activeModal);
      if (!modal) return;
      const focusables = Array.from(modal.querySelectorAll('.nav-focusable'));
      const activeIdx = focusables.indexOf(document.activeElement);

      if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
        e.preventDefault();
        const nextIdx = (activeIdx + 1) % focusables.length;
        focusables[nextIdx].focus();
      } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault();
        const prevIdx = (activeIdx - 1 + focusables.length) % focusables.length;
        focusables[prevIdx].focus();
      } else if (e.key === 'Enter') {
        // Let standard button onclick trigger
      }
    },

    /* ================= Web Audio API & Reference Test Tone ================= */
    initAudioContext() {
      if (!this.audioCtx) {
        const AudioClass = window.AudioContext || window.webkitAudioContext;
        if (AudioClass) {
          this.audioCtx = new AudioClass();
        }
      }
      if (this.audioCtx && this.audioCtx.state === 'suspended') {
        this.audioCtx.resume();
      }
    },

    toggleMute() {
      this.initAudioContext();
      this.isMuted = !this.isMuted;
      const banner = document.getElementById('unmute-banner');
      if (banner) {
        banner.style.display = this.isMuted ? 'block' : 'none';
      }
      if (window.setAudioMute) {
        window.setAudioMute(this.isMuted);
      }
      // If demo tone is playing, update its volume
      if (this.testToneGain) {
        this.testToneGain.gain.setValueAtTime(this.isMuted ? 0 : 0.08, this.audioCtx.currentTime);
      }
    },

    startTestTone() {
      this.initAudioContext();
      if (!this.audioCtx || this.testToneOsc) return;
      try {
        this.testToneOsc = this.audioCtx.createOscillator();
        this.testToneGain = this.audioCtx.createGain();
        this.testToneOsc.type = 'sine';
        this.testToneOsc.frequency.setValueAtTime(1000, this.audioCtx.currentTime); // Standard 1000 Hz broadcast tone
        this.testToneGain.gain.setValueAtTime(this.isMuted ? 0 : 0.08, this.audioCtx.currentTime);
        this.testToneOsc.connect(this.testToneGain);
        this.testToneGain.connect(this.audioCtx.destination);
        this.testToneOsc.start();
      } catch (e) {
        console.warn('[NostalgiaTV] Audio oscillator blocked', e);
      }
    },

    stopTestTone() {
      if (this.testToneOsc) {
        try {
          this.testToneOsc.stop();
          this.testToneOsc.disconnect();
        } catch (e) {}
        this.testToneOsc = null;
        this.testToneGain = null;
      }
    },

    /* ================= SMPTE Color Bar Test Generator ================= */
    renderSMPTETestPattern(canvas, customMessage) {
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;

      // Top 67%: 7 Primary & Secondary Colors
      const topHeight = Math.floor(h * 0.67);
      const barWidth = w / 7;
      const topColors = [
        '#c0c0c0', // 75% White
        '#c0c000', // Yellow
        '#00c0c0', // Cyan
        '#00c000', // Green
        '#c000c0', // Magenta
        '#c00000', // Red
        '#0000c0'  // Blue
      ];
      topColors.forEach((color, i) => {
        ctx.fillStyle = color;
        ctx.fillRect(Math.floor(i * barWidth), 0, Math.ceil(barWidth), topHeight);
      });

      // Middle 8%: Cast sub-bars
      const midHeight = Math.floor(h * 0.08);
      const midY = topHeight;
      const midColors = ['#0000c0', '#131313', '#c000c0', '#131313', '#00c0c0', '#131313', '#c0c0c0'];
      midColors.forEach((color, i) => {
        ctx.fillStyle = color;
        ctx.fillRect(Math.floor(i * barWidth), midY, Math.ceil(barWidth), midHeight);
      });

      // Bottom 25%: I, Q, and PLUGE Black Bars
      const botY = topHeight + midHeight;
      const botHeight = h - botY;
      ctx.fillStyle = '#08214d'; // -I
      ctx.fillRect(0, botY, Math.floor(w * 0.18), botHeight);
      ctx.fillStyle = '#ffffff'; // 100% White
      ctx.fillRect(Math.floor(w * 0.18), botY, Math.floor(w * 0.18), botHeight);
      ctx.fillStyle = '#3b007d'; // +Q
      ctx.fillRect(Math.floor(w * 0.36), botY, Math.floor(w * 0.18), botHeight);
      ctx.fillStyle = '#131313'; // Black level
      ctx.fillRect(Math.floor(w * 0.54), botY, Math.floor(w * 0.46), botHeight);

      // Centered 10-Foot Retro Station Identification Card
      ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
      ctx.fillRect(Math.floor(w * 0.1), Math.floor(h * 0.35), Math.floor(w * 0.8), Math.floor(h * 0.28));
      ctx.strokeStyle = '#ffff00';
      ctx.lineWidth = 4;
      ctx.strokeRect(Math.floor(w * 0.1), Math.floor(h * 0.35), Math.floor(w * 0.8), Math.floor(h * 0.28));

      ctx.fillStyle = '#33ff33';
      ctx.font = 'bold 36px monospace';
      ctx.textAlign = 'center';
      ctx.fillText('★ NOSTALGIA TV BROADCAST SYSTEM ★', w / 2, h * 0.43);

      ctx.fillStyle = '#ffffff';
      ctx.font = '22px monospace';
      ctx.fillText(customMessage || 'OFFLINE / DEMO PATTERN • PRESS [▶] OR [RIGHT] FOR SERVER SETTINGS', w / 2, h * 0.50);

      ctx.fillStyle = '#ffaa00';
      ctx.font = 'bold 20px monospace';
      ctx.fillText(`TARGET SERVER: ${this.serverUrl}`, w / 2, h * 0.57);
    }
  };

  window.TVAdapter = TVAdapter;
})(window, document);
