# recorder/engine.py
import json, time, threading, os
from selenium.webdriver.common.by import By

# JAVASCRIPT LISTENER
 
JS_LISTENER = """
window.__EVTS = window.__EVTS || [];

// CSS path builder
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

// DRAG START
document.addEventListener("dragstart", e => {
    window.__EVTS.push({
        action: "dragstart",
        selector: cssPath(e.target),
        ts: Date.now()
    });
}, true);

// DRAG END
document.addEventListener("dragend", e => {
    window.__EVTS.push({
        action: "dragend",
        selector: cssPath(e.target),
        ts: Date.now()
    });
}, true);
"""

# Flush events
JS_FLUSH = "return window.__EVTS.splice(0, window.__EVTS.length);"

# RECORDER CLASS

class Recorder:
    def __init__(self, driver):
        self.driver = driver
        self.script = []
        self.running = False

    def install_listener(self):
        try:
            self.driver.execute_script(JS_LISTENER)
            return True
        except:
            return False

    def _poll(self):
        while self.running:
            try:
                events = self.driver.execute_script(JS_FLUSH)
            except:
                events = []

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

    # PLAYBACK
    def _find(self, sel):
        try: return self.driver.find_element(By.CSS_SELECTOR, sel)
        except: return None

    def play(self):
        for step in self.script:
            act = step["action"]

            # CLICK
            if act == "click":
                el = self._find(step["selector"])
                if el:
                    try: el.click()
                    except: pass

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
                time.sleep(step["seconds"])

            # SCREENSHOT
            elif act == "screenshot":
                try:
                    self.driver.save_screenshot(step["path"])
                except:
                    pass

            # DRAG START
            elif act == "dragstart":
                el = self._find(step["selector"])
                if el:
                    try:
                        self.driver.execute_script("""
                            const ev = new DragEvent('dragstart', { bubbles:true });
                            arguments[0].dispatchEvent(ev);
                        """, el)
                    except:
                        pass

            # DRAG END
            elif act == "dragend":
                el = self._find(step["selector"])
                if el:
                    try:
                        self.driver.execute_script("""
                            const ev = new DragEvent('dragend', { bubbles:true });
                            arguments[0].dispatchEvent(ev);
                        """, el)
                    except:
                        pass

            time.sleep(0.25)
