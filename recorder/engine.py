# recorder/engine.py
import json, time, threading
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException

# JAVASCRIPT LISTENER (NOW TRACKS MOUSE DRAG + NAVIGATION EVENTS)

JS_LISTENER = """
window.__EVTS = window.__EVTS || [];
window.__DRAG = {active:false, startX:0, startY:0, startSel:''};

// CSS Selector builder
function cssPath(el){
    if (!el) return "";
    if (el.id) return "#" + el.id;
    let p = [];
    while (el && el.nodeType === 1 && el.tagName.toLowerCase() !== "html") {
        let s = el.tagName.toLowerCase();
        if (el.className) s += "." + el.className.trim().replace(/\s+/g, ".");
        let sib = el, nth = 1;
        while (sib = sib.previousElementSibling)
            if (sib.tagName === el.tagName) nth++;
        if (nth > 1) s += ":nth-of-type(" + nth + ")";
        p.unshift(s);
        el = el.parentElement;
    }
    return p.join(" > ");
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

// SCROLL
let st = null;
window.addEventListener("scroll", () => {
    if (st) clearTimeout(st);
    st = setTimeout(() => {
        window.__EVTS.push({
            action: "scroll",
            x: window.scrollX || 0,
            y: window.scrollY || 0,
            ts: Date.now()
        });
    }, 120);
}, true);

// DRAG START (mousedown)
document.addEventListener("mousedown", e => {
    window.__DRAG.active = true;
    window.__DRAG.startX = e.clientX;
    window.__DRAG.startY = e.clientY;
    window.__DRAG.startSel = cssPath(e.target);
}, true);

// DRAG END (mouseup)
document.addEventListener("mouseup", e => {
    if (!window.__DRAG.active) return;
    window.__DRAG.active = false;

    window.__EVTS.push({
        action: "drag",
        from: {
            selector: window.__DRAG.startSel,
            x: window.__DRAG.startX,
            y: window.__DRAG.startY
        },
        to: {
            selector: cssPath(e.target),
            x: e.clientX,
            y: e.clientY
        },
        ts: Date.now()
    });
}, true);

// NAVIGATION detection
window.addEventListener("hashchange", () => {
    window.__EVTS.push({ action: "navigate", url: location.href, ts: Date.now() });
});

window.addEventListener("popstate", () => {
    window.__EVTS.push({ action: "navigate", url: location.href, ts: Date.now() });
});

document.addEventListener("DOMContentLoaded", () => {
    window.__EVTS.push({ action: "navigate", url: location.href, ts: Date.now() });
});
"""

# Flush
JS_FLUSH = "return window.__EVTS.splice(0, window.__EVTS.length);"

# RECORDER CLASS

class Recorder:
    def __init__(self, driver):
        self.driver = driver
        self.script = []
        self.running = False

    # Inject listener into main page and all iframes
    def install_listener(self):
        self._inject()
        frames = self.driver.find_elements(By.TAG_NAME, "iframe")
        for i in range(len(frames)):
            try:
                self.driver.switch_to.frame(i)
                self._inject()
            except:
                pass
            finally:
                self.driver.switch_to.default_content()

    def _inject(self):
        try:
            self.driver.execute_script(JS_LISTENER)
        except:
            pass

    # Poll loop
    def _poll(self):
        while self.running:
            try:
                events = self.driver.execute_script(JS_FLUSH)
            except WebDriverException:
                events = []

            for ev in events:
                self.script.append(ev)

            time.sleep(0.25)

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
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.script, f, indent=2)

  # PLAYBACK ENGINE
    def _find(self, sel):
        try:
            return self.driver.find_element(By.CSS_SELECTOR, sel)
        except:
            return None

    def play(self):
        for step in self.script:
            act = step["action"]

            # CLICK
            if act == "click":
                el = self._find(step["selector"])
                if el:
                    try:
                        el.click()
                    except:
                        pass

            # TYPE
            elif act == "type":
                el = self._find(step["selector"])
                if el:
                    try:
                        el.clear()
                        el.send_keys(step["value"])
                    except:
                        pass

            # SCROLL
            elif act == "scroll":
                try:
                    self.driver.execute_script(
                        "window.scrollTo(arguments[0],arguments[1])",
                        step["x"], step["y"]
                    )
                except:
                    pass

            # WAIT
            elif act == "wait":
                time.sleep(step.get("seconds", 1))

            # SCREENSHOT
            elif act == "screenshot":
                try:
                    self.driver.save_screenshot(step["path"])
                except:
                    pass

            # DRAG & DROP (NOW WORKING)
            elif act == "drag":
                src = self._find(step["from"]["selector"])
                dst = self._find(step["to"]["selector"])
                if src and dst:
                    try:
                        ActionChains(self.driver).drag_and_drop(src, dst).perform()
                    except:
                        pass

            # NAVIGATION
            elif act == "navigate":
                try:
                    self.driver.get(step["url"])
                    time.sleep(1)
                    self.install_listener()
                except:
                    pass

            time.sleep(0.25)
