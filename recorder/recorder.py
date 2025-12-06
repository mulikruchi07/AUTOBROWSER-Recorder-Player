# recorder/recorder.py
import json, time, threading, os
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

# JS listener that we will both inject via CDP and execute on current doc.
JS_LISTENER = """
(function(){
  try {
    if (window.top.__AUTOBROWSER_INSTALLED__) return 'already';
    window.top.__AUTOBROWSER_INSTALLED__ = true;
    window.top.__AUTOBROWSER_EVENTS__ = window.top.__AUTOBROWSER_EVENTS__ || [];

    function cssPath(el){
      if(!el) return '';
      try {
        if(el.id) return '#'+el.id;
        var parts = [];
        var node = el;
        while(node && node.nodeType===1 && node.tagName.toLowerCase()!=='html'){
          var sel = node.tagName.toLowerCase();
          if(node.className){
            sel += '.' + node.className.trim().split(/\s+/).join('.');
          }
          var sib = node; var nth = 1;
          while(sib.previousElementSibling){
            sib = sib.previousElementSibling;
            if(sib.tagName === node.tagName) nth++;
          }
          if(nth>1) sel += ':nth-of-type('+nth+')';
          parts.unshift(sel);
          node = node.parentElement;
        }
        return parts.join(' > ');
      } catch(e){ return ''; }
    }

    function push(ev){ try{ window.top.__AUTOBROWSER_EVENTS__.push(ev); }catch(e){} }

    document.addEventListener('click', function(e){
      try { push({action:'click', selector: cssPath(e.target), tag: e.target.tagName, text: (e.target.innerText||'').trim(), ts: Date.now()}); } catch(e){}
    }, true);

    document.addEventListener('input', function(e){
      try {
        var el = e.target;
        var tag = el.tagName && el.tagName.toLowerCase();
        if(tag === 'input' || tag === 'textarea' || el.isContentEditable){
          push({action:'type', selector: cssPath(el), value: el.value || el.innerText || '', ts: Date.now()});
        }
      } catch(e){}
    }, true);

    document.addEventListener('change', function(e){
      try { push({action:'type', selector: cssPath(e.target), value: e.target.value||'', ts: Date.now()}); } catch(e){}
    }, true);

    var sTO = null;
    window.addEventListener('scroll', function(){
      try{
        if(sTO) clearTimeout(sTO);
        sTO = setTimeout(function(){ push({action:'scroll', x: window.scrollX||0, y: window.scrollY||0, ts: Date.now()}); }, 200);
      }catch(e){}
    }, true);

    document.addEventListener('dragstart', function(e){ try{ push({action:'dragstart', selector: cssPath(e.target), ts: Date.now()}); }catch(e){} }, true);
    document.addEventListener('dragend', function(e){ try{ push({action:'dragend', selector: cssPath(e.target), ts: Date.now()}); }catch(e){} }, true);

    window.addEventListener('beforeunload', function(){ try{ push({action:'navigate_marker', url: location.href, ts: Date.now()}); }catch(e){} });

    return 'ok';
  } catch(ex) { return 'err'; }
})();
"""

JS_FLUSH = """
(function(){
  try {
    var ev = (window.top && window.top.__AUTOBROWSER_EVENTS__) || [];
    var out = JSON.stringify(ev.splice(0, ev.length));
    return out;
  } catch(e) { return '[]'; }
})();
"""

