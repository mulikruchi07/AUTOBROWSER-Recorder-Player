import json, time, threading, os
from selenium.webdriver.common.by import By

JS_LISTENER = """
window.__EVTS = window.__EVTS || [];
function cssPath(el){
    if (!el) return "";
    if (el.id) return "#" + el.id;
    let path = [];
    while (el && el.nodeType === 1 && el.tagName.toLowerCase() !== "html") {
        let selector = el.tagName.toLowerCase();
        if (el.className) {
            selector += "." + el.className.trim().replace(/\s+/g, ".");
        }
        let sib = el, nth = 1;
        while (sib = sib.previousElementSibling) {
            if (sib.tagName === el.tagName) nth++;
        }
        if (nth > 1) selector += ":nth-of-type(" + nth + ")";
        path.unshift(selector);
        el = el.parentElement;
    }
    return path.join(" > ");
}

document.addEventListener("click", e => {
    window.__EVTS.push({
        action: "click",
        selector: cssPath(e.target),
        ts: Date.now()
    });
}, true);

document.addEventListener("input", e => {
    window.__EVTS.push({
        action: "type",
        selector: cssPath(e.target),
        value: e.target.value || "",
        ts: Date.now()
    });
}, true);
"""

JS_FLUSH = """return window.__EVTS.splice(0, window.__EVTS.length);"""

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
            events = self.driver.execute_script(JS_FLUSH)
            for ev in events:
                self.script.append(ev)
            time.sleep(0.3)

    def start(self):
        self.install_listener()
        self.running = True
        threading.Thread(target=self._poll, daemon=True).start()

    def stop(self):
        self.running = False

    def get_script(self):
        return self.script

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.script, f, indent=2)
