"""Codeforces team import line: '<contest id>| <login> | <password> | <team name>'.

Team names come from users and may contain emoji; Codeforces shows them badly,
and a '|' or newline would break the line format, so names are cleaned here.
"""
import unicodedata

# Unicode categories dropped outright: other symbols (emoji, ™, ★), format chars
# (zero-width joiners), enclosing marks (keycaps), private use, surrogates, unassigned.
_DROPPED_CATEGORIES = {"So", "Cf", "Me", "Co", "Cs", "Cn"}
_VARIATION_SELECTORS = range(0xFE00, 0xFE10)
_SKIN_TONES = range(0x1F3FB, 0x1F400)


def _keep(char):
    code = ord(char)
    if code in _VARIATION_SELECTORS or code in _SKIN_TONES:
        return False
    return unicodedata.category(char) not in _DROPPED_CATEGORIES


def clean_team_name(text, fallback=""):
    """Drop emoji and decorative symbols; keep letters of any script, digits and
    ordinary punctuation such as O(DA^2) or #include<hope>."""
    kept = "".join(char for char in text if _keep(char))
    kept = kept.replace("|", "/")
    cleaned = " ".join(kept.split())
    return cleaned or fallback


def online_contest_id(contest_id):
    return f"{contest_id}o"
