// Room list: collapsible overlay on mobile, drag-to-resize on desktop.
function initSidebar() {
  const sidebar = document.getElementById("rooms-sidebar");
  if (!sidebar) return;
  const toggle = document.getElementById("sidebar-toggle");
  const backdrop = document.getElementById("sidebar-backdrop");
  const resizer = document.getElementById("sidebar-resizer");
  const mobile = window.matchMedia("(max-width: 767.98px)");

  // ----- Collapse / expand (mobile overlay) -----
  function setOpen(open) {
    sidebar.classList.toggle("collapsed", !open);
    if (backdrop) backdrop.classList.toggle("show", open);
  }
  setOpen(!mobile.matches);

  toggle?.addEventListener("click", () =>
    setOpen(sidebar.classList.contains("collapsed"))
  );
  backdrop?.addEventListener("click", () => setOpen(false));
  mobile.addEventListener("change", (e) => setOpen(!e.matches));

  // ----- Resize (desktop) -----
  const KEY = "sidebarWidth";
  const MIN = 160, MAX = 480;

  function setWidth(px) {
    const w = Math.min(MAX, Math.max(MIN, px));
    document.documentElement.style.setProperty("--sidebar-width", w + "px");
  }

  const stored = parseInt(localStorage.getItem(KEY), 10);
  if (stored) setWidth(stored);

  let startX = 0, startWidth = 0;
  function onMove(e) {
    setWidth(startWidth + (e.clientX - startX));
  }
  function onUp() {
    document.body.style.userSelect = "";
    document.body.style.cursor = "";
    window.removeEventListener("pointermove", onMove);
    window.removeEventListener("pointerup", onUp);
    localStorage.setItem(KEY, Math.round(sidebar.getBoundingClientRect().width));
  }
  resizer?.addEventListener("pointerdown", (e) => {
    if (mobile.matches) return;
    startX = e.clientX;
    startWidth = sidebar.getBoundingClientRect().width;
    document.body.style.userSelect = "none";
    document.body.style.cursor = "col-resize";
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    e.preventDefault();
  });
}

window.addEventListener("DOMContentLoaded", initSidebar);
