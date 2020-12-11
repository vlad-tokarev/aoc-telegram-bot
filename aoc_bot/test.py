import json

import pytest

import bot
import models

cfg = bot.Settings()


# Unit tests functions

def test_parse_aoc_json_response():
    with open("test_resources/board_2.json") as f:
        response = json.load(f)
    lb = bot.parse_aoc_json_response(response)
    assert lb is not None


# Unit tests models


class TestLeaderBoard:
    def test_str(self):
        with open("test_resources/board_1.json") as f:
            response = json.load(f)
        lb = bot.LeaderBoard(**response)
        with open("test_resources/board_1.json.report", "r") as f:
            expected = f.read()

        assert expected == str(lb)

    def test_str_2(self):
        with open("test_resources/board_2.json") as f:
            response = json.load(f)
        lb = bot.LeaderBoard(**response)
        with open("test_resources/board_2.json.report", "r") as f:
            expected = f.read()

        assert expected == str(lb)

    def test_str_board_3(self):
        with open("test_resources/board_3.json") as f:
            response = json.load(f)
        lb = bot.LeaderBoard(**response)
        with open("test_resources/board_3.json.report", "r") as f:
            expected = f.read()

        assert expected == str(lb)

    def test_sub(self):
        with open("test_resources/board_1.json") as f, \
                open("test_resources/board_2.json") as f2:
            lb = bot.LeaderBoard(**json.load(f))
            lb_changed = bot.LeaderBoard(**json.load(f2))

        diff = lb_changed - lb
        with open("test_resources/board_2-1.report") as f:
            report = f.read()

        assert report == str(diff)

    def test_sub2(self):
        with open("test_resources/board_2.json") as f, \
                open("test_resources/board_3.json") as f2:
            lb = bot.LeaderBoard(**json.load(f))
            lb_changed = bot.LeaderBoard(**json.load(f2))

        diff = lb_changed - lb
        with open("test_resources/board_3-2.report") as f:
            report = f.read()

        assert report == str(diff)

    @pytest.mark.skipif(not cfg.telegram_token,
                        reason=f"{models.ENV_PREFIX}telegram_token secret is required for this test")
    @pytest.mark.skipif(not cfg.telegram_chats,
                        reason=f"{models.ENV_PREFIX}telegram_chats ENV is required for this test")
    def test_sub_telegram(self):
        with open("test_resources/board_1.json") as f, \
                open("test_resources/board_2.json") as f2:
            lb = bot.LeaderBoard(**json.load(f))
            lb_changed = bot.LeaderBoard(**json.load(f2))

        diff = lb_changed - lb
        bot.notify_telegram_chats(cfg.telegram_token, cfg.telegram_chats, str(diff))

    def test_eq(self):
        with open("test_resources/board_1.json") as f, \
                open("test_resources/board_1.json") as f2:
            lb = bot.LeaderBoard(**json.load(f))
            lb2 = bot.LeaderBoard(**json.load(f2))

        assert lb == lb2

        with open("test_resources/board_1.json") as f, \
                open("test_resources/board_2.json") as f2:
            lb = bot.LeaderBoard(**json.load(f))
            lb2 = bot.LeaderBoard(**json.load(f2))

        assert lb != lb2


# Integration tests
# To run these tests a minimal configuration is required

@pytest.mark.skipif(not cfg.aoc_leader_board_url,
                    reason=f"{models.ENV_PREFIX}aoc_leader_board_url ENV is required for this test")
@pytest.mark.skipif(not cfg.aoc_session_id,
                    reason=f"{models.ENV_PREFIX}aoc_session_id secret is required for this test")
def test_aoc_fetch_api():

    d = bot.aoc_fetch_api(cfg.aoc_session_id, cfg.aoc_leader_board_url)
    assert isinstance(d, dict)


@pytest.mark.skipif(not cfg.telegram_token,
                    reason=f"{models.ENV_PREFIX}telegram_token secret is required for this test")
@pytest.mark.skipif(not cfg.telegram_chats,
                    reason=f"{models.ENV_PREFIX}telegram_chats ENV is required for this test")
def test_send_telegram_message():
    for chat_id in cfg.telegram_chats:
        bot.send_telegram_message(cfg.telegram_token, chat_id, "Test")


@pytest.mark.skipif(not cfg.telegram_token,
                    reason=f"{models.ENV_PREFIX}telegram_token secret is required for this test")
@pytest.mark.skipif(not cfg.telegram_chats,
                    reason=f"{models.ENV_PREFIX}telegram_chats ENV is required for this test")
def test_notify_telegram_chats():
    with open("test_resources/board_1.json") as f, \
            open("test_resources/board_2.json") as f2:
        lb = bot.LeaderBoard(**json.load(f))
        lb_changed = bot.LeaderBoard(**json.load(f2))

    diff = lb_changed - lb
    bot.notify_telegram_chats(cfg.telegram_token, cfg.telegram_chats, str(lb))
    bot.notify_telegram_chats(cfg.telegram_token, cfg.telegram_chats, str(lb_changed))
    bot.notify_telegram_chats(cfg.telegram_token, cfg.telegram_chats, str(diff))
