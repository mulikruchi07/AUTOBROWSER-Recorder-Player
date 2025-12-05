# recorder/recorder.py
import json
import time
import threading
import os
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, JavascriptException, NoSuchElementException

# Robust injected JS:
# - installs once per page
# - records click, input, change, scroll (debounced), dragstart/dragend, navigation markers
# - exposes a flush function that returns and clears events
JS_INJECT_LISTENER = """
(function(){
  if(window.__AUTOBROWSER_INSTALLED__) return 'already';
  window.__AUTOBROWSER_INSTALLED__ = true;
  window.__AUTOBROWSER_EVENTS__ = window.__AUTOBROWSER_EVENTS__ || [];

  function cssPath(el){
    if(!el) return '';
    if(el.id) return '#'+el.id;
    var parts = [];
    var node = el;
    while(node && node.nodeType===1 && node.tagName.toLowerCase()!=='html'){
      var name = node.tagName.toLowerCase();
      if(node.className){
        var cls = node.className.trim().split(/\s+/).join('.');
        if(cls) name += '.'+cls;
      }
      var sibling = node;
      var nth = 1;
      while(sibling.previousElementSibling){
        sibling = sibling.previousElementSibling;
        if(sibling.tagName === node.tagName) nth++;
      }
      if(nth>1) name += ':nth-of-type('+nth+')';
      parts.unshift(name);
      node = node.parentElement;
    }
    return parts.join(' > ');
  }

  function pushEvent(ev){
    try{ window.__AUTOBROWSER_EVENTS__.push(ev); }catch(e){}
  }

  // Clicks
  document.addEventListener('click', function(e){
    try{
      var el = e.target;
      pushEvent({action:'click', selector: cssPath(el), tag: el.tagName, text: (el.innerText||'').trim(), ts: Date.now()});
    }catch(err){}
  }, true);

  // Input typing (input events). We record final value on blur as well to be safer.
  document.addEventListener('input', function(e){
    try{
      var el = e.target;
      var tag = el.tagName && el.tagName.toLowerCase();
      if(tag==='input' || tag==='textarea' || el.isContentEditable){
        pushEvent({action:'type', selector: cssPath(el), value: el.value || el.innerText || '', ts: Date.now()});
      }
    }catch(err){}
  }, true);

  document.addEventListener('change', function(e){
    try{
      var el = e.target;
      pushEvent({action:'type', selector: cssPath(el), value: el.value || '', ts: Date.now()});
    }catch(err){}
  }, true);

  // Scroll (debounced)
  var _lastScroll = 0;
  var _scrollTimeout = null;
  window.addEventListener('scroll', function(e){
    try{
      if(_scrollTimeout) clearTimeout(_scrollTimeout);
      _scrollTimeout = setTimeout(function(){
        try{
          pushEvent({action:'scroll', x: window.scrollX, y: window.scrollY, ts: Date.now()});
        }catch(e){}
      }, 250);
    }catch(err){}
  }, true);

  // Drag events
  document.addEventListener('dragstart', function(e){
    try{
      var el = e.target;
      pushEvent({action:'dragstart', selector: cssPath(el), ts: Date.now()});
    }catch(err){}
  }, true);
  document.addEventListener('dragend', function(e){
    try{
      var el = e.target;
      pushEvent({action:'dragend', selector: cssPath(el), ts: Date.now()});
    }catch(err){}
  }, true);

  // navigation marker
  window.addEventListener('beforeunload', function(){
    try{
      pushEvent({action:'navigate', url: location.href, ts: Date.now()});
    }catch(e){}
  });

  return 'ok';
})();
"""

JS_FLUSH_EVENTS = """
(function(){
  try{
    var ev = window.__AUTOBROWSER_EVENTS__ || [];
    var out = JSON.stringify(ev.splice(0, ev.length));
    return out;
  }catch(e){
    return '[]';
  }
})();
"""

