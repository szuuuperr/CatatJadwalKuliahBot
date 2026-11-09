import pytest

import bot_mentah


def test_api_url():
    assert bot_mentah.api_url("ABC", "getMe") == "https://api.telegram.org/botABC/getMe"


def test_proses_update_pesan_teks():
    update = {
        "update_id": 5001,
        "message": {
            "message_id": 1,
            "from": {"id": 42, "first_name": "Ani"},
            "chat": {"id": 42, "type": "private"},
            "date": 1762200000,
            "text": "halo",
        },
    }
    assert bot_mentah.proses_update(update) == (42, "Kamu menulis: halo")


def test_proses_update_start():
    update = {"update_id": 1, "message": {"chat": {"id": 7}, "text": "/start"}}
    chat_id, balasan = bot_mentah.proses_update(update)
    assert chat_id == 7 and balasan.startswith("Halo")


def test_proses_update_bukan_teks():
    stiker = {"update_id": 2, "message": {"chat": {"id": 7}, "sticker": {}}}
    assert bot_mentah.proses_update(stiker) is None
    assert bot_mentah.proses_update({"update_id": 3, "edited_message": {}}) is None


class JawabanPalsu:
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def test_panggil_mengembalikan_result(monkeypatch):
    def post_palsu(url, json, timeout):
        assert url.endswith("/getMe")
        return JawabanPalsu({"ok": True, "result": {"id": 1, "username": "uji_bot"}})

    monkeypatch.setattr(bot_mentah.requests, "post", post_palsu)
    assert bot_mentah.panggil("T", "getMe")["username"] == "uji_bot"


def test_panggil_token_salah(monkeypatch):
    monkeypatch.setattr(
        bot_mentah.requests, "post",
        lambda url, json, timeout: JawabanPalsu(
            {"ok": False, "error_code": 401, "description": "Unauthorized"}),
    )
    with pytest.raises(RuntimeError, match="401"):
        bot_mentah.panggil("salah", "getMe")
