<h1>CTRL+ALT+TICKET – Selenium RPA Recorder and Player</h1>

<p>CTRL+ALT+TICKET is a Python Selenium-based recorder and player that captures browser interactions and replays them as automated workflows. It ships with a Tkinter GUI and a robust recording engine for clicks, typing, scrolling, drag-and-drop, navigation, waits and screenshots.</p>

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
  <h2>Applications</h2>

  <h3>Common practical uses</h3>
  <ul>
    <li><strong>Ticket booking automation</strong> — automate searching availability, choosing seats, and pre-filling user details up to the payment page (user completes payment manually).</li>
    <li><strong>Shopping workflow automation</strong> — apply filters, select variants, place items in cart, and open the checkout page pre-filled for manual confirmation.</li>
    <li><strong>Form filling & data entry</strong> — fill long or repetitive web forms from CSV/Excel source data (extend script to read input data).</li>
    <li><strong>Regression and UI smoke tests</strong> — record critical user flows and replay them as lightweight functional tests across builds.</li>
    <li><strong>Monitoring & availability checks</strong> — run periodic checks that navigate, log in, and verify critical elements are present.</li>
    <li><strong>Bulk / repetitive operations</strong> — automation for administrative web tasks (dashboard updates, report downloads).</li>
  </ul>
