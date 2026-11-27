/**
 * Central configuration for external documentation links.
 * Update the URLs below to change where "Quick Start" and "Startup" point
 * across the desktop header, mobile menu, and footer Help section.
 */

export const QUICK_START_URL = "https://github.com/Vyom1409/crowdwise#quick-start";
export const STARTUP_URL = "https://github.com/Vyom1409/crowdwise#startup";

export const EXTERNAL_LINKS = [
  {
    id: "quick-start",
    label: "Quick Start",
    url: QUICK_START_URL,
    ariaLabel: "Quick Start (opens in a new tab)",
  },
  {
    id: "startup",
    label: "Startup",
    url: STARTUP_URL,
    ariaLabel: "Startup (opens in a new tab)",
  },
];

/**
 * Opens an external URL outside the app.
 * Routes through Electron or native WebView shell APIs if present,
 * and uses window.open(..., "_blank", "noopener,noreferrer") by default
 * when invoked programmatically (or lets native <a target="_blank"> handle clicks in browsers).
 *
 * @param {string} url - Destination URL to open in the user's external browser.
 * @param {Event|null} [event=null] - Optional DOM click event from an anchor tag.
 * @returns {boolean} True if handled by a shell bridge or window.open, false to let native <a> proceed.
 */
export function openExternal(url, event = null) {
  if (!url) return false;

  if (typeof window !== "undefined") {
    // 1. Electron preload bridge (contextBridge)
    if (window.electronAPI && typeof window.electronAPI.openExternal === "function") {
      if (event) event.preventDefault();
      window.electronAPI.openExternal(url);
      return true;
    }

    if (window.electron && typeof window.electron.openExternal === "function") {
      if (event) event.preventDefault();
      window.electron.openExternal(url);
      return true;
    }

    // 2. Direct Electron renderer require fallback
    if (typeof window.require === "function") {
      try {
        const electron = window.require("electron");
        if (electron && electron.shell && typeof electron.shell.openExternal === "function") {
          if (event) event.preventDefault();
          electron.shell.openExternal(url);
          return true;
        }
      } catch (_) {
        // Not running in nodeIntegration Electron environment
      }
    }

    // 3. Mobile WebView bridges (Android / iOS WKWebView)
    if (window.Android && typeof window.Android.openExternal === "function") {
      if (event) event.preventDefault();
      window.Android.openExternal(url);
      return true;
    }

    if (window.webkit?.messageHandlers?.openExternal?.postMessage) {
      if (event) event.preventDefault();
      window.webkit.messageHandlers.openExternal.postMessage(url);
      return true;
    }

    // 4. Default programmatic fallback outside native <a> clicks
    if (!event) {
      window.open(url, "_blank", "noopener,noreferrer");
      return true;
    }
  }

  return false;
}
