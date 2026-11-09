# TugasBot — Praktikum Bot Telegram

## Menjalankan di VS Code

1. Simpan folder ini di lokasi lokal yang TIDAK tersinkron iCloud/OneDrive,
   misalnya `~/praktikum/bot-tugas` atau `C:\praktikum\bot-tugas`.
2. VS Code: File → Open Folder → pilih folder yang berisi `bot.py`.
3. Terminal → New Terminal, lalu:

   | Windows (PowerShell)            | macOS / Linux                   |
   |---------------------------------|---------------------------------|
   | `python -m venv venv`           | `python3 -m venv venv`          |
   | `venv\Scripts\activate`         | `source venv/bin/activate`      |
   | `pip install -r requirements.txt` | `pip install -r requirements.txt` |

4. Ctrl+Shift+P → Python: Select Interpreter → pilih `venv`.
5. Explorer → New File → `.env`, isi satu baris: `BOT_TOKEN=token_dari_botfather`
   (tanpa spasi, tanpa tanda kutip, jangan pakai Notepad).
6. Uji: `python -m pytest -v` → harus `35 passed`.
7. Jalankan: `python bot.py`, lalu kirim `/start` ke bot di Telegram. Berhenti: Ctrl+C.

Jangan pernah membagikan file `.env`.
