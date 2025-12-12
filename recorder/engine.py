# recorder/engine.py
import json
import time
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException

JS_LISTENER = """
(function(){
  // try top-level storage for cross-frame collection
  try {
    if (!window.top.__AUTOBROWSER_EVENTS__) window.top.__AUTOBROWSER_EVENTS__ = [];
    var STORE = window.top.__AUTOBROWSER_EVENTS__;
  } catch(e) {
    if (!window.__AUTOBROWSER_EVENTS__) window.__AUTOBROWSER_EVENTS__ = [];
    var STORE = window.__AUTOBROWSER_EVENTS__;
  }

  if (STORE._INSTALLED) return "already";
  STORE._INSTALLED = true;

  function push(ev){
    try { STORE.push(ev); } catch(e) {}
  }

  function cssPath(el){
    if (!el) return "";
    if (el.id) return "#" + el.id;
    var path = [];
    var node = el;
    while(node && node.nodeType === 1 && node.tagName.toLowerCase() !== 'html'){
      var sel = node.tagName.toLowerCase();
      if (node.className) sel += "." + node.className.trim().split(/\s+/).join('.');
      var sib = node, nth = 1;
      while(sib.previousElementSibling){
        sib = sib.previousElementSibling;
        if (sib.tagName === node.tagName) nth++;
      }
      if (nth > 1) sel += ":nth-of-type(" + nth + ")";
      path.unshift(sel);
      node = node.parentElement;
    }
    return path.join(' > ');
  }

  // ------------------
  // Click listener (suppressed if drag just occurred)
  // ------------------
  var _suppressNextClick = false;
  document.addEventListener('click', function(e){
    try {
      if (_suppressNextClick) { _suppressNextClick = false; return; }
      push({ action: 'click', selector: cssPath(e.target), ts: Date.now() });
    } catch(ex) {}
  }, true);

  // ------------------
  // Type/input: debounce per element, only push if value changed
  // ------------------
  var __input_timers = {};
  var __input_last = {}; // selector -> lastValue recorded
  function schedule_input(el){
    try {
      var sel = cssPath(el);
      var value = (el.value !== undefined) ? el.value : (el.innerText || '');
      if (!__input_timers[sel]) __input_timers[sel] = null;
      if (__input_timers[sel]) clearTimeout(__input_timers[sel]);
      __input_timers[sel] = setTimeout(function(){
        try {
          if (__input_last[sel] !== value) {
            __input_last[sel] = value;
            push({ action: 'type', selector: sel, value: value, ts: Date.now() });
          }
        } catch(e){}
        __input_timers[sel] = null;
      }, 600); // 600ms debounce
    } catch(e){}
  }
  document.addEventListener('input', function(e){
    try { schedule_input(e.target); } catch(e){}
  }, true);
  // change fallback
  document.addEventListener('change', function(e){
    try { schedule_input(e.target); } catch(e){}
  }, true);

  // ------------------
  // Scroll (debounced)
  // ------------------
  var _scrTo = null;
  window.addEventListener('scroll', function(){
    try {
      if (_scrTo) clearTimeout(_scrTo);
      _scrTo = setTimeout(function(){
        try {
          push({ action:'scroll', x: window.scrollX || 0, y: window.scrollY || 0, ts: Date.now() });
        } catch(e){}
      }, 120);
    } catch(e){}
  }, true);

  // ------------------
  // Drag detection (mousedown/mouseup pair). Only record drag when moved more than threshold.
  // If drag recorded, suppress the next click event.
  // ------------------
  var DRAG = { active:false, sx:0, sy:0, sselector:'' };
  var DRAG_THRESHOLD = 8; // pixels
  document.addEventListener('mousedown', function(e){
    try {
      DRAG.active = true;
      DRAG.sx = e.clientX;
      DRAG.sy = e.clientY;
      DRAG.sselector = cssPath(e.target);
    } catch(e){}
  }, true);

  document.addEventListener('mouseup', function(e){
    try {
      if (!DRAG.active) return;
      DRAG.active = false;
      var dx = Math.abs(e.clientX - DRAG.sx);
      var dy = Math.abs(e.clientY - DRAG.sy);
      var moved = Math.sqrt(dx*dx + dy*dy);
      var tselector = cssPath(e.target);
      if (moved >= DRAG_THRESHOLD) {
        _suppressNextClick = true;
        push({
          action: 'drag',
          from: { selector: DRAG.sselector, x: DRAG.sx, y: DRAG.sy },
          to:   { selector: tselector, x: e.clientX, y: e.clientY },
          ts: Date.now()
        });
      } else {
        // no drag; leave normal click handler to record click
      }
    } catch(e){}
  }, true);

  // ------------------
  // Navigation detection
  // ------------------
  window.addEventListener('hashchange', function(){ try{ push({action:'navigate', url: location.href, ts: Date.now()}); }catch(e){} });
  window.addEventListener('popstate', function(){ try{ push({action:'navigate', url: location.href, ts: Date.now()}); }catch(e){} });
  document.addEventListener('DOMContentLoaded', function(){ try{ push({action:'navigate', url: location.href, ts: Date.now()}); }catch(e){} });

  return "ok";
})();
"""