class Recorder:
    def __init__(self, driver, poll_interval=0.6):
        self.driver = driver
        self.poll_interval = poll_interval
        self.recording = False
        self._thread = None
        self._lock = threading.Lock()
        self.script = []  # a list of action dicts

    # injection
    def inject(self):
        if not self.driver:
            return None
        try:
            return self.driver.execute_script(JS_INJECT_LISTENER)
        except (JavascriptException, WebDriverException):
            return None

    def _poll_loop(self):
        while self.recording:
            try:
                raw = self.driver.execute_script(JS_FLUSH_EVENTS)
                if raw:
                    try:
                        events = json.loads(raw)
                    except Exception:
                        events = []
                    if events:
                        with self._lock:
                            for ev in events:
                                self._append_event(ev)
                time.sleep(self.poll_interval)
            except Exception:
                # driver gone or page navigation heavy
                time.sleep(self.poll_interval)
                continue

    def start(self):
        if not self.driver:
            raise RuntimeError("No driver to record from")
        # try inject multiple times (useful if page not ready)
        try:
            self.inject()
        except Exception:
            pass
        self.recording = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.recording = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def _append_event(self, ev):
        # Normalize events to our action format
        action = ev.get('action')
        if action == 'click':
            self.script.append({'action':'click','selector':ev.get('selector'),'meta':{'tag':ev.get('tag'),'text':ev.get('text')},'ts':ev.get('ts')})
        elif action == 'type':
            # skip empty or password-like types
            val = ev.get('value','')
            if val is None:
                return
            self.script.append({'action':'type','selector':ev.get('selector'),'value':val,'ts':ev.get('ts')})
        elif action == 'scroll':
            self.script.append({'action':'scroll','x':ev.get('x',0),'y':ev.get('y',0),'ts':ev.get('ts')})
        elif action in ('dragstart','dragend'):
            self.script.append({'action':action,'selector':ev.get('selector'),'ts':ev.get('ts')})
        elif action == 'navigate':
            # we record navigation markers as helpful (but playback will re-navigate when navigate actions appear in script)
            self.script.append({'action':'navigate_marker','url':ev.get('url'),'ts':ev.get('ts')})
        else:
            # unknown - store raw
            self.script.append(ev)

    # manual script operations
    def get_script(self):
        with self._lock:
            return list(self.script)

    def clear(self):
        with self._lock:
            self.script = []

    def save(self, path):
        with self._lock:
            with open(path,"w",encoding="utf-8") as f:
                json.dump(self.script, f, indent=2, ensure_ascii=False)

    def load(self, path):
        with open(path,"r",encoding="utf-8") as f:
            data = json.load(f)
        with self._lock:
            self.script = data

    # helper UI actions
    def add_wait(self, seconds):
        with self._lock:
            self.script.append({'action':'wait','seconds': float(seconds), 'ts': int(time.time()*1000)})

    def add_screenshot(self, path=None):
        # take screenshot now and add action referencing file
        if not self.driver:
            return None
        if not path:
            # generate file in cwd with timestamp
            path = os.path.abspath(f"screenshot_{int(time.time())}.png")
        try:
            self.driver.save_screenshot(path)
            with self._lock:
                self.script.append({'action':'screenshot','path':path,'ts':int(time.time()*1000)})
            return path
        except Exception:
            return None

    def add_scroll(self, x=None, y=None):
        if x is None or y is None:
            try:
                x = self.driver.execute_script("return window.scrollX || 0;")
                y = self.driver.execute_script("return window.scrollY || 0;")
            except Exception:
                x,y = 0,0
        with self._lock:
            self.script.append({'action':'scroll','x':int(x),'y':int(y),'ts':int(time.time()*1000)})

    # Playback
    def _find_element(self, selector):
        # try css then xpath
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
                act = step.get('action')
                if act == 'click':
                    sel = step.get('selector')
                    el = self._find_element(sel) if sel else None
                    if el:
                        try:
                            el.click()
                        except Exception:
                            # fallback execute JS click
                            try:
                                self.driver.execute_script("arguments[0].click();", el)
                            except Exception:
                                pass
                elif act == 'type':
                    sel = step.get('selector')
                    val = step.get('value','')
                    el = self._find_element(sel) if sel else None
                    if el:
                        try:
                            el.clear()
                            el.send_keys(val)
                        except Exception:
                            pass
                elif act == 'navigate':
                    url = step.get('url')
                    if url:
                        self.driver.get(url)
                        time.sleep(0.8)
                        # re-inject after navigation
                        try:
                            self.inject()
                        except Exception:
                            pass
                elif act == 'wait':
                    secs = float(step.get('seconds', 1))
                    time.sleep(secs)
                elif act == 'screenshot':
                    p = step.get('path')
                    if p:
                        try:
                            self.driver.save_screenshot(p)
                        except Exception:
                            pass
                elif act == 'scroll':
                    x = int(step.get('x',0))
                    y = int(step.get('y',0))
                    try:
                        self.driver.execute_script("window.scrollTo(arguments[0], arguments[1]);", x, y)
                    except Exception:
                        pass
                elif act == 'dragstart' or act == 'dragend':
                    # best-effort: try to simulate drag by JS dispatch (may not work for complex apps)
                    sel = step.get('selector')
                    el = self._find_element(sel) if sel else None
                    if el:
                        try:
                            self.driver.execute_script("""
                                const el = arguments[0];
                                const ev = new DragEvent(arguments[1], {bubbles:true, cancelable:true});
                                el.dispatchEvent(ev);
                            """, el, 'dragstart' if act=='dragstart' else 'dragend')
                        except Exception:
                            pass
                # ignore navigate_marker
            except Exception:
                # continue on errors
                pass
            time.sleep(delay_between)
