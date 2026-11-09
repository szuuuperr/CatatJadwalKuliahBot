"""
Penyimpanan tugas di SQLite. Setiap tugas terikat ke chat_id pemiliknya,
sehingga satu bot bisa melayani banyak mahasiswa tanpa data tercampur.
"""
import sqlite3
from contextlib import contextmanager
from datetime import date

DB_PATH = "tugas.db"


@contextmanager
def koneksi(path=DB_PATH):
    """Buka database, commit jika sukses (rollback jika error), lalu tutup."""
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row  # baris bisa dibaca seperti dict: row["judul"]
    try:
        with con:  # transaksi: commit otomatis di akhir blok
            yield con
    finally:
        con.close()


def siapkan(path=DB_PATH):
    """Buat tabel jika belum ada."""
    with koneksi(path) as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS tugas (
                   id       INTEGER PRIMARY KEY AUTOINCREMENT,
                   chat_id  INTEGER NOT NULL,
                   judul    TEXT    NOT NULL,
                   deadline TEXT,              -- 'YYYY-MM-DD' atau NULL
                   selesai  INTEGER NOT NULL DEFAULT 0
               )"""
        )


def tambah(chat_id, judul, deadline=None, path=DB_PATH):
    """Simpan tugas baru, kembalikan id-nya."""
    with koneksi(path) as con:
        cur = con.execute(
            "INSERT INTO tugas (chat_id, judul, deadline) VALUES (?, ?, ?)",
            (chat_id, judul, deadline.isoformat() if deadline else None),
        )
        return cur.lastrowid


def daftar(chat_id, path=DB_PATH):
    """Tugas yang belum selesai milik chat_id, deadline terdekat di atas."""
    with koneksi(path) as con:
        rows = con.execute(
            """SELECT id, judul, deadline FROM tugas
               WHERE chat_id = ? AND selesai = 0
               ORDER BY deadline IS NULL, deadline, id""",
            (chat_id,),
        ).fetchall()
    return [
        {
            "id": r["id"],
            "judul": r["judul"],
            "deadline": date.fromisoformat(r["deadline"]) if r["deadline"] else None,
        }
        for r in rows
    ]


def tandai_selesai(chat_id, tugas_id, path=DB_PATH):
    """Tandai selesai. True jika berhasil, False jika tugas bukan milik chat_id."""
    with koneksi(path) as con:
        cur = con.execute(
            "UPDATE tugas SET selesai = 1 WHERE id = ? AND chat_id = ? AND selesai = 0",
            (tugas_id, chat_id),
        )
        return cur.rowcount == 1
