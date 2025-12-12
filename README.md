<h1>CTRL+ALT+TICKET – Selenium RPA Recorder and Player</h1>

<p>CTRL+ALT+TICKET is a Python Selenium-based recorder and player that captures browser interactions and replays them as automated workflows. It ships with a Tkinter GUI and a robust recording engine for clicks, typing, scrolling, drag-and-drop, navigation, waits and screenshots.</p>
<img width="1002" height="652" alt="image" src="https://github.com/user-attachments/assets/a30c3496-288d-4287-b743-64f9f0bc922a" />

<div class="section">
  <h2>Features</h2>
  <ul>
    <li>Launch isolated Chrome session per run (temporary profile)</li>
    <li>Record events: click, type, scroll, drag, navigate</li>
    <li>Manual actions: wait and screenshot</li>
    <li>Playback engine with element resolution and ActionChains drag support</li>
    <li>Script save/load (JSON)</li>
    <li>Listener diagnostics (Test Listener)</li>
    <li>Same-origin iframe support (uses top-level shared store)</li>
  </ul>
</div>

<div class="section">
  <h2>How It Works (brief)</h2>
  <p>When you start recording the tool injects a small JavaScript listener into the opened Chrome page (and same-origin frames when possible). The listener pushes events into a top-level array in the browser. A background Python thread polls this array and stores events in memory. Playback re-locates elements and executes recorded actions using Selenium.</p>
</div>

<div class="section">
 <h2>Packaging as a Desktop Application</h2>
  <p>You can distribute CTRL+ALT+TICKET as a single executable for Windows using PyInstaller (or similar packagers). Below are minimal packaging instructions.</p>

  <h3>Preparing</h3>
  <pre>pip install pyinstaller
pip install selenium webdriver-manager</pre>

  <h3>Build a single executable</h3>
  <pre>pyinstaller --onefile --add-data "path/to/chromedriver;." main.py</pre>
  <p>Notes:</p>
  <ul>
    <li>PyInstaller will bundle Python and your code into a single binary. Include any non-Python assets using <code>--add-data</code>.</li>
    <li>Chromedriver is obtained automatically at runtime by <code>webdriver-manager</code> — ensure network access on first run or bundle a tested chromedriver matching target Chrome.</li>
    <li>Test the built executable on a clean VM similar to end-user machines.</li>
  </ul>
  <h2>Applications (Testing & QA)</h2>
  <ul>
    <li><strong>Test evidence:</strong> Record exact user actions and screenshots to attach to bug reports.</li>
    <li><strong>Reproducible bugs:</strong> Replay tester scripts so developers can reproduce issues precisely.</li>
    <li><strong>Regression checks:</strong> Save failing-case scripts as repeatable regression tests.</li>
    <li><strong>UI smoke tests:</strong> Automate frequent flows (login, checkout, form submission) for quick verification.</li>
    <li><strong>Input tracking:</strong> Log typed values to identify which inputs cause validation or server errors.</li>
    <li><strong>Automation starter:</strong> Use recorded scripts as templates for building full Selenium test cases.</li>
    <li><strong>Onboarding & demos:</strong> Provide recorded flows for training or consistent product demonstrations.</li>
  </ul>
