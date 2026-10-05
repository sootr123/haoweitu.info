/* HTU. — small, dependency-free behaviour for every page.
   Everything here is progressive: pages read fine without it. */
(() => {
  const root = document.documentElement;
  root.classList.add("js");
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = matchMedia("(hover: hover) and (pointer: fine)").matches;
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
  };

  /* ── language ─────────────────────────────────────── */
  const setLang = (value) => {
    const lang = value === "zh" ? "zh" : "en";
    root.dataset.lang = lang;
    root.lang = lang === "zh" ? "zh-Hant" : "en";
    $$("[data-set-lang]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.setLang === lang)));
    store.set("lang", lang);
    document.dispatchEvent(new Event("langchange"));
  };
  const asked = new URLSearchParams(location.search).get("lang");
  setLang(asked === "zh" || asked === "en" ? asked : store.get("lang"));
  $$("[data-set-lang]").forEach((b) => b.addEventListener("click", () => setLang(b.dataset.setLang)));

  /* ── clocks: Melbourne and Taipei ─────────────────── */
  const clocks = $$("time[data-tz]");
  if (clocks.length) {
    const tick = () => clocks.forEach((t) => {
      t.textContent = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: t.dataset.tz }).format(new Date());
    });
    tick();
    setInterval(tick, 20000);
  }

  /* ── reveal on scroll ─────────────────────────────── */
  const rv = $$(".rv");
  if (rv.length && "IntersectionObserver" in window && !reduce) {
    const io = new IntersectionObserver((es) => es.forEach((e) => {
      if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
    }), { rootMargin: "0px 0px -8% 0px" });
    rv.forEach((el) => io.observe(el));
  } else rv.forEach((el) => el.classList.add("in"));

  /* ── cursor preview for image-backed records ─────── */
  const peek = $(".peek");
  if (peek && finePointer && !reduce) {
    const img = $("img", peek);
    let x = 0, y = 0, raf = 0, active = null;
    const hide = () => { peek.classList.remove("on"); active = null; };
    const place = () => {
      raf = 0;
      const w = peek.offsetWidth, h = peek.offsetHeight;
      const right = x + 24;
      const px = Math.max(12, right + w < innerWidth - 12 ? right : x - w - 24);
      const py = Math.max(12, Math.min(y - h / 2, innerHeight - h - 12));
      peek.style.transform = `translate(${px}px, ${py}px)`;
    };
    img.addEventListener("load", () => { if (active) { place(); peek.classList.add("on"); } });
    img.addEventListener("error", hide);
    document.addEventListener("pointermove", (e) => {
      const row = e.target.closest("[data-peek]");
      if (!row || (row.tagName === "SUMMARY" && row.parentElement.open)) { hide(); return; }
      x = e.clientX; y = e.clientY;
      active = row;
      if (img.getAttribute("src") !== row.dataset.peek) {
        peek.classList.remove("on"); img.src = row.dataset.peek;
      } else if (img.complete && img.naturalWidth) peek.classList.add("on");
      if (!raf) raf = requestAnimationFrame(place);
    }, { passive: true });
    document.addEventListener("scroll", hide, { passive: true, capture: true });
    document.addEventListener("toggle", hide, { capture: true });
    document.addEventListener("pointerdown", hide);
    document.documentElement.addEventListener("pointerleave", hide);
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") hide(); });
  }

  /* A small shift of ground, with the photographs left intact. */
  const mark = $(".mark");
  if (mark) {
    const type = $(".mark-type", mark);
    const lens = $(".ground-lens", mark);
    const fit = () => {
      type.style.fontSize = "100px";
      const width = type.getBoundingClientRect().width;
      if (width) type.style.fontSize = `${100 * mark.clientWidth / width}px`;
    };
    fit();
    document.fonts?.ready.then(fit);
    addEventListener("resize", fit);
    if (finePointer && !reduce) {
      mark.addEventListener("pointermove", (e) => {
        const r = mark.getBoundingClientRect();
        const x = Math.max(0, Math.min(r.width - lens.offsetWidth, e.clientX - r.left - lens.offsetWidth / 2));
        const y = Math.max(0, Math.min(r.height - lens.offsetHeight, e.clientY - r.top - lens.offsetHeight / 2));
        lens.style.left = `${x}px`;
        lens.style.top = `${y}px`;
      });
      mark.addEventListener("pointerleave", () => { lens.style.left = ""; lens.style.top = ""; });
    }
  }

  /* The two article previews share one native scrolling window. */
  const reader = $(".press-scroll");
  if (reader) {
    const articles = $$(".press-article", reader);
    const choices = $$("[data-press-choice]");
    const syncReading = () => {
      const centre = reader.scrollTop + reader.clientHeight * .45;
      const active = [...articles].reverse().find((a) => a.offsetTop <= centre) || articles[0];
      choices.forEach((a) => a.setAttribute("aria-current", String(a.dataset.pressChoice === active.id)));
      $("[data-press-address]").href = active.dataset.url;
      $("[data-press-domain]").textContent = new URL(active.dataset.url).hostname.replace(/^www\./, "");
    };
    choices.forEach((a) => a.addEventListener("click", (e) => {
      const article = articles.find((p) => p.id === a.dataset.pressChoice);
      if (!article) return;
      e.preventDefault();
      reader.scrollTo({ top: article.offsetTop, behavior: reduce ? "instant" : "smooth" });
    }));
    reader.addEventListener("scroll", syncReading, { passive: true });
    addEventListener("resize", syncReading);
    syncReading();
  }

  /* ── work page: filters ───────────────────────────── */
  const wl = $(".w-list");
  if (wl) {
    const rows = $$(".w-row", wl);
    const shuffle = () => {
      const order = [...rows];
      for (let i = order.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [order[i], order[j]] = [order[j], order[i]];
      }
      order.forEach((r) => wl.append(r));
    };
    shuffle();
    addEventListener("pageshow", (e) => { if (e.persisted) shuffle(); });
    const buttons = $$("[data-filter]");
    const allowed = new Set(buttons.map((b) => b.dataset.filter));
    const filter = (value) => {
      const f = allowed.has(value) ? value : "all";
      wl.dataset.filtered = String(f !== "all");
      buttons.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.filter === f)));
      rows.forEach((r) => { r.hidden = !(f === "all" || r.dataset.filters.split(" ").includes(f)); });
      const url = new URL(location.href);
      if (f === "all") url.searchParams.delete("f"); else url.searchParams.set("f", f);
      history.replaceState(null, "", url);
    };
    buttons.forEach((b) => b.addEventListener("click", () => filter(b.dataset.filter)));
    const start = new URLSearchParams(location.search).get("f");
    if (start) filter(start);
  }

  /* ── films: embeds load only when asked ───────────── */
  $$(".film-play").forEach((b) => b.addEventListener("click", () => {
    if (b.dataset.video) {
      const v = document.createElement("video");
      v.src = b.dataset.video; v.controls = true; v.autoplay = true; v.playsInline = true;
      b.replaceWith(v);
      return;
    }
    const f = document.createElement("iframe");
    f.src = b.dataset.src;
    f.title = b.getAttribute("aria-label");
    f.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
    f.allowFullscreen = true;
    b.replaceWith(f);
  }));

  /* Muted previews run only near the viewport; visitors can pause them. */
  const loops = $$("video.loop");
  const motionToggle = $("[data-pause-previews]");
  let motionPaused = reduce;
  const near = new Set();
  const syncMotion = () => {
    loops.forEach((v) => {
      if (near.has(v) && !motionPaused && !document.hidden) { v.preload = "auto"; v.play().catch(() => {}); }
      else v.pause();
    });
    if (motionToggle) {
      motionToggle.setAttribute("aria-pressed", String(motionPaused));
      motionToggle.innerHTML = motionPaused ? '<span class="en">Resume motion</span><span class="zh">播放動態</span>' : '<span class="en">Pause motion</span><span class="zh">暫停動態</span>';
    }
  };
  loops.forEach((v) => v.removeAttribute("autoplay"));
  if (loops.length && "IntersectionObserver" in window) {
    const lo = new IntersectionObserver((es) => {
      es.forEach((e) => { if (e.isIntersecting) near.add(e.target); else near.delete(e.target); });
      syncMotion();
    }, { rootMargin: "120px 0px" });
    loops.forEach((v) => lo.observe(v));
  }
  motionToggle?.addEventListener("click", () => { motionPaused = !motionPaused; syncMotion(); });
  document.addEventListener("visibilitychange", syncMotion);
  syncMotion();

  /* ── pictures fade in once decoded ────────────────── */
  $$("img[loading=lazy]").forEach((im) => {
    if (im.complete && im.naturalWidth) return;
    im.classList.add("fade");
    const done = () => im.classList.add("ld");
    im.addEventListener("load", done, { once: true });
    im.addEventListener("error", done, { once: true });
  });

  /* ── about: load the talk only when asked ─────────── */
  $$(".video-btn").forEach((b) => b.addEventListener("click", () => {
    const f = document.createElement("iframe");
    f.src = `https://www.youtube-nocookie.com/embed/${b.dataset.yt}?autoplay=1`;
    f.title = b.getAttribute("aria-label");
    f.allow = "autoplay; encrypted-media; picture-in-picture";
    f.allowFullscreen = true;
    b.replaceWith(f);
  }));
})();
