# recorder/recorder.py
import json
import time
import threading
from selenium.webdriver.common.by import By
from selenium.common.exceptions import JavascriptException, WebDriverException, NoSuchElementException

JS_INJECT_LISTENER = r"""
(function(){

    // Prevent duplicate installation
    if (window.__AUDIOX_RECORDER__) { return "already"; }
    window.__AUDIOX_RECORDER__ = true;

    // Event storage
    window.__AUDIOX_EVENTS__ = [];

    // Utility: CSS path generator
    function cssPath(node){
        if (!node) return "";
        if (node.id) return "#" + node.id;
        var path = [];
        while(node && node.nodeType === 1 && node.tagName.toLowerCase() !== "html"){
            var selector = node.tagName.toLowerCase();
            if(node.className){
                selector += "." + node.className.trim().split(/\\s+/).join(".");
            }
            var sibling = node;
            var nth = 1;
            while(sibling.previousElementSibling){
                sibling = sibling.previousElementSibling;
                if (sibling.tagName === node.tagName) nth++;
            }
            if (nth > 1) selector += ":nth-of-type(" + nth + ")";
            path.unshift(selector);
            node = node.parentElement;
        }
        return path.join(" > ");
    }

    // Capture click
    document.addEventListener("click", function(e){
        let el = e.target;
        let sel = cssPath(el);
        let text = (el.innerText || "").trim();
        window.__AUDIOX_EVENTS__.push({
            action: "click",
            selector: sel,
            text: text,
            ts: Date.now()
        });
    }, true);

    // Capture typing
    document.addEventListener("input", function(e){
        let el = e.target;
        let sel = cssPath(el);
        let val = el.value || "";
        if (val && val.trim() !== ""){
            window.__AUDIOX_EVENTS__.push({
                action: "type",
                selector: sel,
                value: val,
                ts: Date.now()
            });
        }
    }, true);

    // Capture navigation
    window.addEventListener("beforeunload", function(){
        window.__AUDIOX_EVENTS__.push({
            action: "navigate",
            url: document.location.href,
            ts: Date.now()
        });
    });

    return "ok";
})();
"""

JS_FLUSH_EVENTS = r"""
(function(){
    let ev = window.__AUDIOX_EVENTS__ || [];
    let out = JSON.stringify(ev.splice(0, ev.length));
    return out;
})();
"""

class Recorder:
    def __init__(self, driver, poll_interval=0.8):
        self.driver = driver
        self.poll_interval = poll_interval
        self._recording = False
        self._thread = None
        self.script = []
        self._lock = threading.Lock()

    def inject(self):
        """Inject listener into current page."""
        try:
            return self.driver.execute_script(JS_INJECT_LISTENER)
        except Exception:
            return None

    def _poll(self):
        """Polling thread that fetches recorded events."""
        while self._recording:
            try:
                raw = self.driver.execute_script(JS_FLUSH_EVENTS)
                if not raw:
                    time.sleep(self.poll_interval)
                    continue
                events = json.loads(raw)
                if events:
                    with self._lock:
                        for e in events:
                            self.script.append(e)
                time.sleep(self.poll_interval)
            except:
                break

    def start(self):
        """Start recording."""
        self.inject()              # inject now
        self._recording = True
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop recording."""
        self._recording = False
        if self._thread:
            self._thread.join()

    def get_script(self):
        """Return a copy of the script."""
        with self._lock:
            return list(self.script)

    def clear(self):
        with self._lock:
            self.script = []

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.get_script(), f, indent=2)

    def load(self, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        with self._lock:
            self.script = data

    def play(self):
        """Play back the recorded script."""
        actions = self.get_script()
        for step in actions:
            try:
                act = step.get("action")
                sel = step.get("selector")
                if act == "click" and sel:
                    try:
                        el = self.driver.find_element(By.CSS_SELECTOR, sel)
                        el.click()
                    except:
                        pass

                elif act == "type" and sel:
                    try:
                        el = self.driver.find_element(By.CSS_SELECTOR, sel)
                        el.clear()
                        el.send_keys(step.get("value", ""))
                    except:
                        pass

                elif act == "navigate":
                    url = step.get("url")
                    if url:
                        self.driver.get(url)
                        time.sleep(1)
                        self.inject()  # <-- CRITICAL: re-inject after navigation

            except:
                pass

            time.sleep(0.7)
