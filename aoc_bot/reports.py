import pytz
from tabulate import tabulate

import models


def text_leaderboard(lb: models.LeaderBoard) -> str:

    headers = ["pos", "score", "user"]

    tbl = []
    for mp in lb.positioned_members.values():
        line = [
            f"{str(mp.position):2} ",
            f"{str(mp.member.local_score):4} ",
            mp.member.username[:18]
        ]
        tbl.append(line)

    return tabulate(tbl, headers=headers)


def text_leaderboard_diff(lb_diff: models.LeaderBoardDiff) -> str:

    date_format = "%H:%M:%S"
    local = pytz.timezone("Europe/Moscow")

    report = "Changes in leaderboard!\n"

    headers = ["pos", "score", "user"]
    tbl = []
    for mp in lb_diff.members:
        pch = f"{mp.pos_change:>+3}" if mp.pos_change else f"{'0':>3}"
        lch = f"{mp.score_change:>+3}" if mp.score_change else f"{'0':>3}"
        line = [
            f"{str(mp.position):2} {pch}",
            f"{str(mp.member.local_score):4} {lch}",
            mp.member.username[:18]
        ]
        tbl.append(line)

    report += tabulate(tbl, headers=headers) + "\n--\n"

    solution_rows = []
    for m in lb_diff.members:
        if m.new_solutions:
            prefix = f"{m.member.username} solved "
            content = ", ".join(
                [f"d{s.day}_t{s.task} at {s.when.replace(tzinfo=pytz.utc).astimezone(local).strftime(date_format)}"
                 for s in m.new_solutions]
            )
            row = prefix + content
            solution_rows.append(row)

    report += "\n".join(solution_rows)

    return report
