import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pydantic
from tabulate import tabulate

SECRETS_DIR = os.environ.get("SECRETS_DIR", '/run/secrets')
ENV_PREFIX = 'aoc_bot__'


class Settings(pydantic.BaseSettings):
    aoc_session_id: str = ""
    aoc_leader_board_url: Optional[pydantic.AnyHttpUrl]
    telegram_token: str = ""
    telegram_chats: List[str] = []
    interval: int = 15 * 60

    class Config:
        env_prefix = ENV_PREFIX
        secrets_dir = SECRETS_DIR


class StarInfo(pydantic.BaseModel):
    get_star_ts: datetime


class StarsInfo(pydantic.BaseModel):
    silver: StarInfo = pydantic.Field(alias='1', default=None)
    gold: StarInfo = pydantic.Field(alias='2', default=None)


class Member(pydantic.BaseModel):
    stars: int
    local_score: int
    name: Optional[str]
    id: str
    last_star_ts: datetime
    global_score: int
    completion_day_level: Dict[pydantic.PositiveInt, StarsInfo]

    @property
    def username(self):
        return str(self.name) if self.name else f"anon {self.id}"

    def __str__(self):
        return f"{self.local_score=}  {self.username=}"


class MemberWithPosition(pydantic.BaseModel):
    member: Member
    position: int

    def __str__(self):
        return f"{self.position=}, {self.member.local_score=}, {self.member.username=}"


class Solution(pydantic.BaseModel):
    when: datetime
    day: int
    task: int


class MemberProgress(pydantic.BaseModel):

    def __str__(self):
        return f"{self.position=} {self.pos_change=} {self.member.username=} {self.member.local_score=} {self.new=}"

    member: Member
    position: int
    pos_change: int
    score_change: int
    new: bool
    new_solutions: List[Solution] = pydantic.Field(default_factory=list)


class LeaderBoardDiff(pydantic.BaseModel):
    members: List[MemberProgress]

    def __str__(self):

        date_format = "%H:%M:%S"

        report = "Changes in leaderboard!\n"

        headers = ["pos", "score", "user"]
        tbl = []
        for mp in self.members:
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
        for m in self.members:
            if m.new_solutions:
                prefix = f"{m.member.username} solved "
                content = ", ".join([f"d{s.day}_t{s.task} at {s.when.strftime(date_format)}" for s in m.new_solutions])
                row = prefix + content
                solution_rows.append(row)

        report += "\n".join(solution_rows)

        return report






def calc_member_new_solved(member_new: Member, member_old: Member) -> List[Solution]:

    new_solutions: List[Solution] = []
    for day, stars in member_new.completion_day_level.items():
        if day not in member_old.completion_day_level:
            if stars.silver:
                s = Solution(
                    day=day,
                    task=1,
                    when=stars.silver.get_star_ts
                )
                new_solutions.append(s)
            if stars.gold:
                s = Solution(
                    day=day,
                    task=2,
                    when=stars.gold.get_star_ts
                )
                new_solutions.append(s)
        else:
            old_stars = member_old.completion_day_level[day]

            if stars.silver and not old_stars.silver:
                s = Solution(
                    day=1,
                    task=1,
                    when=stars.silver.get_star_ts
                )
                new_solutions.append(s)

            if stars.gold and not old_stars.gold:
                s = Solution(
                    day=day,
                    task=2,
                    when=stars.gold.get_star_ts
                )
                new_solutions.append(s)
    return new_solutions


class LeaderBoard(pydantic.BaseModel):
    members: Dict[str, Member]

    def sorted_members(self) -> Dict[str, MemberWithPosition]:
        def sort(m: Tuple[str, Member]):
            # We use username to stable sort
            return m[1].local_score, m[1].last_star_ts
        sorted_members: Dict[str, Member] = {k: v for k, v in sorted(self.members.items(), key=sort, reverse=True)}

        result: Dict[str, MemberWithPosition] = {}

        pos = 1
        for k, v in sorted_members.items():
            mem_pos = MemberWithPosition(
                member=v,
                position=pos
            )
            result[k] = mem_pos
            pos += 1
        return result

    def __str__(self):
        headers = ["pos", "score", "user"]
        tbl = []
        for mp in self.sorted_members().values():
            line = [
                f"{str(mp.position):2} ",
                f"{str(mp.member.local_score):4} ",
                mp.member.username[:18]
            ]
            tbl.append(line)

        return tabulate(tbl, headers=headers)

    def __eq__(self, other: 'LeaderBoard') -> bool:
        for k, v in self.members.items():
            if k not in other.members:
                return False
            v2 = other.members[k]

            if v.local_score != v2.local_score:
                return False

        return True

    def __sub__(self, other: 'LeaderBoard') -> LeaderBoardDiff:

        # Empty chart in case of there is not members
        if len(self.members) == 0:
            return LeaderBoardDiff(members=[])

        members_change: List[MemberProgress] = []

        new_leader_board = self.sorted_members()
        old_leader_board = other.sorted_members()
        for id_, mem_pos in new_leader_board.items():
            if id_ not in old_leader_board:
                prog = MemberProgress(
                    member=mem_pos.member,
                    position=mem_pos.position,
                    new=True,
                    pos_change=0,
                    score_change=0
                )
            else:
                old_mem_pos = old_leader_board[id_]
                new_solutions = calc_member_new_solved(mem_pos.member, old_mem_pos.member)
                prog = MemberProgress(
                    member=mem_pos.member,
                    position=mem_pos.position,
                    new=False,
                    pos_change=-(mem_pos.position - old_mem_pos.position),
                    score_change=mem_pos.member.local_score - old_mem_pos.member.local_score,
                    new_solutions=new_solutions
                )

            members_change.append(prog)

        result = LeaderBoardDiff(members=members_change)
        return result
