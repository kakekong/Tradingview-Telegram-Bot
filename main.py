import threading, signal, sys
from server import app       # webhook receiver
from telegrambot import poll # command handler & alert creator

if __name__ == "__main__":
    # 1. webhook server in thread
    t1 = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000, debug=False), daemon=True)
    t1.start()
    # 2. telegram polling (blocking)
    poll()
