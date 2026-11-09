"""Menguji handler bot tanpa internet: Update dan context diganti objek tiruan."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import bot
import db


@pytest.fixture
def path(tmp_path):
    p = tmp_path / "uji.db"
    db.siapkan(p)
    return p


def buat_update(teks="", chat_id=42):
    """Update tiruan berisi pesan; reply_text dicatat, tidak dikirim."""
    pesan = SimpleNamespace(text=teks, reply_text=AsyncMock())
    return SimpleNamespace(
        message=pesan,
        effective_message=pesan,
        effective_chat=SimpleNamespace(id=chat_id),
        effective_user=SimpleNamespace(first_name="Ani"),
    )


def buat_context(path, args=None):
    return SimpleNamespace(args=args or [], bot_data={"db": path},
                           job_queue=MagicMock())


def teks_balasan(update):
    return update.message.reply_text.call_args.args[0]


def test_start_menyapa_dengan_nama(path):
    upd = buat_update("/start")
    asyncio.run(bot.start(upd, buat_context(path)))
    assert "Halo, Ani!" in teks_balasan(upd)


def test_tambah_menyimpan_ke_db(path):
    upd = buat_update()
    ctx = buat_context(path, ["Kuis", "2026-11-04"])
    asyncio.run(bot.tambah(upd, ctx))
    assert teks_balasan(upd).startswith("Tercatat: Kuis")
    assert db.daftar(42, path=path)[0]["judul"] == "Kuis"


def test_tambah_tanpa_judul_memberi_contoh(path):
    upd = buat_update()
    asyncio.run(bot.tambah(upd, buat_context(path, [])))
    assert "Contoh" in teks_balasan(upd)
    assert db.daftar(42, path=path) == []


def test_daftar_memberi_tombol_per_tugas(path):
    db.tambah(42, "Kuis", path=path)
    db.tambah(42, "Laporan", path=path)
    upd = buat_update()
    asyncio.run(bot.daftar(upd, buat_context(path)))
    markup = upd.message.reply_text.call_args.kwargs["reply_markup"]
    data = [baris[0].callback_data for baris in markup.inline_keyboard]
    assert len(data) == 2 and all(d.startswith("selesai:") for d in data)


def test_tombol_selesai_mengubah_pesan(path):
    tid = db.tambah(42, "Kuis", path=path)
    query = SimpleNamespace(data=f"selesai:{tid}", answer=AsyncMock(),
                            edit_message_text=AsyncMock())
    upd = SimpleNamespace(callback_query=query, effective_chat=SimpleNamespace(id=42))
    asyncio.run(bot.tombol_selesai(upd, buat_context(path)))
    query.answer.assert_awaited_once()
    assert "ditandai selesai" in query.edit_message_text.call_args.args[0]
    assert db.daftar(42, path=path) == []


def test_ingatkan_menjadwalkan_job(path):
    upd = buat_update()
    ctx = buat_context(path, ["5", "kumpulkan", "laporan"])
    asyncio.run(bot.ingatkan(upd, ctx))
    kw = ctx.job_queue.run_once.call_args.kwargs
    assert kw["when"] == 300 and kw["chat_id"] == 42 and kw["data"] == "kumpulkan laporan"


def test_kirim_pengingat():
    kirim = AsyncMock()
    ctx = SimpleNamespace(job=SimpleNamespace(chat_id=42, data="minum air"),
                          bot=SimpleNamespace(send_message=kirim))
    asyncio.run(bot.kirim_pengingat(ctx))
    kirim.assert_awaited_once_with(42, "Pengingat: minum air")


def test_aplikasi_mendaftarkan_semua_handler(tmp_path):
    app = bot.buat_aplikasi("123:ABC", db_path=tmp_path / "uji.db")
    perintah = {c for h in app.handlers[0] for c in getattr(h, "commands", [])}
    assert {"start", "help", "tambah", "daftar", "ingatkan"} <= perintah
    assert app.job_queue is not None  # extra [job-queue] terpasang
