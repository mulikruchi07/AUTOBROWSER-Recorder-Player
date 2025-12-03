# recorder/recorder.py
import json
import time
import threading
from selenium.webdriver.common.by import By
from selenium.common.exceptions import JavascriptException, WebDriverException, NoSuchElementException

JS_INJECT_LISTENER = r"""
(function(){
  if(window.__autobrowser_recorder_installed) return 'already';
  window.__autobrowser_recorder_installed = true;
  window.__autobrowser_events = window.__autobrowser_events || [];

  function cssPath(el){
    if(!el) return '';
    if(el.id) return '#'+el.id;
    var path = [];
    var node = el;
    while(node && node.nodeType===1 && node.tagName.toLowerCase()!=='html'){
      var selector = node.tagName.toLowerCase();
      if(node.className){
        var cls = node.className.trim().split(/\s+/).join('.');
        if(cls) selector += '.'+cls;
      }
      var sib = node;
      var nth = 1;
      while(sib.previousElementSibling){
        sib = sib.previousElementSibling;
        if(sib.tagName===node.tagName) nth++;
      }
      if(nth>1) selector += ':nth-of-type('+nth+')';
      path.unshift(selector);
      node = node.parentElement;
    }
    return path.join(' > ');
  }

  function safeValue(el){
    if(!el) return '';
    try{
      if(el.tagName.toLowerCase()==='input' || el.tagName.toLowerCase()==='textarea' || el.isContentEditable){
        var t = el.getAttribute('type') || '';
        if(t.toLowerCase()==='password') return '[password]';
        return el.value || el.innerText || '';
      }
      return '';
    }catch(e){
      return '';
    }
  }

  document.addEventListener('click', function(e){
    try{
      var el = e.target;
      var sel = cssPath(el);
      var tag = el.tagName.toLowerCase();
      var txt = (el.innerText||'').trim();
      window.__autobrowser_events.push({type:'click', selector:sel, tag:tag, text:txt, time:Date.now()});
    }catch(err){}
  }, true);

  // input capture: on blur record final value
  document.addEventListener('blur', function(e){
    try{
      var el = e.target;
      var tagName = el.tagName && el.tagName.toLowerCase();
      if(tagName==='input' || tagName==='textarea' || el.isContentEditable){
        var sel = cssPath(el);
        var val = safeValue(el);
        window.__autobrowser_events.push({type:'type', selector:sel, value:val, time:Date.now()});
      }
    }catch(err){}
  }, true);

  // also push on change events (selects)
  document.addEventListener('change', function(e){
    try{
      var el = e.target;
      var tagName = el.tagName && el.tagName.toLowerCase();
      if(tagName){
        var sel = cssPath(el);
        var val = safeValue(el);
        window.__autobrowser_events.push({type:'type', selector:sel, value:val, time:Date.now()});
      }
    }catch(err){}
  }, true);

  return 'ok';
})();
"""

JS_FLUSH_EVENTS = r"""
(function(){
  var ev = window.__autobrowser_events || [];
  var out = JSON.stringify(ev.splice(0, ev.length));
  return out;
})();
"""

class Recorder:
    def __init__(self, driver, poll_interval=1.0):
        self.driver = driver
        self._recording = False
        self._poll_interval = poll_interval
        self._thread = None
        self.script = []  # list of actions
        self._lock = threading.Lock()

    def start_inject(self):
        try:
            res = self.driver.execute_script(JS_INJECT_LISTENER)
            return res
        except JavascriptException as e:
            raise RuntimeError("JS injection failed: "+str(e))

    def _poll_loop(self):
        while self._recording:
            try:
                raw = self.driver.execute_script(JS_FLUSH_EVENTS)
                if raw:
                    events = json.loads(raw)
                    if events:
                        with self._lock:
                            for ev in events:
                                action = self._convert_event_to_action(ev)
                                if action:
                                    self.script.append(action)
                time.sleep(self._poll_interval)
            except (WebDriverException, JavascriptException):
                # driver closed or page navigation; stop polling safely
                break

    def _convert_event_to_action(self, ev):
        t = ev.get('type')
        if t == 'click':
            return {"action": "click", "selector": ev.get('selector'), "meta": {"tag": ev.get('tag'), "text": ev.get('text')}}
        if t == 'type':
            val = ev.get('value', '')
            # skip recording empty password values
            if val == '[password]':
                return None
            return {"action": "type", "selector": ev.get('selector'), "value": val}
        return None

    def start_recording(self):
        if self._recording:
            return
        # ensure listener installed on current page(s)
        self.start_inject()
        self._recording = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop_recording(self):
        self._recording = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def clear_script(self):
        with self._lock:
            self.script = []

    def get_script(self):
        with self._lock:
            return list(self.script)

    def save_script_to_file(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.get_script(), f, indent=2, ensure_ascii=False)

    def load_script_from_file(self, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        with self._lock:
            self.script = data

    # Player functions
    def play_script(self, delay_between=0.6):
        """
        Execute actions in self.script sequentially.
        Supports 'click' and 'type' actions; also supports 'navigate' and 'wait' if present.
        """
        actions = self.get_script()
        for a in actions:
            act = a.get("action")
            try:
                if act == "click":
                    sel = a.get("selector")
                    if not sel:
                        continue
                    try:
                        el = self.driver.find_element(By.CSS_SELECTOR, sel)
                        el.click()
                    except NoSuchElementException:
                        # try XPath fallback
                        try:
                            el = self.driver.find_element(By.XPATH, sel)
                            el.click()
                        except Exception:
                            pass
                elif act == "type":
                    sel = a.get("selector")
                    val = a.get("value", "")
                    if not sel:
                        continue
                    try:
                        el = self.driver.find_element(By.CSS_SELECTOR, sel)
                        el.clear()
                        el.send_keys(val)
                    except NoSuchElementException:
                        try:
                            el = self.driver.find_element(By.XPATH, sel)
                            el.clear()
                            el.send_keys(val)
                        except Exception:
                            pass
                elif act == "navigate":
                    url = a.get("url")
                    if url:
                        self.driver.get(url)
                elif act == "wait":
                    sec = float(a.get("seconds", 1))
                    time.sleep(sec)
                elif act == "screenshot":
                    path = a.get("path", "screenshot.png")
                    self.driver.save_screenshot(path)
            except Exception:
                # continue on error
                pass
            time.sleep(delay_between)
