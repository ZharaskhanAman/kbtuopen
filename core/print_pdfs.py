"""Printable PDFs for the contest day, built with reportlab (no system deps).

* password_slips_pdf — cut-out slips, 6 per A4 portrait page
* team_cards_pdf — one landscape A4 desk card per team with a big seat number

Pure functions over small dataclasses so they are easy to test. DejaVu fonts
(core/fonts, free licence) cover Cyrillic and Kazakh; emoji are not in the font,
so names are cleaned with the same rules as the Codeforces export.
"""
import io
from dataclasses import dataclass, field
from pathlib import Path

from reportlab.lib.colors import HexColor, black
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from core.codeforces import clean_team_name

FONT_DIR = Path(__file__).resolve().parent / "fonts"
SANS, SANS_BOLD, MONO, MONO_BOLD = "DejaVuSans", "DejaVuSans-Bold", "DejaVuSansMono", "DejaVuSansMono-Bold"
BLUE, VIOLET = HexColor("#2563EB"), HexColor("#7C3AED")
SLIPS_PER_PAGE = 6


def _register_fonts():
    for name in (SANS, SANS_BOLD, MONO, MONO_BOLD):
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / f"{name}.ttf")))


@dataclass(frozen=True)
class PrintTexts:
    title: str
    place_date: str
    contest_url: str


@dataclass(frozen=True)
class Slip:
    team: str
    organization: str
    login: str
    password: str
    room: int | None
    seat: int | None


@dataclass(frozen=True)
class TeamCard:
    team: str
    organization: str
    members: list = field(default_factory=list)
    room: int | None = None
    seat: int | None = None


def seat_number(seat):
    return f"{seat:02d}" if seat else "—"


def place_label(room, seat):
    return f"Room {room}, seat {seat}" if room else "Room: ask organizers"


def _fit(text, font, max_size, min_size, width):
    """Largest size in [min_size, max_size] at which text fits; truncates at min_size."""
    size = max_size
    while size > min_size and pdfmetrics.stringWidth(text, font, size) > width:
        size -= 0.5
    while len(text) > 1 and pdfmetrics.stringWidth(text, font, size) > width:
        text = text[:-2] + "…"
    return text, size


def _wrap(text, font, size, width, max_lines):
    """Greedy word wrap; returns None if it needs more than max_lines lines."""
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if pdfmetrics.stringWidth(candidate, font, size) <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines if len(lines) <= max_lines else None


def _centered(c, text, font, max_size, min_size, x_center, y, width):
    text, size = _fit(text, font, max_size, min_size, width)
    c.setFont(font, size)
    c.drawCentredString(x_center, y, text)


def _draw_slip(c, slip, texts, top, left, width, height):
    center = left + width / 2
    c.setLineWidth(0.8)
    c.line(left, top, left + width, top)
    c.setFillColor(black)
    c.setFont(SANS, 9)
    c.drawCentredString(center, top - 16, texts.title)
    c.drawCentredString(center, top - 28, texts.place_date)
    _centered(c, clean_team_name(slip.organization), SANS_BOLD, 10.5, 7, center, top - 46, width - 20)
    _centered(c, clean_team_name(slip.team, fallback=slip.login), SANS_BOLD, 10.5, 7, center, top - 60, width - 20)

    c.setFont(SANS, 10)
    c.drawString(left + 16, top - 82, place_label(slip.room, slip.seat))
    right = left + width * 0.5
    c.setFont(MONO, 9)
    c.drawString(right, top - 82, texts.contest_url)
    for offset, label, value, font, size in ((96, "Login: ", slip.login, MONO, 10), (110, "Password: ", slip.password, MONO_BOLD, 11)):
        c.setFont(SANS, 10)
        c.drawString(right, top - offset, label)
        c.setFont(font, size)
        c.drawString(right + pdfmetrics.stringWidth(label, SANS, 10), top - offset, value)
    if height:
        c.line(left, top - height, left + width, top - height)


def password_slips_pdf(slips, texts):
    _register_fonts()
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_w, page_h = A4
    margin = 40
    slip_h = (page_h - 2 * margin) / SLIPS_PER_PAGE
    for index, slip in enumerate(slips):
        position = index % SLIPS_PER_PAGE
        if index and position == 0:
            c.showPage()
        last_on_page = position == SLIPS_PER_PAGE - 1 or index == len(slips) - 1
        _draw_slip(c, slip, texts, page_h - margin - position * slip_h, margin, page_w - 2 * margin,
                   slip_h if last_on_page else 0)
    c.showPage()
    c.save()
    return buffer.getvalue()


def _draw_card(c, card, texts, page_w, page_h):
    m = 28
    left, bottom, width, height = m, m, page_w - 2 * m, page_h - 2 * m
    footer_h = 52
    center = page_w / 2
    c.setLineWidth(2)
    c.roundRect(left, bottom, width, height, 16)
    c.line(left, bottom + footer_h, left + width, bottom + footer_h)

    header = f"{clean_team_name(card.organization)}: {clean_team_name(card.team, fallback='Team')}"
    lines = _wrap(header, SANS_BOLD, 26, width - 40, 1) or _wrap(header, SANS_BOLD, 22, width - 40, 2)
    top = bottom + height - 40
    if lines:
        size = 26 if len(lines) == 1 else 22
        c.setFont(SANS_BOLD, size)
        for i, line in enumerate(lines):
            c.drawCentredString(center, top - i * (size + 4), line)
        top -= (len(lines) - 1) * (size + 4)
    else:
        _centered(c, header, SANS_BOLD, 22, 12, center, top, width - 40)
    if card.members:
        _centered(c, f"({', '.join(clean_team_name(m) for m in card.members)})", SANS, 13, 8, center, top - 22, width - 40)

    c.setFillColor(BLUE)
    c.setFont(SANS_BOLD, 72)
    c.drawCentredString(left + 175, bottom + 290, "KBTU")
    c.setFillColor(VIOLET)
    c.drawCentredString(left + 175, bottom + 210, "OPEN")
    c.setFillColor(black)
    _centered(c, seat_number(card.seat), SANS, 210, 80, left + width * 0.68, bottom + 175, width * 0.55)

    room = f"Room {card.room}" if card.room else "Room: ask organizers"
    prefix = f"{texts.title} · "
    total = pdfmetrics.stringWidth(prefix, SANS, 20) + pdfmetrics.stringWidth(room, SANS_BOLD, 22)
    x = center - total / 2
    c.setFont(SANS, 20)
    c.drawString(x, bottom + footer_h + 22, prefix)
    c.setFont(SANS_BOLD, 22)
    c.drawString(x + pdfmetrics.stringWidth(prefix, SANS, 20), bottom + footer_h + 22, room)
    _centered(c, texts.place_date, SANS, 18, 10, center, bottom + 20, width - 40)


def team_cards_pdf(cards, texts):
    _register_fonts()
    buffer = io.BytesIO()
    page_w, page_h = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=(page_w, page_h))
    for card in cards:
        _draw_card(c, card, texts, page_w, page_h)
        c.showPage()
    if not cards:
        c.showPage()
    c.save()
    return buffer.getvalue()
