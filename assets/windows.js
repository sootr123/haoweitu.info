/* Three viewport-bound reading windows. Geometry stays local to this visit. */
(() => {
  const clamp = (value, low, high) => Math.max(low, Math.min(value, Math.max(low, high)));
  const jitter = () => Math.random() * 2 - 1;

  document.querySelectorAll("[data-window-workspace]").forEach((workspace) => {
    const panels = [...workspace.querySelectorAll("[data-window]")];
    if (!panels.length) return;

    const states = new Map();
    const iframeSources = new WeakMap();
    let mode = "";
    let layer = 10;
    let active = null;
    let resizeFrame = 0;
    let lastWidth = 0;
    let lastHeight = 0;

    const dimensions = () => ({ width: workspace.clientWidth, height: workspace.clientHeight });
    const modeFor = (width) => width >= 1000 ? "desktop" : width >= 560 ? "tablet" : "phone";
    const openers = (state) => [...document.querySelectorAll("[data-window-open]")]
      .filter((button) => button.dataset.windowOpen === state.key);

    function bounded(geometry) {
      const { width, height } = dimensions();
      const pad = Math.min(8, width / 4);
      const availableWidth = Math.max(1, width - pad * 2);
      const availableHeight = Math.max(1, height - pad * 2);
      const w = clamp(geometry.width, Math.min(240, availableWidth), availableWidth);
      const h = clamp(geometry.height, Math.min(300, availableHeight), availableHeight);
      return {
        x: clamp(geometry.x, pad, width - w - pad),
        y: clamp(geometry.y, pad, height - h - pad),
        width: w,
        height: h,
      };
    }

    function paint(state, geometry) {
      state.geometry = bounded(geometry);
      const { x, y, width, height } = state.geometry;
      Object.assign(state.panel.style, {
        left: `${x}px`, top: `${y}px`, width: `${width}px`, height: `${height}px`,
      });
    }

    function labels(state) {
      const zh = document.documentElement.dataset.lang === "zh";
      state.close?.setAttribute("aria-label", zh ? `關閉${state.label}視窗` : `Close ${state.label} window`);
      state.handle?.setAttribute("aria-label", zh
        ? `${state.label}視窗；使用方向鍵移動`
        : `${state.label} window; use arrow keys to move`);
      state.resize?.setAttribute("aria-label", zh
        ? `調整${state.label}視窗尺寸；使用方向鍵`
        : `Resize ${state.label} window; use arrow keys`);
      openers(state).forEach((button) => {
        button.setAttribute("aria-controls", state.panel.id);
        button.setAttribute("aria-expanded", String(!state.panel.hidden));
      });
    }

    function front(state) {
      if (layer > 10000) {
        [...states.values()].sort((a, b) => a.layer - b.layer).forEach((item, index) => {
          item.layer = index + 1;
          item.panel.style.zIndex = String(item.layer);
        });
        layer = states.size + 1;
      }
      state.layer = ++layer;
      state.panel.style.zIndex = String(state.layer);
    }

    function close(state) {
      if (active?.state === state) finish();
      state.panel.querySelectorAll("video, audio").forEach((media) => media.pause());
      state.panel.querySelectorAll("iframe[src]").forEach((frame) => {
        const src = frame.getAttribute("src");
        if (src && src !== "about:blank") {
          iframeSources.set(frame, src);
          frame.src = "about:blank";
        }
      });
      state.panel.hidden = true;
      labels(state);
      openers(state)[0]?.focus({ preventScroll: true });
    }

    function open(state) {
      state.panel.hidden = false;
      state.panel.querySelectorAll("iframe").forEach((frame) => {
        if (iframeSources.has(frame)) {
          frame.src = iframeSources.get(frame);
          iframeSources.delete(frame);
        }
      });
      paint(state, state.geometry);
      front(state);
      labels(state);
      state.handle?.focus({ preventScroll: true });
    }

    function finish() {
      if (!active) return;
      const previous = active;
      active = null;
      workspace.classList.remove("is-manipulating");
      previous.state.panel.classList.remove("is-moving", "is-resizing");
      if (previous.handle.hasPointerCapture?.(previous.pointerId)) {
        previous.handle.releasePointerCapture(previous.pointerId);
      }
    }

    function begin(event, state, type, handle) {
      if (event.button !== 0 || !event.isPrimary || active) return;
      if (type === "move" && event.target.closest("button, a, input, select, textarea")) return;
      event.preventDefault();
      front(state);
      handle.focus({ preventScroll: true });
      active = { state, type, handle, pointerId: event.pointerId, x: event.clientX, y: event.clientY, geometry: { ...state.geometry } };
      workspace.classList.add("is-manipulating");
      state.panel.classList.add(type === "move" ? "is-moving" : "is-resizing");
      handle.setPointerCapture(event.pointerId);
    }

    function keyboard(event, state, type) {
      if (event.target !== event.currentTarget) return;
      const delta = event.shiftKey ? 32 : 10;
      const direction = {
        ArrowLeft: [-delta, 0], ArrowRight: [delta, 0],
        ArrowUp: [0, -delta], ArrowDown: [0, delta],
      }[event.key];
      if (!direction) return;
      event.preventDefault();
      front(state);
      const next = { ...state.geometry };
      if (type === "move") { next.x += direction[0]; next.y += direction[1]; }
      else {
        const { width, height } = dimensions();
        next.width = Math.min(next.width + direction[0], width - next.x - 8);
        next.height = Math.min(next.height + direction[1], height - next.y - 8);
      }
      paint(state, next);
    }

    panels.forEach((panel, index) => {
      const key = panel.dataset.window;
      panel.id ||= `reading-window-${key}`;
      const state = {
        key, panel, label: panel.dataset.windowLabel || ({ ca: "Communication Arts", swinburne: "Swinburne", tedx: "TEDx" }[key] || key),
        handle: panel.querySelector("[data-window-drag]"),
        close: panel.querySelector("[data-window-close]"),
        resize: panel.querySelector("[data-window-resize]"),
        geometry: null, layer: index + 1,
        variation: { x: jitter(), y: jitter(), width: jitter(), height: jitter() },
      };
      states.set(key, state);
      panel.style.zIndex = String(state.layer);
      panel.addEventListener("pointerdown", () => front(state));
      panel.addEventListener("focusin", () => front(state));
      state.handle?.addEventListener("pointerdown", (event) => begin(event, state, "move", state.handle));
      state.resize?.addEventListener("pointerdown", (event) => begin(event, state, "resize", state.resize));
      state.handle?.addEventListener("keydown", (event) => keyboard(event, state, "move"));
      state.resize?.addEventListener("keydown", (event) => keyboard(event, state, "resize"));
      state.close?.addEventListener("click", () => close(state));
      openers(state).forEach((button) => button.addEventListener("click", () => open(state)));
      panel.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;
        if (active?.state === state) {
          paint(state, active.geometry);
          finish();
          event.preventDefault();
        }
      });
      labels(state);
    });

    // Shuffle the initial overlap once, independently of later focus and dragging.
    const initialStack = [...states.values()];
    for (let index = initialStack.length - 1; index > 0; index--) {
      const other = Math.floor(Math.random() * (index + 1));
      [initialStack[index], initialStack[other]] = [initialStack[other], initialStack[index]];
    }
    initialStack.forEach((state, index) => {
      state.layer = index + 1;
      state.panel.style.zIndex = String(state.layer);
    });

    workspace.addEventListener("pointermove", (event) => {
      if (!active || event.pointerId !== active.pointerId) return;
      const next = { ...active.geometry };
      const dx = event.clientX - active.x;
      const dy = event.clientY - active.y;
      if (active.type === "move") { next.x += dx; next.y += dy; }
      else {
        const { width, height } = dimensions();
        next.width = Math.min(next.width + dx, width - next.x - 8);
        next.height = Math.min(next.height + dy, height - next.y - 8);
      }
      paint(active.state, next);
    });
    ["pointerup", "pointercancel", "lostpointercapture"].forEach((name) => {
      workspace.addEventListener(name, (event) => {
        if (active?.pointerId === event.pointerId) finish();
      });
    });
    addEventListener("blur", () => {
      finish();
      // Focus inside an embedded player does not bubble into the parent document.
      requestAnimationFrame(() => {
        const focused = document.activeElement;
        if (focused?.tagName !== "IFRAME") return;
        const panel = focused.closest("[data-window]");
        const state = panel && states.get(panel.dataset.window);
        if (state && !state.panel.hidden) front(state);
      });
    });

    function arrange(reset) {
      const { width, height } = dimensions();
      if (!width || !height) return;
      const nextMode = modeFor(width);
      reset ||= mode !== nextMode;
      mode = nextMode;
      lastWidth = width;
      lastHeight = height;
      if (active) finish();
      [...states.values()].forEach((state, index) => {
        if (reset) {
          let geometry;
          const variation = state.variation;
          if (mode === "desktop") {
            const w = Math.min(350, width * .25) + variation.width * 14;
            geometry = {
              x: [width * .45, width * .62, width - w - 16][index] + variation.x * 18,
              y: [40, height * .18, 20][index] + variation.y * [30, 40, 25][index],
              width: w,
              height: Math.min([560, 600, 540][index] + variation.height * 22, height - 80),
            };
          } else {
            geometry = {
              x: [16, 32, 48][index] + variation.x * 8,
              y: [20, 55, 90][index] + variation.y * 8,
              width: Math.min(350 + variation.width * 8, width - 64),
              height: Math.min([560, 600, 540][index] + variation.height * 8, height - 100),
            };
          }
          paint(state, geometry);
        } else {
          paint(state, state.geometry);
        }
        labels(state);
      });
      workspace.classList.add("windows-ready");
    }

    function scheduleArrange() {
      if (resizeFrame) return;
      resizeFrame = requestAnimationFrame(() => { resizeFrame = 0; arrange(false); });
    }
    arrange(true);
    addEventListener("resize", scheduleArrange);
    document.addEventListener("langchange", () => states.forEach(labels));
    if ("ResizeObserver" in window) {
      new ResizeObserver(() => {
        if (workspace.clientWidth !== lastWidth || workspace.clientHeight !== lastHeight) scheduleArrange();
      }).observe(workspace);
    }
  });
})();
