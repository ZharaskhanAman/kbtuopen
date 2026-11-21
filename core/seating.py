"""Seating planner: spreads teams over rooms so that teams of the same
university never sit next to each other.

Pure functions only (no DB) so the algorithm is easy to test and reason about.

1. Each room gets a share of teams proportional to its capacity.
2. Teams are sorted so the biggest universities go first and dealt into an
   interleaved room sequence, which spreads every university across rooms.
0. Rooms reserved for one university are filled first with its teams.
   Strong teams (core/strong_teams.py) never sit in lecture halls.
3. Inside a room teams are ordered greedily so neighbours never share a
   university (when possible), then placed at evenly spaced seats.
"""
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache

_ORG_SEPARATORS = re.compile(r"[+,/&]")


@dataclass(frozen=True)
class SeatingTeam:
    id: int
    name: str
    organization: str
    strong: bool = False  # strong teams never sit in lecture halls


@dataclass(frozen=True)
class RoomSpec:
    number: int
    capacity: int
    only: str = ""  # reserved for one university, e.g. "KBTU"
    lecture: bool = False  # lecture hall: strong teams don't sit here


@dataclass(frozen=True)
class Assignment:
    team: SeatingTeam
    room: int
    position: int

    @property
    def label(self):
        return f"Room {self.room}, seat {self.position}"


class NotEnoughSeats(ValueError):
    pass


@lru_cache(maxsize=None)
def org_tokens(organization):
    """'SDU + KBTU' -> {'sdu', 'kbtu'}: a joint team counts as each university."""
    parts = (" ".join(part.split()).lower() for part in _ORG_SEPARATORS.split(organization))
    return frozenset(part for part in parts if part)


def conflicts(a, b):
    return bool(org_tokens(a.organization) & org_tokens(b.organization))


def allocate_quotas(team_count, rooms):
    """Largest-remainder split of team_count proportional to room capacity."""
    usable = [room for room in rooms if room.capacity > 0]
    total = sum(room.capacity for room in usable)
    if team_count > total:
        raise NotEnoughSeats(f"Не хватает мест: команд {team_count}, мест {total}")
    if team_count == 0:
        return ()

    exact = [team_count * room.capacity / total for room in usable]
    base = [int(value) for value in exact]
    leftover = team_count - sum(base)
    by_remainder = sorted(range(len(usable)), key=lambda i: (-(exact[i] - base[i]), i))
    bonus = set(by_remainder[:leftover])
    return tuple(
        (room.number, base[i] + (1 if i in bonus else 0))
        for i, room in enumerate(usable)
        if base[i] + (1 if i in bonus else 0) > 0
    )


def interleaved_rooms(quotas):
    """Room sequence where each room appears `quota` times, evenly interleaved."""
    slots = [
        ((i + 0.5) / quota, order, number)
        for order, (number, quota) in enumerate(quotas)
        for i in range(quota)
    ]
    return [number for _, _, number in sorted(slots)]


def spread_positions(count, capacity):
    """Evenly spaced 1-based seat numbers, e.g. 3 teams in 9 seats -> 1, 4, 7."""
    return [i * capacity // count + 1 for i in range(count)]


def _priority(teams):
    frequency = Counter(token for team in teams for token in org_tokens(team.organization))

    def key(team):
        tokens = org_tokens(team.organization)
        top = max(tokens, key=lambda t: (frequency[t], t)) if tokens else ""
        return (-frequency[top] if top else 0, top, team.id)

    return key


def _pressure(team, remaining):
    tokens = org_tokens(team.organization)
    return max((sum(1 for other in remaining if token in org_tokens(other.organization)) for token in tokens), default=0)


def arrange_room(teams):
    """Order teams so consecutive ones don't share a university, most-constrained first."""
    remaining = list(teams)
    order = []
    while remaining:
        previous = order[-1] if order else None
        candidates = [t for t in remaining if previous is None or not conflicts(previous, t)] or remaining
        pick = min(candidates, key=lambda t: (-_pressure(t, remaining), t.id))
        order.append(pick)
        remaining = [t for t in remaining if t is not pick]
    return order


def _fill_dedicated(teams, rooms):
    """Fill rooms reserved for one university with teams from exactly that
    university (joint teams like 'KBTU + IITU' stay in the open pool).
    Returns (assignments, teams left for open rooms)."""
    remaining = sorted(teams, key=lambda team: team.id)
    assignments = []
    for room in rooms:
        wanted = org_tokens(room.only)
        chosen = [
            t for t in remaining
            if org_tokens(t.organization) == wanted and not (room.lecture and t.strong)
        ][: room.capacity]
        chosen_ids = {team.id for team in chosen}
        remaining = [t for t in remaining if t.id not in chosen_ids]
        assignments = assignments + [
            Assignment(team=team, room=room.number, position=position)
            for team, position in zip(chosen, spread_positions(len(chosen), room.capacity))
        ]
    return assignments, remaining


def plan_seating(teams, rooms):
    dedicated = [room for room in rooms if room.only and room.capacity > 0]
    open_rooms = [room for room in rooms if not room.only]
    fixed, rest = _fill_dedicated(teams, dedicated)
    return tuple(fixed) + _plan_open_rooms(rest, open_rooms)


def _assign_slots(ordered, sequence, regular_rooms):
    """Strong teams take the earliest slots outside lecture halls (the
    sequence is interleaved, so they spread over those rooms); everyone else
    fills the remaining slots in order. Returns [(team, room number)]."""
    strong = [team for team in ordered if team.strong]
    others = [team for team in ordered if not team.strong]
    allowed_slots = [i for i, number in enumerate(sequence) if number in regular_rooms]
    if len(strong) > len(allowed_slots):
        raise NotEnoughSeats(
            f"Не хватает мест вне лекционных залов для сильных команд: "
            f"сильных {len(strong)}, мест {len(allowed_slots)}"
        )
    strong_slots = allowed_slots[: len(strong)]
    taken = set(strong_slots)
    other_slots = [i for i in range(len(sequence)) if i not in taken]
    return [(team, sequence[i]) for team, i in zip(strong, strong_slots)] + [
        (team, sequence[i]) for team, i in zip(others, other_slots)
    ]


def _plan_open_rooms(teams, rooms):
    quotas = allocate_quotas(len(teams), rooms)
    sequence = interleaved_rooms(quotas)
    ordered = sorted(teams, key=_priority(teams))
    regular_rooms = {room.number for room in rooms if not room.lecture}

    per_room = {number: [] for number, _ in quotas}
    for team, number in _assign_slots(ordered, sequence, regular_rooms):
        per_room[number].append(team)

    capacity = {room.number: room.capacity for room in rooms}
    return tuple(
        Assignment(team=team, room=number, position=position)
        for number, room_teams in per_room.items()
        for team, position in zip(
            arrange_room(room_teams), spread_positions(len(room_teams), capacity[number])
        )
    )


def count_adjacent_conflicts(assignments, ignore_rooms=()):
    """Pairs of same-university teams on neighbouring seat numbers in one room.
    ignore_rooms: rooms reserved for one university, where that is intended."""
    seats = {(a.room, a.position): a.team for a in assignments if a.room not in ignore_rooms}
    return sum(
        1
        for (room, position), team in seats.items()
        if (room, position + 1) in seats and conflicts(team, seats[(room, position + 1)])
    )
