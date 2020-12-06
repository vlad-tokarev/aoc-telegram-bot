import logging
import os
from dataclasses import dataclass
from time import sleep
from typing import Dict, List, Union

import pydantic
import requests
from pydantic import ValidationError
import telegram

from models import LeaderBoard, Settings

logging.basicConfig(format='[%(levelname)8s] %(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


@dataclass
class AOCFetchAPIError(Exception):
    http_status_code: int


def aoc_fetch_api(session_id: str, board_url: pydantic.AnyHttpUrl) -> Dict:
    if not board_url.endswith(".json"):
        board_url = board_url + ".json"

    resp = requests.get(board_url, cookies={"session": session_id})
    if resp.status_code == 200:
        return resp.json()
    else:
        raise AOCFetchAPIError(http_status_code=resp.status_code)


def parse_aoc_json_response(resp_body: Dict) -> LeaderBoard:
    return LeaderBoard(**resp_body)


def send_telegram_message(token: str, chat_id: str, text: str):
    bot = telegram.bot.Bot(token=token)
    logger.warning(f"telegram message is prepared:\n{text}")
    text = text.replace("(", r"\(").replace(")", r"\)").replace("-", r"\-")
    bot.send_message(chat_id, text=f"`{text}`", parse_mode=telegram.ParseMode.MARKDOWN_V2)
    logger.info("telegram message was sent")


def notify_telegram_chats(token: str, chat_ids: List[str], text: str):
    for chat_id in chat_ids:
        try:
            send_telegram_message(token, chat_id, text)
        except Exception:
            logger.exception(f"Unable to send message to {chat_id=}")


def run_once(conf: Settings, previous_board: LeaderBoard) -> LeaderBoard:
    """
    Notify telegram chats about changes in AoC leader_board
    :param conf: Configuration
    :param previous_board: Leader board to compare with current and detect changes
           If None then compare step will be skipped but current leader board
           will be returned
    :return: Current LeaderBoard. Can be memorized to pass for next call and compare with a new one
    """

    api_result = aoc_fetch_api(conf.aoc_session_id, conf.aoc_leader_board_url)

    logger.info("Data successfully fetched from AoC")

    leader_board = parse_aoc_json_response(api_result)

    logger.info("JSON was parsed to leader board")

    if previous_board is None:
        logger.info("Previous leader board is None. Send current board without comparison")
        notify_telegram_chats(conf.telegram_token, conf.telegram_chats, str(leader_board))
        return leader_board

    if leader_board == previous_board:
        logger.info("Leader board is not changed")
        return leader_board

    lb_diff = leader_board - previous_board

    logger.info("Diff was calculated")

    notify_telegram_chats(conf.telegram_token, conf.telegram_chats, str(lb_diff))

    return leader_board


def run_forever():

    logger.info(f"Current pid={os.getpid()}")

    cached_leader_board: Union[LeaderBoard, None] = None
    config = Settings()

    sleep_interval = config.interval

    while True:
        try:
            cached_leader_board = run_once(config, cached_leader_board)

        except AOCFetchAPIError as e:
            logger.warning(f"Unable to fetch data from AoC API. {e.http_status_code=}")
            sleep_interval *= 2
        except ValidationError as e:
            logger.warning(f"Unable validate response json. {e.json()}")
            sleep_interval *= 2
        except Exception:
            logger.exception("Unhandled exception")
            sleep_interval *= 2
        else:
            sleep_interval = config.interval

        logger.info(f"Sleep for {sleep_interval}")
        sleep(sleep_interval)


if __name__ == '__main__':
    run_forever()
