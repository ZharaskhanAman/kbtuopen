"""Strong teams: onsite teams that solved 6+ problems at ICPC Kazakhstan 2026
(https://neerc.ifmo.ru/archive/2026/kazakhstan/standings.html), matched to our
registrations by team name or by 2+ member surnames. Seating keeps them out of
lecture halls. Matched by (organization, team name), case/space-insensitive.
"""

STRONG_TEAMS = [
    ("KBTU", "One more line"),  # 7 solved
    ("Satbayev University", "The Throngler"),  # 7
    ("KBTU", "Kurmash Nurzhan"),  # 7, IOMCHYDTCRY at ICPC
    ("SDU", "And yet they burn out"),  # 6
    ("SDU", "InParis"),  # 6, NARXOZ 1 at ICPC
    ("KBTU", "Jensen Huang"),  # 6, Rezero at ICPC
    ("IITU", "Nova"),  # 6
    ("KBTU", "pobedimye"),  # 6
]


def _key(organization, name):
    return (" ".join(organization.split()).lower(), " ".join(name.split()).lower())


STRONG_KEYS = frozenset(_key(org, name) for org, name in STRONG_TEAMS)


def is_strong(organization, name):
    return _key(organization, name) in STRONG_KEYS


def missing_strong_teams(teams):
    """Listed strong teams that aren't among the given (organization, name) pairs."""
    present = {_key(org, name) for org, name in teams}
    return [(org, name) for org, name in STRONG_TEAMS if _key(org, name) not in present]
