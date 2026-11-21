"""CSV export/import of seating so it can be reviewed and edited by hand.

Teams are matched by Team + Organization when both are filled (the pair is
unique, and it survives copying prod data via the public /teams page, where
ids differ), otherwise by login (kbtuspring26-<id>). Import is all-or-nothing: any bad
row rejects the whole file.
"""
import csv
import io
import re
from dataclasses import dataclass

from core.seating import Assignment, SeatingTeam

HEADER = ["Login", "Team", "Organization", "Members", "Status", "Room", "Seat", "Current seat"]
REQUIRED_COLUMNS = ("Room", "Seat")
OPTIONAL_COLUMNS = ("Login", "Team", "Organization")
MAX_ERRORS = 30
_SEAT_LABEL = re.compile(r"^Room (\d+), seat (\d+)$")


@dataclass(frozen=True)
class ImportResult:
    assignments: tuple
    errors: tuple


def parse_label(label):
    """'Room 365, seat 7' -> (365, 7); anything else -> None."""
    match = _SEAT_LABEL.match((label or "").strip())
    return (int(match[1]), int(match[2])) if match else None


def seating_team(team):
    return SeatingTeam(id=team.id, name=team.name, organization=team.organization.name)


def export_csv(teams, seat_for):
    """seat_for(team) -> (room, position) or None. Returns CSV text for Excel."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(HEADER)
    for team in teams:
        room, position = seat_for(team) or ("", "")
        writer.writerow([
            team.login,
            team.name,
            team.organization.name,
            ", ".join(member.full_name for member in team.members.all()),
            team.status,
            room,
            position,
            team.seat or "",
        ])
    return buffer.getvalue()


def decode_upload(raw):
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1251")  # Excel on a Russian Windows saves CSV like this


def _delimiter(text):
    first_line = text.split("\n", 1)[0]
    return max(";,\t", key=first_line.count)


def _team_id(login):
    tail = login.rsplit("-", 1)[-1]
    return int(tail) if tail.isdigit() else None


def _norm(text):
    return " ".join(text.split()).lower()


def index_by_name(teams_by_id):
    """(team name, organization) -> [teams]; this pair is unique on prod, the name alone isn't."""
    index = {}
    for team in teams_by_id.values():
        key = (_norm(team.name), _norm(team.organization.name))
        index[key] = index.get(key, []) + [team]
    return index


def _find_team(line, row, teams_by_id, teams_by_name):
    """Returns (team, error). Name + organization win over login, because ids
    differ between prod and a local copy loaded from the public /teams page."""
    if row["Team"] and row["Organization"]:
        found = teams_by_name.get((_norm(row["Team"]), _norm(row["Organization"])), [])
        if len(found) == 1:
            return found[0], None
        problem = "нет оффлайн-команды" if not found else "несколько команд"
        return None, f"Строка {line}: {problem} «{row['Team']}» ({row['Organization']})"

    login = row["Login"]
    team_id = _team_id(login)
    if team_id is None:
        return None, f"Строка {line}: не понимаю логин «{login}»"
    team = teams_by_id.get(team_id)
    if team is None:
        return None, f"Строка {line}: нет оффлайн-команды с логином {login}"
    return team, None


def _parse_row(line, row, teams_by_id, teams_by_name, rooms_by_number):
    """Returns (assignment, error); exactly one of them is set."""
    team, error = _find_team(line, row, teams_by_id, teams_by_name)
    if error:
        return None, error
    if not row["Room"].isdigit():
        return None, f"Строка {line}: кабинет должен быть числом, а не «{row['Room']}»"
    room = rooms_by_number.get(int(row["Room"]))
    if room is None:
        return None, f"Строка {line}: кабинет {row['Room']} не найден или выключен в Rooms"
    if not row["Seat"].isdigit():
        return None, f"Строка {line}: место должно быть числом, а не «{row['Seat']}»"
    position = int(row["Seat"])
    if not 1 <= position <= room.capacity:
        return None, f"Строка {line}: в кабинете {room.number} только {room.capacity} мест"
    return Assignment(team=seating_team(team), room=room.number, position=position), None


def parse_seating_csv(text, teams_by_id, rooms_by_number):
    reader = csv.DictReader(io.StringIO(text), delimiter=_delimiter(text))
    columns = [name.strip() for name in reader.fieldnames or []]
    missing = [name for name in REQUIRED_COLUMNS if name not in columns]
    if "Login" not in columns and not {"Team", "Organization"} <= set(columns):
        missing.append("Login (или Team и Organization)")
    if missing:
        return ImportResult(assignments=(), errors=(f"В файле нет колонок: {', '.join(missing)}",))
    reader.fieldnames = columns

    teams_by_name = index_by_name(teams_by_id)
    assignments, errors = [], []
    team_lines, seat_lines = {}, {}
    for line, raw in enumerate(reader, start=2):
        row = {name: (raw.get(name) or "").strip() for name in REQUIRED_COLUMNS + OPTIONAL_COLUMNS}
        if not row["Room"] and not row["Seat"]:
            continue
        assignment, error = _parse_row(line, row, teams_by_id, teams_by_name, rooms_by_number)
        if error is None and assignment.team.id in team_lines:
            error = f"Строка {line}: команда {assignment.team.name} уже есть в строке {team_lines[assignment.team.id]}"
        seat = assignment and (assignment.room, assignment.position)
        if error is None and seat in seat_lines:
            error = f"Строка {line}: место {assignment.label} уже занято (строка {seat_lines[seat]})"
        if error:
            errors.append(error)
            continue
        team_lines[assignment.team.id] = line
        seat_lines[seat] = line
        assignments.append(assignment)

    return ImportResult(assignments=tuple(assignments), errors=tuple(errors[:MAX_ERRORS]))