class Recorder:
    def __init__(self, driver, poll_interval=0.6):
        self.driver = driver
        self.poll_interval = poll_interval
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self.script = []

    # install via CDP (persistent) and also injection into current document
    def install_listener(self):
        if not self.driver:
            return False
        ok = False
        try:
            # persistent injection so new documents have this too
            try:
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": JS_LISTENER})
                ok = True
            except Exception:
                ok = ok or False
            # also inject into current window
            try:
                res = self.driver.execute_script(JS_LISTENER)
                ok = True if res else ok
            except Exception:
                ok = ok or False
            return ok
        except Exception:
            return False

    def _append(self, ev):
        action = ev.get('action')
        if action == 'click':
            self.script.append({'action':'click','selector':ev.get('selector'),'meta':{'tag':ev.get('tag'),'text':ev.get('text')},'ts':ev.get('ts')})
        elif action == 'type':
            self.script.append({'action':'type','selector':ev.get('selector'),'value':ev.get('value',''),'ts':ev.get('ts')})
        elif action == 'scroll':
            self.script.append({'action':'scroll','x':int(ev.get('x',0)),'y':int(ev.get('y',0)),'ts':ev.get('ts')})
        elif action in ('dragstart','dragend'):
            self.script.append({'action':action,'selector':ev.get('selector'),'ts':ev.get('ts')})
        elif action == 'navigate_marker':
            self.script.append({'action':'navigate_marker','url':ev.get('url'),'ts':ev.get('ts')})
        else:
            self.script.append(ev)

    def _poll(self):
        while self._running:
            try:
                raw = self.driver.execute_script(JS_FLUSH)
                if raw:
                    try:
                        arr = json.loads(raw)
                    except Exception:
                        arr = []
                    if arr:
                        with self._lock:
                            for ev in arr:
                                self._append(ev)
                time.sleep(self.poll_interval)
            except WebDriverException:
                time.sleep(self.poll_interval)
            except Exception:
                time.sleep(self.poll_interval)

    def start(self):
        if not self.driver:
            raise RuntimeError("Driver not set")
        # ensure listener installed
        self.install_listener()
        self._running = True
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def get_script(self):
        with self._lock:
            return list(self.script)

    def clear(self):
        with self._lock:
            self.script = []

    def save(self, path):
        with self._lock:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.script, f, indent=2, ensure_ascii=False)

    def load(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        with self._lock:
            self.script = data

    def add_wait(self, seconds):
        with self._lock:
            self.script.append({'action':'wait','seconds':float(seconds),'ts':int(time.time()*1000)})

    def add_screenshot(self, path=None):
        if not self.driver:
            return None
        if not path:
            path = os.path.abspath(f"screenshot_{int(time.time())}.png")
        try:
            self.driver.save_screenshot(path)
            with self._lock:
                self.script.append({'action':'screenshot','path':path,'ts':int(time.time()*1000)})
            return path
        except Exception:
            return None

    def add_scroll(self, x=None, y=None):
        try:
            if x is None or y is None:
                x = int(self.driver.execute_script("return window.scrollX || 0"))
                y = int(self.driver.execute_script("return window.scrollY || 0"))
        except Exception:
            x,y = 0,0
        with self._lock:
            self.script.append({'action':'scroll','x':x,'y':y,'ts':int(time.time()*1000)})

    # diagnostic: push a test event from JS and then poll it back
    def test_listener(self):
        if not self.driver:
            return False, "no-driver"
        try:
            # push a test event directly into top storage
            js = "window.top.__AUTOBROWSER_EVENTS__ = window.top.__AUTOBROWSER_EVENTS__ || []; window.top.__AUTOBROWSER_EVENTS__.push({action:'_test', ts:Date.now()}); return true;"
            try:
                self.driver.execute_script(js)
            except Exception:
                # fall back to CDP method (some environments allow)
                pass
            # immediately flush once
            raw = self.driver.execute_script(JS_FLUSH)
            try:
                arr = json.loads(raw)
            except Exception:
                arr = []
            # check if test event present
            found = any(a.get('action') == '_test' for a in arr)
            return found, f"polled:{len(arr)}"
        except Exception as e:
            return False, str(e)

    # playback
    def _find(self, selector):
        if not selector: return None
        try:
            return self.driver.find_element(By.CSS_SELECTOR, selector)
        except Exception:
            try:
                return self.driver.find_element(By.XPATH, selector)
            except Exception:
                return None

    def play(self, delay_between=0.6):
        actions = self.get_script()
        for step in actions:
            try:
                a = step.get('action')
                if a == 'click':
                    el = self._find(step.get('selector'))
                    if el:
                        try:
                            el.click()
                        except Exception:
                            try:
                                self.driver.execute_script("arguments[0].click()", el)
                            except:
                                pass
                elif a == 'type':
                    el = self._find(step.get('selector'))
                    if el:
                        try:
                            el.clear()
                            el.send_keys(step.get('value',''))
                        except Exception:
                            pass
                elif a == 'scroll':
                    try:
                        self.driver.execute_script("window.scrollTo(arguments[0], arguments[1])", int(step.get('x',0)), int(step.get('y',0)))
                    except Exception:
                        pass
                elif a == 'wait':
                    time.sleep(float(step.get('seconds',1)))
                elif a == 'screenshot':
                    p = step.get('path')
                    if p:
                        try:
                            self.driver.save_screenshot(p)
                        except Exception:
                            pass
                elif a == 'navigate':
                    url = step.get('url')
                    if url:
                        self.driver.get(url)
                        time.sleep(1)
                        try:
                            self.install_listener()
                        except:
                            pass
                elif a in ('dragstart','dragend'):
                    el = self._find(step.get('selector'))
                    if el:
                        try:
                            self.driver.execute_script("""
                                const el = arguments[0];
                                const ev = new DragEvent(arguments[1], {bubbles:true, cancelable:true});
                                el.dispatchEvent(ev);
                            """, el, a)
                        except Exception:
                            pass
            except Exception:
                pass
            time.sleep(delay_between)
