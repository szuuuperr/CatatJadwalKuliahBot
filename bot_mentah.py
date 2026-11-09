"""
Langkah 2: bot Telegram TANPA pustaka bot, hanya requests.

Tujuannya melihat apa yang sebenarnya terjadi di balik python-telegram-bot:
1. getMe        : cek token, tanyakan "siapa saya?"
2. getUpdates   : long polling, minta update baru ke server Telegram
3. sendMessage  : kirim balasan ke chat_id pengirim
4. offset       : tandai update yang sudah diproses agar tidak dikirim ulang

Jalankan:  python bot_mentah.py   (hentikan dengan Ctrl+C)
"""
import os

import requests
from dotenv import load_dotenv

API = "https://api.telegram.org/bot{token}/{method}"


def api_url(token, method):
    """Bentuk URL Bot API: https://api.telegram.org/bot<TOKEN>/<method>."""
    return API.format(token=token, method=method)


def panggil(token, method, **params):
    """Panggil satu method Bot API dan kembalikan isi 'result'.

    Setiap jawaban Bot API berbentuk JSON: {"ok": true, "result": ...}
    atau {"ok": false, "error_code": 401, "description": "Unauthorized"}.
    """
    # timeout HTTP harus lebih lama dari timeout long polling
    batas = params.get("timeout", 0) + 10
    resp = requests.post(api_url(token, method), json=params, timeout=batas)
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"{method} gagal: {data.get('error_code')} {data.get('description')}")
    return data["result"]


def buat_balasan(teks):
    """Logika bot: dari teks masuk, tentukan teks balasan."""
    if teks == "/start":
        return "Halo! Aku bot mentah. Kirim pesan apa saja, akan kubalas."
    return f"Kamu menulis: {teks}"


def proses_update(update):
    """Ambil (chat_id, balasan) dari satu update. None jika bukan pesan teks."""
    pesan = update.get("message")
    if not pesan or "text" not in pesan:
        return None  # misalnya stiker, foto, atau pesan yang diedit
    return pesan["chat"]["id"], buat_balasan(pesan["text"])


def main():
    load_dotenv()
    token = os.environ["BOT_TOKEN"]

    saya = panggil(token, "getMe")
    print(f"Terhubung sebagai @{saya['username']} (id {saya['id']})")

    offset = None
    while True:
        # Long polling: server menahan request sampai 30 detik
        # dan langsung menjawab begitu ada pesan baru.
        updates = panggil(token, "getUpdates", offset=offset, timeout=30)
        for upd in updates:
            print("update masuk:", upd)
            hasil = proses_update(upd)
            if hasil:
                chat_id, balasan = hasil
                panggil(token, "sendMessage", chat_id=chat_id, text=balasan)
            # update_id + 1 = "yang ini sudah saya proses, jangan kirim lagi"
            offset = upd["update_id"] + 1


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot berhenti.")
