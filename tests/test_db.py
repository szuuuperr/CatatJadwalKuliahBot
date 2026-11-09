from datetime import date

import pytest

import db


@pytest.fixture
def path(tmp_path):
    p = tmp_path / "uji.db"
    db.siapkan(p)
    return p


def test_tambah_dan_daftar(path):
    db.tambah(111, "Kuis", date(2026, 11, 4), path=path)
    hasil = db.daftar(111, path=path)
    assert len(hasil) == 1
    assert hasil[0]["judul"] == "Kuis"
    assert hasil[0]["deadline"] == date(2026, 11, 4)


def test_urutan_deadline_terdekat_dulu(path):
    db.tambah(111, "Tanpa deadline", None, path=path)
    db.tambah(111, "Jauh", date(2026, 12, 1), path=path)
    db.tambah(111, "Dekat", date(2026, 11, 5), path=path)
    judul = [t["judul"] for t in db.daftar(111, path=path)]
    assert judul == ["Dekat", "Jauh", "Tanpa deadline"]


def test_data_tiap_chat_terpisah(path):
    db.tambah(111, "Milik A", path=path)
    db.tambah(222, "Milik B", path=path)
    assert [t["judul"] for t in db.daftar(222, path=path)] == ["Milik B"]


def test_tandai_selesai(path):
    tid = db.tambah(111, "Kuis", path=path)
    assert db.tandai_selesai(111, tid, path=path) is True
    assert db.daftar(111, path=path) == []
    assert db.tandai_selesai(111, tid, path=path) is False  # sudah selesai


def test_tidak_bisa_menyelesaikan_tugas_orang_lain(path):
    tid = db.tambah(111, "Milik A", path=path)
    assert db.tandai_selesai(222, tid, path=path) is False
    assert len(db.daftar(111, path=path)) == 1
