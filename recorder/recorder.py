from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time, json

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

JS_FLUSH = "return window.__EVTS.splice(0, window.__EVTS.length);"

print("Launching browser...")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://www.w3schools.com/html/html_forms.asp")

time.sleep(1)
driver.execute_script(JS_LISTENER)
print("Listener injected.")

print("\nTry clicking or typing in the browser window...")
print("Collecting events for 10 seconds...\n")

for _ in range(20):
    time.sleep(0.5)
    evts = driver.execute_script(JS_FLUSH)
    if evts:
        print("Captured:", json.dumps(evts, indent=2))

driver.quit()

print("\nDone.")
