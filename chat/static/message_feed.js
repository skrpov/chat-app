function clamp(v, lo, hi) { return Math.max(lo, Math.min(v, hi)); }

const BLOCK_SIZE = 50;
const MAX_BLOCKS = 5;
const MAX_MESSAGES = MAX_BLOCKS * BLOCK_SIZE;
const BUFFER_BLOCKS = 1;
const EST_ROW = 64;
const NEAR_BOTTOM_PX = 150;

function renderMessageNode(data, userName) {
  const own = data.username === userName;
  const wrapper = document.createElement("div");
  wrapper.className = `d-flex mb-1 ${own ? "justify-content-end" : "justify-content-start"}`;
  wrapper.dataset.id = data.id;

  const container = document.createElement("div");
  container.style.maxWidth = "75%";
  container.style.minWidth = "12rem";
  container.className = "pt-2";
  container.innerHTML = `
    <div class="d-flex justify-content-between align-items-baseline gap-3">
      <span class="small text-muted fw-semibold">${data.username}</span>
      <span class="text-muted" style="font-size: 0.7rem">${new Date(data.sent_at).toLocaleTimeString()}</span>
    </div>
    <div class="px-2 py-1 border bg-light" style="border-radius: 0.5rem; width: 100%;">${data.message}</div>
    ${own ? `<div class="text-end text-muted" style="font-size: 0.65rem">Delivered</div>` : ""}
  `;
  wrapper.appendChild(container);
  return wrapper;
}

class MessageFeed {
  constructor(parent, userName) {
    this.parent = parent;
    this.userName = userName;
    this.requestHistory = null;
    this.messages = [];
    this.windowStart = 0;
    this.total = 0;
    this.initialized = false;
    this.loading = false;
    this.ticking = false;

    this.topSpacer = document.createElement("div");
    this.bottomSpacer = document.createElement("div");
    this.topMarker = document.createElement("div");
    this.topMarker.className = "text-center text-muted small py-3";
    this.topMarker.innerHTML =
      `<i class="fa-solid fa-comments me-1 opacity-75"></i> Start of chat history`;
    this.parent.replaceChildren(this.topMarker, this.topSpacer, this.bottomSpacer);
  }

  belowCount() {
    return Math.max(0, this.total - this.windowStart - this.messages.length);
  }

  isNearBottom() {
    const p = this.parent;
    return p.scrollHeight - p.scrollTop - p.clientHeight < NEAR_BOTTOM_PX;
  }

  scrollToBottom() {
    this.parent.scrollTop = this.parent.scrollHeight;
  }

  render() {
    this.topSpacer.style.height = `${this.windowStart * EST_ROW}px`;
    this.bottomSpacer.style.height = `${this.belowCount() * EST_ROW}px`;
    const nodes = this.messages.map(m => renderMessageNode(m, this.userName));
    const top = this.windowStart === 0 ? [this.topMarker] : [];
    this.parent.replaceChildren(...top, this.topSpacer, ...nodes, this.bottomSpacer);
  }

  desiredRange() {
    const topIdx = Math.floor(this.parent.scrollTop / EST_ROW);
    const visRows = Math.ceil(this.parent.clientHeight / EST_ROW);
    let start = (topIdx - BUFFER_BLOCKS * BLOCK_SIZE);
    let end = (topIdx + visRows + BUFFER_BLOCKS * BLOCK_SIZE);
    start = Math.floor(start / BLOCK_SIZE) * BLOCK_SIZE;
    end = Math.ceil(end / BLOCK_SIZE) * BLOCK_SIZE;
    start = clamp(start, 0, this.total);
    end = clamp(end, 0, this.total);
    if (end - start > MAX_MESSAGES) end = start + MAX_MESSAGES;
    return { start, count: end - start };
  }

  maybeLoad() {
    if (this.loading || this.total === 0) return;
    const { start, count } = this.desiredRange();
    const loadedEnd = this.windowStart + this.messages.length;
    if (start === this.windowStart && start + count === loadedEnd) return;
    this.loading = true;
    this.requestStart = start;
    this.requestHistory(start, count);
  }

  onHistory(data) {
    this.total = data.total;

    if (!this.initialized) {
      this.initialized = true;
      this.windowStart = data.offset;
      this.messages = data.messages;
      this.render();
      this.scrollToBottom();
      return;
    }

    this.loading = false;
    if (data.offset !== this.requestStart) {
      this.maybeLoad();
      return;
    }
    this.windowStart = data.offset;
    this.messages = data.messages;
    this.render();
    this.maybeLoad();
  }

  addNewMessage(data) {
    const showingNewest = this.windowStart + this.messages.length >= this.total;
    const pinned = showingNewest && this.isNearBottom();
    this.total = data.total;

    if (showingNewest) {
      this.messages.push(data);
      while (this.messages.length > MAX_MESSAGES) {
        this.messages.shift();
        this.windowStart += 1;
      }
      this.render();
      if (pinned) this.scrollToBottom();
    } else {
      this.render();
    }
  }

  onScroll() {
    if (this.ticking) return;
    this.ticking = true;
    requestAnimationFrame(() => {
      this.ticking = false;
      this.maybeLoad();
    });
  }
}
