# recorder/engine.py
import json, time, threading, os
from selenium.webdriver.common.by import By

# JAVASCRIPT LISTENER
JS_LISTENER = """
// Global event storage
window.__EVTS = window.__EVTS || [];

// Build CSS selector path
function cssPath(el){
    if (!el) return "";
    if (el.id) return "#" + el.id;

    let path = [];
    while (el && el.nodeType === 1 && el.tagName.toLowerCase() !== "html") {
        let sel = el.tagName.toLowerCase();

        if (el.className) {
            sel += "." + el.className.trim().replace(/\s+/g, ".");
        }

        let sib = el, nth = 1;
        while (sib = sib.previousElementSibling) {
            if (sib.tagName === el.tagName) nth++;
        }
        if (nth > 1) sel += ":nth-of-type(" + nth + ")";

        path.unshift(sel);
        el = el.parentElement;
    }
    return path.join(" > ");
}

// CLICK
document.addEventListener("click", e => {
    window.__EVTS.push({
        action: "click",
        selector: cssPath(e.target),
        ts: Date.now()
    });
}, true);

// TYPE
document.addEventListener("input", e => {
    window.__EVTS.push({
        action: "type",
        selector: cssPath(e.target),
        value: e.target.value || "",
        ts: Date.now()
    });
}, true);

// SCROLL (debounced)
let scrollTimeout = null;
window.addEventListener("scroll", e => {
    if (scrollTimeout) clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(() => {
        window.__EVTS.push({
            action: "scroll",
            x: window.scrollX || 0,
            y: window.scrollY || 0,
            ts: Date.now()
        });
    }, 150);
}, true);
"""

# FLUSH EVENTS FROM PAGE
JS_FLUSH = "return window.__EVTS.splice(0, window.__EVTS.length);"

# RECORDER CLASS
class Recorder:
    def __init__(self, driver):
        self.driver = driver
        self.script = []
        self.running = False

    def install_listener(self):
        """Inject JS listener into current page."""
        try:
            self.driver.execute_script(JS_LISTENER)
            return True
        except:
            return False

    # Poll events continuously
    def _poll(self):
        while self.running:
            events = []
            try:
                events = self.driver.execute_script(JS_FLUSH)
            except:
                pass

            for ev in events:
                self.script.append(ev)

            time.sleep(0.2)

    def start(self):
        self.install_listener()
        self.running = True
        threading.Thread(target=self._poll, daemon=True).start()

    def stop(self):
        self.running = False

    def get_script(self):
        return self.script

    def clear(self):
        self.script = []

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.script, f, indent=2)

    # PLAYBACK ENGINE
    def _find(self, selector):
        try:
            return self.driver.find_element(By.CSS_SELECTOR, selector)
        except:
            return None

    def play(self):
        for step in self.script:
            action = step["action"]

            # CLICK
            if action == "click":
                el = self._find(step.get("selector"))
                if el:
                    try:
                        el.click()
                    except:
                        pass

            # TYPE
            elif action == "type":
                el = self._find(step.get("selector"))
                if el:
                    try:
                        el.clear()
                        el.send_keys(step.get("value", ""))
                    except:
                        pass

            # SCROLL
            elif action == "scroll":
                x = step.get("x", 0)
                y = step.get("y", 0)
                try:
                    self.driver.execute_script(
                        "window.scrollTo(arguments[0], arguments[1])",
                        x, y
                    )
                except:
                    pass

            # WAIT
            elif action == "wait":
                time.sleep(step.get("seconds", 1))

            time.sleep(0.25)
