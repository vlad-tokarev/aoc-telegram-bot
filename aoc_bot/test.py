import json
from unittest.mock import patch

import pytest

import bot
import models
import reports

cfg = bot.Settings()

TEST_RESOURCES = "test_resources"

# Unit tests


def test_parse_aoc_json_response():
    with open("test_resources/board_2.json") as f:
        response = json.load(f)
    lb = bot.parse_aoc_json_response(response)
    assert lb is not None


@pytest.mark.parametrize("current_board_file,fetched_board_file,expected_report_file", [
    (None, "board_2.json", "board_2.json.report"),
    ("board_1.json", "board_2.json", "board_2-1.report"),
    ("board_2.json", "board_3.json", "board_3-2.report"),
])
def test_run_once(current_board_file, fetched_board_file, expected_report_file):

    current_board = None
    if current_board_file is not None:
        with open(f"{TEST_RESOURCES}/{current_board_file}") as f:
            current_board = models.LeaderBoard(**json.load(f))

    with open(f"{TEST_RESOURCES}/{fetched_board_file}") as f:
        fetched_board_json = json.load(f)

    with open(f"{TEST_RESOURCES}/{expected_report_file}") as f:
        expected_report = f.read()

    with patch("bot.aoc_fetch_api") as fetch_mock, patch("bot.send_telegram_message") as send_mock:
        fetch_mock.return_value = fetched_board_json
        local_cfg = models.Settings(telegram_chats=["1234"], telegram_token="21414a14")

        bot.run_once(local_cfg, current_board)

        for chat in local_cfg.telegram_chats:
            send_mock.assert_called_with(local_cfg.telegram_token, chat, expected_report)


@pytest.mark.parametrize("board_file,report_file", [
    ("board_1.json", "board_1.json.report"),
    ("board_2.json", "board_2.json.report"),
    ("board_3.json", "board_3.json.report"),
])
def test_text_leaderboard(board_file, report_file):
    with open(f"{TEST_RESOURCES}/{board_file}") as f:
        lb = models.LeaderBoard(**json.load(f))
    with open(f"{TEST_RESOURCES}/{report_file}") as f:
        report = f.read()
    assert report == reports.text_leaderboard(lb)


@pytest.mark.parametrize("board_file,board_file_new,report_file", [
    ("board_1.json", "board_2.json", "board_2-1.report"),
    ("board_2.json", "board_3.json", "board_3-2.report"),
])
def test_text_leaderboard(board_file, board_file_new, report_file):
    with open(f"{TEST_RESOURCES}/{board_file}") as f:
        lb = models.LeaderBoard(**json.load(f))
    with open(f"{TEST_RESOURCES}/{board_file_new}") as f:
        lb_new = models.LeaderBoard(**json.load(f))

    with open(f"{TEST_RESOURCES}/{report_file}") as f:
        report = f.read()
    assert report == reports.text_leaderboard_diff(lb_new-lb)


@pytest.mark.parametrize("board_file,report_file", [
    ("board_1.json", "board_1.json.report"),
    ("board_2.json", "board_2.json.report"),
    ("board_3.json", "board_3.json.report"),
])
def text_leaderboard_diff(board_file, report_file):
    with open(f"{TEST_RESOURCES}/{board_file}") as f:
        lb = models.LeaderBoard(**json.load(f))
    with open(f"{TEST_RESOURCES}/{report_file}") as f:
        report = f.read()
    assert report == reports.text_leaderboard(lb)


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

