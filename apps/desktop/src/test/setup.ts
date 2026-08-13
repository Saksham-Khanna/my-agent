import "@testing-library/jest-dom/vitest";

// jsdom does not implement matchMedia; framer-motion's useReducedMotion
// reads it during render.
if (!window.matchMedia) {
  window.matchMedia = (query: string): MediaQueryList =>
    ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }) as MediaQueryList;
}

// jsdom provides requestAnimationFrame via a legacy alias; ensure it exists.
if (!window.requestAnimationFrame) {
  window.requestAnimationFrame = (cb: FrameRequestCallback) =>
    window.setTimeout(() => cb(performance.now()), 16);
}
