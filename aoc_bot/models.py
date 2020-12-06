import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pydantic

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

    @property
    def stars(self):

        silver_ = "1"
        gold_ = "2"

        repr_ = ""
        for day in sorted(self.completion_day_level.keys()):
            stars_info = self.completion_day_level[day]
            if stars_info.gold:
                repr_ += gold_
            elif stars_info.silver:
                repr_ += silver_

        return repr_

    def __str__(self):
        return f"{self.local_score=}  {self.username=}"


class MemberWithPosition(pydantic.BaseModel):
    member: Member
    position: int

    def __str__(self):
        return f"{self.position=}, {self.member.local_score=}, {self.member.username=}"


class MemberProgress(pydantic.BaseModel):

    def __str__(self):
        return f"{self.position=} {self.change=} {self.member.username=} {self.member.local_score=} {self.new=}"

    member: Member
    position: int
    new: bool
    change: int


class LeaderBoardDiff(pydantic.BaseModel):
    members: List[MemberProgress]

    def __str__(self):

        position_col = "pos"
        change_col = "change"
        score_col = "score"
        stars_col = "stars"
        user_col = "user"

        pos_l = len(position_col)
        ch_l = len(change_col)
        sc_l = len(score_col)
        stars_l = len(stars_col)
        name_l = len(user_col)

        for mp in self.members:
            m = mp.member
            pos_l = max(pos_l, len(str(mp.position)))
            ch_l = max(ch_l, len(str(mp.change)))
            name_l = max(name_l, len(m.username))
            sc_l = max(sc_l, len(str(m.local_score)))
            stars_l = max(stars_l, len(m.stars))

        header = f"{position_col:{pos_l}} {change_col:{ch_l}} {score_col:{sc_l}} {user_col:{name_l}}"
        members_reprs = [header]
        for mp in self.members:
            m = mp.member
            pos = str(mp.position)
            ch = mp.change
            # new_ = "new" if mp.new else "   "
            name = m.username
            sc = str(m.local_score)
            # stars = m.stars

            repr_ = f"{pos:{pos_l}} {ch:<+{ch_l}} {sc:{sc_l}} {name:{name_l}}"

            members_reprs.append(repr_)

        return "\n".join(members_reprs)


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

        position_col = "pos"
        score_col = "score"
        stars_col = "stars"
        user_col = "user"

        pos_l = len(position_col)
        sc_l = len(score_col)
        stars_l = len(stars_col)
        name_l = len(user_col)

        for mp in self.sorted_members().values():
            m = mp.member
            pos_l = max(pos_l, len(str(mp.position)))
            name_l = max(name_l, len(m.username))
            sc_l = max(sc_l, len(str(m.local_score)))
            stars_l = max(stars_l, len(m.stars))

        header = f"{position_col:{pos_l}} {score_col:{sc_l}} {user_col:{name_l}}"
        members_reprs = [header]
        for mp in self.sorted_members().values():
            m = mp.member
            pos = str(mp.position)
            # new_ = "new" if mp.new else "   "
            name = m.username
            sc = str(m.local_score)
            # stars = m.stars

            repr_ = f"{pos:{pos_l}} {sc:{sc_l}} {name:{name_l}}"

            members_reprs.append(repr_)

        return "\n".join(members_reprs)

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
                    change=0
                )
            else:
                old_mem_pos = old_leader_board[id_]
                prog = MemberProgress(
                    member=mem_pos.member,
                    position=mem_pos.position,
                    new=False,
                    change=-(mem_pos.position - old_mem_pos.position)
                )

            members_change.append(prog)

        result = LeaderBoardDiff(members=members_change)
        return result
