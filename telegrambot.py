import os, re, requests, sqlite3, json
from telebot import TeleBot
from tradingview import create_alert, delete_alert

TOKEN   = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEBHOOK = os.getenv("WEBHOOK_ROOT") + "/webhook"

bot = TeleBot(TOKEN)

def db():
    conn = sqlite3.connect("alerts.db", check_same_thread=False)
    conn.execute("""CREATE TABLE IF NOT EXISTS alerts(
                     ticker TEXT PRIMARY KEY,
                     alert_id TEXT UNIQUE)""")
    return conn

@bot.message_handler(commands=["start","help"])
def help_(m):
    bot.reply_to(m, "15m volume-breakout bot\n"
                    "/add TICKER TICKER …  – start tracking\n"
                    "/remove TICKER        – stop\n"
                    "/list                 – show active\n"
                    "/wipe                 – stop all")

@bot.message_handler(commands=["add"])
def add(m):
    tickers = re.findall(r"[A-Z0-9]+", m.text.upper())
    if not tickers:
        bot.reply_to(m, "❌  give at least one ticker  e.g.  /add BTCUSDT")
        return
    conn = db()
    added, skipped = [], []
    for t in tickers:
        if conn.execute("SELECT 1 FROM alerts WHERE ticker=?", (t,)).fetchone():
            skipped.append(t); continue
        try:
            aid = create_alert(t, WEBHOOK)   # 15m hard-coded inside
            conn.execute("INSERT INTO alerts(ticker,alert_id) VALUES (?,?)", (t, aid))
            added.append(t)
        except Exception as e:
            bot.reply_to(m, f"⚠️  {t}  fail: {e}")
    conn.commit(); conn.close()
    bot.reply_to(m, f"✅ added: {added}\n🟡 skipped: {skipped}")

@bot.message_handler(commands=["remove"])
def rem(m):
    t = m.text.split()[1].upper() if len(m.text.split())==2 else None
    if not t: bot.reply_to(m, "❌  /remove TICKER"); return
    conn = db()
    row = conn.execute("SELECT alert_id FROM alerts WHERE ticker=?", (t,)).fetchone()
    if not row:
        bot.reply_to(m, f"❌  {t} not tracked")
    else:
        delete_alert(row[0])
        conn.execute("DELETE FROM alerts WHERE ticker=?", (t,))
        conn.commit()
        bot.reply_to(m, f"✅  {t} removed")
    conn.close()

@bot.message_handler(commands=["list"])
def lst(m):
    conn = db()
    rows = [r[0] for r in conn.execute("SELECT ticker FROM alerts").fetchall()]
    conn.close()
    bot.reply_to(m, "📋 tracking:\n" + "\n".join(rows) if rows else "📋 nothing")

@bot.message_handler(commands=["wipe"])
def wipe(m):
    conn = db()
    for (aid,) in conn.execute("SELECT alert_id FROM alerts").fetchall():
        delete_alert(aid)
    conn.execute("DELETE FROM alerts")
    conn.commit(); conn.close()
    bot.reply_to(m, "🗑️  all alerts deleted")

def poll():
    print("Telegram bot polling…")
    bot.infinity_polling()
