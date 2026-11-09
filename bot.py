"""
TugasBot: asisten pencatat dan pengingat tugas kuliah di Telegram.

Perintah:
  /start                         sapaan + keyboard menu
  /help                          daftar perintah
  /tambah <judul> [YYYY-MM-DD]   catat tugas baru
  /daftar                        lihat tugas + tombol "selesai"
  /ingatkan <menit> <pesan>      pengingat sekali jalan

Jalankan:  python bot.py   (hentikan dengan Ctrl+C)
"""
import logging
import os

from dotenv import load_dotenv
from telegram import (BotCommand, InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, Update)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

import db
import logika

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)  # sembunyikan log tiap request
log = logging.getLogger("tugasbot")

BANTUAN = (
    "Perintah yang tersedia:\n"
    "/tambah <judul> [YYYY-MM-DD] - catat tugas\n"
    "/daftar - lihat tugas yang belum selesai\n"
    "/ingatkan <menit> <pesan> - pengingat\n"
    "/help - bantuan ini"
)


# ---------- Langkah 3: handler pertama ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nama = update.effective_user.first_name
    keyboard = ReplyKeyboardMarkup([["/daftar", "/help"]], resize_keyboard=True)
    await update.message.reply_text(
        f"Halo, {nama}! Aku TugasBot.\n"
        "Aku bisa mencatat tugas kuliah dan mengingatkanmu.\n\n" + BANTUAN,
        reply_markup=keyboard,
    )


async def bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(BANTUAN)


async def teks_biasa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pesan teks yang bukan perintah."""
    await update.message.reply_text(
        f'Aku menerima: "{update.message.text}".\nKetik /help untuk melihat perintah.'
    )


# ---------- Langkah 4: perintah dengan argumen + database ----------
async def tambah(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        judul, deadline = logika.parse_tambah(context.args)
    except ValueError as e:
        await update.message.reply_text(f"{e}\nContoh: /tambah Laporan P16 2026-11-10")
        return
    chat_id = update.effective_chat.id
    db.tambah(chat_id, judul, deadline, path=context.bot_data["db"])
    log.info("chat %s menambah tugas: %s", chat_id, judul)
    await update.message.reply_text(
        f"Tercatat: {judul} — {logika.label_deadline(deadline)}"
    )


# ---------- Langkah 5: inline keyboard dan callback query ----------
def keyboard_selesai(tugas):
    """Satu tombol per tugas. callback_data dikirim balik saat tombol ditekan."""
    tombol = [
        [InlineKeyboardButton(f"Selesai: {i}. {t['judul'][:30]}",
                              callback_data=f"selesai:{t['id']}")]
        for i, t in enumerate(tugas, start=1)
    ]
    return InlineKeyboardMarkup(tombol) if tombol else None


async def daftar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tugas = db.daftar(update.effective_chat.id, path=context.bot_data["db"])
    await update.message.reply_text(
        logika.format_daftar(tugas), reply_markup=keyboard_selesai(tugas)
    )


async def tombol_selesai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # wajib: menghentikan ikon jam pada tombol
    tugas_id = int(query.data.split(":")[1])
    chat_id = update.effective_chat.id
    ok = db.tandai_selesai(chat_id, tugas_id, path=context.bot_data["db"])
    tugas = db.daftar(chat_id, path=context.bot_data["db"])
    awal = "Tugas ditandai selesai.\n\n" if ok else "Tugas sudah selesai sebelumnya.\n\n"
    await query.edit_message_text(
        awal + logika.format_daftar(tugas), reply_markup=keyboard_selesai(tugas)
    )


# ---------- Langkah 6: JobQueue untuk pengingat ----------
async def kirim_pengingat(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(job.chat_id, f"Pengingat: {job.data}")


async def ingatkan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        menit, pesan = logika.parse_ingatkan(context.args)
    except ValueError as e:
        await update.message.reply_text(str(e))
        return
    context.job_queue.run_once(
        kirim_pengingat,
        when=menit * 60,  # detik
        chat_id=update.effective_chat.id,
        data=pesan,
        name=f"ingat-{update.effective_chat.id}",
    )
    await update.message.reply_text(f"Oke, aku ingatkan {menit} menit lagi.")


# ---------- Langkah 7: perintah tak dikenal dan penanganan error ----------
async def tak_dikenal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Perintah tidak dikenal. Ketik /help.")


async def saat_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Error saat memproses update", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("Maaf, terjadi kesalahan. Coba lagi.")


async def setelah_mulai(app: Application):
    """Dijalankan sekali saat bot menyala: isi menu perintah di aplikasi Telegram."""
    await app.bot.set_my_commands([
        BotCommand("tambah", "Catat tugas baru"),
        BotCommand("daftar", "Lihat tugas"),
        BotCommand("ingatkan", "Pengingat dalam N menit"),
        BotCommand("help", "Bantuan"),
    ])


def buat_aplikasi(token, db_path=db.DB_PATH):
    """Rakit Application beserta semua handler (dipisah agar bisa diuji)."""
    app = Application.builder().token(token).post_init(setelah_mulai).build()
    app.bot_data["db"] = db_path
    db.siapkan(db_path)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", bantuan))
    app.add_handler(CommandHandler("tambah", tambah))
    app.add_handler(CommandHandler("daftar", daftar))
    app.add_handler(CommandHandler("ingatkan", ingatkan))
    app.add_handler(CallbackQueryHandler(tombol_selesai, pattern=r"^selesai:\d+$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, teks_biasa))
    app.add_handler(MessageHandler(filters.COMMAND, tak_dikenal))  # paling akhir
    app.add_error_handler(saat_error)
    return app


def main():
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise SystemExit("BOT_TOKEN belum diisi. Salin .env.example menjadi .env lalu isi tokennya.")
    app = buat_aplikasi(token)
    log.info("Bot berjalan. Tekan Ctrl+C untuk berhenti.")
    # Hanya minta jenis update yang kita tangani. Tanpa ini, pesan yang DIEDIT
    # juga masuk ke CommandHandler/MessageHandler dengan update.message = None.
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
