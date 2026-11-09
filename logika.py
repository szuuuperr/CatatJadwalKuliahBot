"""
Logika murni TugasBot: tidak ada Telegram dan tidak ada database di sini.

Semua fungsi menerima nilai biasa dan mengembalikan nilai biasa,
sehingga mudah diuji dengan pytest tanpa internet.
"""
from datetime import date

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def parse_tambah(args):
    """Pecah argumen /tambah menjadi (judul, deadline).

    /tambah Laporan P16 2026-11-10  -> ("Laporan P16", date(2026, 11, 10))
    /tambah Baca bab 3              -> ("Baca bab 3", None)
    """
    if not args:
        raise ValueError("Judul tugas tidak boleh kosong.")
    deadline = None
    try:
        deadline = date.fromisoformat(args[-1])
        args = args[:-1]
    except ValueError:
        pass  # kata terakhir bukan tanggal, berarti bagian dari judul
    judul = " ".join(args).strip()
    if not judul:
        raise ValueError("Judul tugas tidak boleh kosong.")
    return judul, deadline


def sisa_hari(deadline, hari_ini=None):
    """Selisih hari dari hari_ini ke deadline (negatif = terlambat)."""
    hari_ini = hari_ini or date.today()
    return (deadline - hari_ini).days


def label_deadline(deadline, hari_ini=None):
    """Teks ramah untuk deadline: 'hari ini', 'besok', 'lewat 2 hari', dst."""
    if deadline is None:
        return "tanpa deadline"
    n = sisa_hari(deadline, hari_ini)
    if n < 0:
        return f"lewat {-n} hari"
    if n == 0:
        return "hari ini"
    if n == 1:
        return "besok"
    return f"{n} hari lagi ({HARI[deadline.weekday()]}, {deadline:%d-%m-%Y})"


def format_daftar(tugas, hari_ini=None):
    """Ubah list tugas menjadi satu pesan teks bernomor.

    tugas: list of dict {"id", "judul", "deadline"} (deadline: date atau None)
    """
    if not tugas:
        return "Belum ada tugas. Tambahkan dengan /tambah <judul> [YYYY-MM-DD]"
    baris = ["Daftar tugasmu:"]
    for i, t in enumerate(tugas, start=1):
        baris.append(f"{i}. {t['judul']} — {label_deadline(t['deadline'], hari_ini)}")
    return "\n".join(baris)


def parse_ingatkan(args):
    """Pecah argumen /ingatkan menjadi (menit, pesan).

    /ingatkan 10 kumpulkan laporan -> (10, "kumpulkan laporan")
    """
    if len(args) < 2:
        raise ValueError("Format: /ingatkan <menit> <pesan>")
    try:
        menit = int(args[0])
    except ValueError:
        raise ValueError("Menit harus berupa angka, contoh: /ingatkan 10 minum air")
    if not 1 <= menit <= 1440:
        raise ValueError("Menit harus antara 1 dan 1440 (24 jam).")
    return menit, " ".join(args[1:])