# JS_FLUSH returns the array (splice) so execute_script returns list in Python
JS_FLUSH = r"return (window.top && window.top.__AUTOBROWSER_EVENTS__ ? window.top.__AUTOBROWSER_EVENTS__.splice(0, window.top.__AUTOBROWSER_EVENTS__.length) : (window.__AUTOBROWSER_EVENTS__ ? window.__AUTOBROWSER_EVENTS__.splice(0, window.__AUTOBROWSER_EVENTS__.length) : []));"


class Recorder:
    def __init__(self, driver, poll_interval=0.25):
        self.driver = driver
        self.script = []
        self.running = False
        self.poll_interval = poll_interval
        self._thread = None
        self._recording_started = False

    def install_listener(self):
        # best-effort persistent injection via CDP
        try:
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": JS_LISTENER})
        except Exception:
            pass
        # inject now
        try:
            self.driver.execute_script(JS_LISTENER)
        except Exception:
            pass

        # further attempt: inject into same-origin iframes by switching (best-effort)
        try:
            frames = self.driver.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(frames)):
                try:
                    self.driver.switch_to.frame(i)
                    try:
                        self.driver.execute_script(JS_LISTENER)
                    except Exception:
                        pass
                except Exception:
                    pass
                finally:
                    try:
                        self.driver.switch_to.default_content()
                    except Exception:
                        pass
        except Exception:
            pass

    def _poll(self):
        while self.running:
            try:
                events = self.driver.execute_script(JS_FLUSH)
            except WebDriverException:
                events = []
            except Exception:
                events = []

            if events:
                for ev in events:
                    self.script.append(ev)
            time.sleep(self.poll_interval)

    def start(self):
        if not self.driver:
            raise RuntimeError("Driver not set")
        # record initial URL as first step so playback can start from it
        try:
            cur = self.driver.current_url
            # only record if script empty or first entry not already navigate
            if not self.script or self.script[0].get("action") != "navigate":
                self.script.insert(0, {"action": "navigate", "url": cur, "ts": int(time.time()*1000)})
        except Exception:
            pass

        self.install_listener()
        self.running = True
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()
        self._recording_started = True

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

    def get_script(self):
        return list(self.script)

    def clear(self):
        self.script = []

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.script, f, indent=2, ensure_ascii=False)

    # find element (only top-level document); return element or None
    def _find(self, sel):
        if not sel:
            return None
        try:
            return self.driver.find_element(By.CSS_SELECTOR, sel)
        except Exception:
            try:
                return self.driver.find_element(By.XPATH, sel)
            except Exception:
                return None

    def play(self, delay_between=0.35):
        if not self.driver:
            raise RuntimeError("Driver not set for playback")
        if not self.script:
            return

        # If first step is navigate, go to it first
        first = self.script[0]
        try:
            if first.get("action") == "navigate" and first.get("url"):
                try:
                    self.driver.get(first.get("url"))
                    time.sleep(1)
                    # re-install listener after navigation
                    try:
                        self.install_listener()
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass

        for step in list(self.script):
            act = step.get("action")
            try:
                if act == "click":
                    sel = step.get("selector")
                    el = self._find(sel)
                    if el:
                        try:
                            el.click()
                        except Exception:
                            try:
                                self.driver.execute_script("arguments[0].click();", el)
                            except:
                                pass

                elif act == "type":
                    sel = step.get("selector")
                    val = step.get("value", "")
                    el = self._find(sel)
                    if el:
                        try:
                            el.clear()
                            el.send_keys(val)
                        except Exception:
                            pass

                elif act == "scroll":
                    x = int(step.get("x", 0))
                    y = int(step.get("y", 0))
                    try:
                        self.driver.execute_script("window.scrollTo(arguments[0], arguments[1]);", x, y)
                    except:
                        pass

                elif act == "wait":
                    time.sleep(float(step.get("seconds", 1)))

                elif act == "screenshot":
                    path = step.get("path")
                    if path:
                        try:
                            self.driver.save_screenshot(path)
                        except:
                            pass

                elif act == "drag":
                    frm = step.get("from", {})
                    to = step.get("to", {})
                    sel_from = frm.get("selector")
                    sel_to = to.get("selector")
                    el_from = self._find(sel_from)
                    el_to = self._find(sel_to)
                    if el_from and el_to:
                        try:
                            ActionChains(self.driver).drag_and_drop(el_from, el_to).perform()
                        except Exception:
                            # fallback: dispatch drag events via JS
                            try:
                                self.driver.execute_script("""
                                  function simulateDragDrop(src, dst){
                                    var EVENT_TYPES = { DRAG_START: 'dragstart', DROP: 'drop', DRAG_END: 'dragend'};
                                    function create(type){
                                      var e = new CustomEvent(type, {bubbles:true, cancelable:true});
                                      e.dataTransfer = { data: {} , setData:function(k,v){this.data[k]=v}, getData:function(k){return this.data[k]} };
                                      return e;
                                    }
                                    var s = arguments[0], d = arguments[1];
                                    var ds = create(EVENT_TYPES.DRAG_START); s.dispatchEvent(ds);
                                    var dd = create(EVENT_TYPES.DROP); d.dispatchEvent(dd);
                                    var de = create(EVENT_TYPES.DRAG_END); s.dispatchEvent(de);
                                  }
                                  simulateDragDrop(arguments[0], arguments[1]);
                                """, el_from, el_to)
                            except Exception:
                                pass
                    else:
                        # fallback by coordinates in top document
                        try:
                            sx = frm.get("x", 0); sy = frm.get("y", 0); tx = to.get("x", 0); ty = to.get("y", 0)
                            self.driver.execute_script("""
                                var sx=arguments[0], sy=arguments[1], tx=arguments[2], ty=arguments[3];
                                function ev(t,x,y){ return new MouseEvent(t, {bubbles:true, cancelable:true, clientX:x, clientY:y}); }
                                var s = document.elementFromPoint(sx, sy);
                                var t = document.elementFromPoint(tx, ty);
                                if(s) s.dispatchEvent(ev('mousedown', sx, sy));
                                if(s) s.dispatchEvent(ev('mousemove', (sx+tx)/2, (sy+ty)/2));
                                if(t) t.dispatchEvent(ev('mouseup', tx, ty));
                            """, sx, sy, tx, ty)
                        except Exception:
                            pass

                elif act == "navigate":
                    url = step.get("url")
                    if url:
                        try:
                            self.driver.get(url)
                            time.sleep(0.8)
                            try:
                                self.install_listener()
                            except:
                                pass
                        except:
                            pass

            except Exception:
                # ignore step-level errors
                pass

            time.sleep(delay_between)
