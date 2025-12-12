# recorder/engine.py
import json
import time
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException

JS_LISTENER = """
(function() {
    try {
        if (!window.top.__AUTOBROWSER_EVENTS__)
            window.top.__AUTOBROWSER_EVENTS__ = [];
        var STORE = window.top.__AUTOBROWSER_EVENTS__;
    } catch(e) {
        if (!window.__AUTOBROWSER_EVENTS__)
            window.__AUTOBROWSER_EVENTS__ = [];
        var STORE = window.__AUTOBROWSER_EVENTS__;
    }

    if (STORE._INSTALLED) return;
    STORE._INSTALLED = true;

    function push(ev) {
        try { STORE.push(ev); } catch(e) {}
    }

    function cssPath(el) {
        if (!el) return "";
        if (el.id) return "#" + el.id;
        var path = [];
        while (el && el.nodeType === 1 && el.tagName.toLowerCase() !== "html") {
            var seg = el.tagName.toLowerCase();
            if (el.className)
                seg += "." + el.className.trim().split(/\s+/).join(".");
            var sib = el, nth = 1;
            while (sib = sib.previousElementSibling)
                if (sib.tagName === el.tagName) nth++;
            if (nth > 1) seg += ":nth-of-type(" + nth + ")";
            path.unshift(seg);
            el = el.parentElement;
        }
        return path.join(" > ");
    }

    // -------------------------------------------------------
    // CLICK (suppressed if drag happened)
    // -------------------------------------------------------
    var suppressClick = false;
    document.addEventListener("click", function(e) {
        if (suppressClick) { suppressClick = false; return; }
        push({ action: "click", selector: cssPath(e.target), ts: Date.now() });
    }, true);

    // -------------------------------------------------------
    // TYPING — debounce, only value change
    // -------------------------------------------------------
    var debounceTimers = {};
    var lastValues = {};

    function queueInput(target) {
        var sel = cssPath(target);
        var val = target.value || target.innerText || "";
        if (debounceTimers[sel]) clearTimeout(debounceTimers[sel]);

        debounceTimers[sel] = setTimeout(function() {
            if (lastValues[sel] !== val) {
                lastValues[sel] = val;
                push({ action: "type", selector: sel, value: val, ts: Date.now() });
            }
            debounceTimers[sel] = null;
        }, 500);
    }

    document.addEventListener("input", e => queueInput(e.target), true);
    document.addEventListener("change", e => queueInput(e.target), true);

    // -------------------------------------------------------
    // SCROLL (debounced)
    // -------------------------------------------------------
    var scrollTimer = null;
    window.addEventListener("scroll", () => {
        if (scrollTimer) clearTimeout(scrollTimer);
        scrollTimer = setTimeout(() => {
            push({
                action: "scroll",
                x: window.scrollX || 0,
                y: window.scrollY || 0,
                ts: Date.now()
            });
        }, 120);
    }, true);

    // -------------------------------------------------------
    // DRAG — mouse + pointer
    // -------------------------------------------------------
    var DRAG = { active: false, sx: 0, sy: 0, sel: "" };
    var THRESH = 8;

    function startDrag(e) {
        DRAG.active = true;
        DRAG.sx = e.clientX;
        DRAG.sy = e.clientY;
        DRAG.sel = cssPath(e.target);
    }

    function endDrag(e) {
        if (!DRAG.active) return;
        DRAG.active = false;

        var dx = e.clientX - DRAG.sx;
        var dy = e.clientY - DRAG.sy;
        var dist = Math.sqrt(dx*dx + dy*dy);

        if (dist >= THRESH) {
            suppressClick = true;
            push({
                action: "drag",
                from: { selector: DRAG.sel, x: DRAG.sx, y: DRAG.sy },
                to:   { selector: cssPath(e.target), x: e.clientX, y: e.clientY },
                ts: Date.now()
            });
        }
    }

    document.addEventListener("mousedown", startDrag, true);
    document.addEventListener("mouseup", endDrag, true);
    document.addEventListener("pointerdown", startDrag, true);
    document.addEventListener("pointerup", endDrag, true);

    // -------------------------------------------------------
    // NAVIGATION
    // -------------------------------------------------------
    window.addEventListener("hashchange", () => {
        push({ action: "navigate", url: location.href, ts: Date.now() });
    });

    window.addEventListener("popstate", () => {
        push({ action: "navigate", url: location.href, ts: Date.now() });
    });

    document.addEventListener("DOMContentLoaded", () => {
        push({ action: "navigate", url: location.href, ts: Date.now() });
    });

})();
"""

JS_FLUSH = """
return (window.top && window.top.__AUTOBROWSER_EVENTS__
    ? window.top.__AUTOBROWSER_EVENTS__.splice(0, window.top.__AUTOBROWSER_EVENTS__.length)
    : (window.__AUTOBROWSER_EVENTS__
        ? window.__AUTOBROWSER_EVENTS__.splice(0, window.__AUTOBROWSER_EVENTS__.length)
        : []));
"""
class Recorder:
    def __init__(self, driver):
        self.driver = driver
        self.script = []
        self.running = False
        self.pause_recording = False
        self.thread = None

    def install_listener(self):
        try:
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
                {"source": JS_LISTENER})
        except:
            pass

        try:
            self.driver.execute_script(JS_LISTENER)
        except:
            pass

        # Inject into accessible iframes
        try:
            frames = self.driver.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(frames)):
                try:
                    self.driver.switch_to.frame(i)
                    self.driver.execute_script(JS_LISTENER)
                except:
                    pass
                finally:
                    self.driver.switch_to.default_content()
        except:
            pass

    def _poll(self):
        while self.running:
            try:
                events = self.driver.execute_script(JS_FLUSH)
            except WebDriverException:
                events = []

            if not self.pause_recording:
                for ev in events:
                    self.script.append(ev)

            time.sleep(0.25)

    def start(self):
        # record current URL as starting point
        try:
            self.script.insert(0, {
                "action": "navigate",
                "url": self.driver.current_url,
                "ts": int(time.time()*1000)
            })
        except:
            pass

        self.install_listener()
        self.running = True
        self.thread = threading.Thread(target=self._poll, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    # Pause during wait block
    def pause(self):
        self.pause_recording = True

    def resume(self):
        self.pause_recording = False

    def get_script(self):
        return self.script

    def clear(self):
        self.script = []

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.script, f, indent=2)

    def _find(self, sel):
        try:
            return self.driver.find_element(By.CSS_SELECTOR, sel)
        except:
            return None

    def play(self):
        script = list(self.script)

        # find first navigation always
        start_url = None
        for ev in script:
            if ev["action"] == "navigate":
                start_url = ev["url"]
                break

        if start_url:
            try:
                self.driver.get(start_url)
                time.sleep(1)
                self.install_listener()
            except:
                pass

        # play the steps
        for step in script:
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
                        "window.scrollTo(arguments[0], arguments[1]);",
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

            # DRAG
            elif act == "drag":
                src = self._find(step["from"]["selector"])
                dst = self._find(step["to"]["selector"])
                if src and dst:
                    try:
                        ActionChains(self.driver).drag_and_drop(src, dst).perform()
                    except:
                        pass

            # NAVIGATE
            elif act == "navigate":
                try:
                    self.driver.get(step["url"])
                    time.sleep(1)
                    self.install_listener()
                except:
                    pass

            time.sleep(0.25)
