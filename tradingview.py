# tradingview.py  –  IDX edition  (15-minute volume-breakout)
import os, json, time
from playwright.sync_api import sync_playwright

TV_USER    = os.getenv("TV_USER")
TV_PASS    = os.getenv("TV_PASS")
EXCHANGE   = os.getenv("EXCHANGE") or "IDX"      # default to IDX

# ---------- helper ----------
def _new_page():
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(user_agent="Mozilla/5.0")
    # ----- login -----
    page.goto("https://www.tradingview.com/accounts/signin/")
    page.fill('[name="username"]', TV_USER)
    page.fill('[name="password"]', TV_PASS)
    page.click('button[type="submit"]')
    page.wait_for_url("https://www.tradingview.com/**", timeout=30000)
    return browser, page

# ---------- create ----------
def create_alert(ticker: str, webhook_url: str) -> str:
    browser, page = _new_page()
    # 1. open 15-minute chart of IDX:ticker
    page.goto(f"https://www.tradingview.com/symbols/{EXCHANGE}-{ticker}/?interval=15")
    page.wait_for_load_state("networkidle")

    # 2. add “Breakout Volume Alert” indicator
    page.click('[data-name="indicators"]')
    page.fill('[placeholder="Search"]', "Breakout Volume Alert")
    page.click('text=Breakout Volume Alert  ‑  MDSMARTTrader2022')   # exact match
    page.keyboard.press("Escape")

    # 3. open alert dialog
    page.click('[data-name="alerts"]')
    page.click('text=Create alert')

    # 4. fill condition (default ≥ 1.5× already selected by indicator)
    #    just ensure webhook + message
    page.fill('[placeholder="Message"]', json.dumps(
        {"ticker":"{{ticker}}","close":{{close}},"volume":{{volume}},"time":"{{time}}"}
    ))
    page.fill('[placeholder="Webhook URL"]', webhook_url)

    # 5. create
    page.click('button:has-text("Create")')
    time.sleep(2)

    # 6. scrape alert-id from URL
    alert_id = page.url.split("/")[-1] if "/" in page.url else "unknown"
    browser.close()
    return alert_id

# ---------- delete ----------
def delete_alert(alert_id: str):
    browser, page = _new_page()
    page.goto(f"https://www.tradingview.com/uql/?alert_id={alert_id}")
    page.click('button[title="Delete"]')
    page.click('button:has-text("Delete")')   # confirm
    browser.close()
