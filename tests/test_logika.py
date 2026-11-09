from datetime import date

import pytest

import logika

HARI_INI = date(2026, 11, 3)  # Selasa


def test_parse_tambah_dengan_deadline():
    judul, dl = logika.parse_tambah(["Laporan", "P16", "2026-11-10"])
    assert judul == "Laporan P16"
    assert dl == date(2026, 11, 10)


def test_parse_tambah_tanpa_deadline():
    assert logika.parse_tambah(["Baca", "bab", "3"]) == ("Baca bab 3", None)


@pytest.mark.parametrize("args", [[], ["2026-11-10"]])
def test_parse_tambah_judul_kosong(args):
    with pytest.raises(ValueError):
        logika.parse_tambah(args)


@pytest.mark.parametrize("deadline, harapan", [
    (date(2026, 11, 1), "lewat 2 hari"),
    (date(2026, 11, 3), "hari ini"),
    (date(2026, 11, 4), "besok"),
    (date(2026, 11, 10), "7 hari lagi (Selasa, 10-11-2026)"),
    (None, "tanpa deadline"),
])
def test_label_deadline(deadline, harapan):
    assert logika.label_deadline(deadline, HARI_INI) == harapan


def test_format_daftar_kosong():
    assert "Belum ada tugas" in logika.format_daftar([])


def test_format_daftar_bernomor():
    tugas = [
        {"id": 7, "judul": "Kuis", "deadline": date(2026, 11, 4)},
        {"id": 9, "judul": "Baca", "deadline": None},
    ]
    teks = logika.format_daftar(tugas, HARI_INI)
    assert teks.splitlines() == [
        "Daftar tugasmu:",
        "1. Kuis — besok",
        "2. Baca — tanpa deadline",
    ]


def test_parse_ingatkan_valid():
    assert logika.parse_ingatkan(["10", "minum", "air"]) == (10, "minum air")


@pytest.mark.parametrize("args", [["10"], ["sepuluh", "x"], ["0", "x"], ["2000", "x"]])
def test_parse_ingatkan_tidak_valid(args):
    with pytest.raises(ValueError):
        logika.parse_ingatkan(args)
