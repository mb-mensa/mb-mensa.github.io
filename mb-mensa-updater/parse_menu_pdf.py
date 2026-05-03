#!/usr/bin/env python3
"""Parse Migros Bank menu PDFs and render HTML tables."""

import os
import re

from pypdf import PdfReader

DAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
PRICE_RE = re.compile(r"^\s*\d+\.\d{2}\s*$")
DATE_RE = re.compile(r"^\s*\d+\.\s+\w+\s*$")
FLEISCH_RE = re.compile(r"^\s*Fleisch:")
FOOTER_MARKERS = ["Für Fragen", "Öffnungszeiten", "Bei den Menüs"]
PDF_DIR = "pdf_menus"
HTML_DIR = "html_menus"

PAGE_FOOTER = """\
<footer>
  <p>
    HTML viewer for the Migros Bank Personalrestaurant menu plan publicly available at
    <a href="https://www.betriebsrestaurants-migros.ch/landingpages/migrosbank/info-menueplan">\
betriebsrestaurants-migros.ch/landingpages/migrosbank/info-menueplan</a>.
    This page simply parses the PDF to HTML once a week to save you some clicks and bandwidth.
  </p>
  <p>
    Inspired by <a href="https://mensa.davidemarcoli.dev">mensa.davidemarcoli.dev</a>,
    but much simpler and with fewer features.
    Hosted via <a href="https://docs.github.com/en/pages">GitHub Pages</a>
    from repo
    <a href="https://github.com/mb-mensa/mb-mensa.github.io">mb-mensa/mb-mensa.github.io</a>.
  </p>
</footer>"""

PAGE_CSS = """\
    body {
      font-family: sans-serif;
      max-width: 960px;
      margin: 2rem auto;
      padding: 0 1rem;
      color: #222;
    }
    table { border-collapse: collapse; width: 100%; }
    th { text-align: left; padding: 6px 12px; border-bottom: 2px solid #ddd; }
    td { padding: 6px 12px; vertical-align: top; border-bottom: 1px solid #f0f0f0; }
    td:nth-child(2) { white-space: nowrap; }
    footer {
      margin-top: 2.5rem;
      border-top: 1px solid #ddd;
      padding-top: 1rem;
      font-size: 0.8rem;
      color: #666;
    }
    footer a { color: #0066cc; }"""


def page_html(body: str) -> str:
    return f"""\
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="Wochenmenü des Migros Bank Personalrestaurants">
  <meta name="robots" content="index, follow">
  <title>MB Mensa</title>
  <link rel="icon" href="data:,">
  <style>
{PAGE_CSS}
  </style>
</head>
<body>
{body}
{PAGE_FOOTER}
</body>
</html>
"""


def main() -> None:
    os.makedirs(HTML_DIR, exist_ok=True)
    pdf_files = sorted(f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf"))

    for pdf_file in pdf_files:
        week = os.path.splitext(pdf_file)[0]
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        menu = parse_menu(pdf_path)
        html = page_html(to_table(menu))
        html_path = os.path.join(HTML_DIR, f"{week}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Written: {html_path}")


def to_table(menu: list[dict[str, str]]) -> str:
    header = "  <tr>" "<th>Tag</th>" "<th>Datum</th>" "<th>Local</th>" "<th>Vegi</th>" "</tr>"
    rows = []
    for m in menu:
        local = f"<strong>{m['local']}</strong>"
        if m["local_desc"]:
            local += f"<br>{m['local_desc']}"
        veggie = f"<strong>{m['veggie']}</strong>"
        if m["veggie_desc"]:
            veggie += f"<br>{m['veggie_desc']}"
        rows.append(
            f"  <tr>"
            f"<td>{m['day']}</td>"
            f"<td>{m['date']}</td>"
            f"<td>{local}</td>"
            f"<td>{veggie}</td>"
            f"</tr>"
        )
    inner = "\n".join([header] + rows)
    return f"<table>\n{inner}\n</table>"


def parse_menu(pdf_path: str) -> list[dict[str, str]]:
    reader = PdfReader(pdf_path)
    lines = reader.pages[0].extract_text().split("\n")

    day_indices = {day: i for i, line in enumerate(lines) for day in DAYS if line.strip() == day}
    sorted_days = sorted(day_indices.items(), key=lambda x: x[1])
    results = []

    for idx, (day, start) in enumerate(sorted_days):
        end = sorted_days[idx + 1][1] if idx + 1 < len(sorted_days) else len(lines)
        block = lines[start + 1 : end]
        date, local, local_desc, veggie, veggie_desc = parse_day_block(block)
        results.append(
            {
                "day": day,
                "date": date,
                "local": local,
                "local_desc": local_desc,
                "veggie": veggie,
                "veggie_desc": veggie_desc,
            }
        )

    return results


def strip_footer(lines: list[str]) -> list[str]:
    for i, line in enumerate(lines):
        if any(marker in line for marker in FOOTER_MARKERS):
            return lines[:i]
    return lines


def split_into_groups(lines: list[str]) -> list[list[str]]:
    groups: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip():
            current.append(line)
        else:
            if current:
                groups.append(current)
                current = []
    if current:
        groups.append(current)
    return groups


def parse_day_block(lines: list[str]) -> tuple[str, str, str, str, str]:
    lines = strip_footer(lines)

    date = ""
    rest = list(lines)
    for i, line in enumerate(lines):
        if line.strip() and DATE_RE.match(line):
            date = line.strip()
            rest = lines[i + 1 :]
            break

    price_indices = [i for i, line in enumerate(rest) if PRICE_RE.match(line)]

    if not price_indices:
        local, local_desc, veggie, veggie_desc = parse_no_price_block(rest)
        return date, local, local_desc, veggie, veggie_desc

    first_price_idx = price_indices[0]
    local_lines = rest[:first_price_idx]
    after_price = rest[first_price_idx + 1 :]

    if after_price and FLEISCH_RE.match(after_price[0]):
        after_price = after_price[1:]

    local_name, local_desc = extract_dish(local_lines)
    veggie_name, veggie_desc = extract_dish(after_price)
    return date, local_name, local_desc, veggie_name, veggie_desc


def parse_no_price_block(lines: list[str]) -> tuple[str, str, str, str]:
    groups = split_into_groups(lines)
    if len(groups) >= 2:
        local_name, local_desc = extract_dish(groups[0])
        veggie_name, veggie_desc = extract_dish(groups[1])
        return local_name, local_desc, veggie_name, veggie_desc
    # Fallback: single line with two columns separated by multiple spaces
    combined = " ".join(line.strip() for line in lines if line.strip())
    parts = [p.strip() for p in re.split(r"\s{2,}", combined) if p.strip()]
    local = parts[0] if parts else ""
    veggie = parts[1] if len(parts) > 1 else local
    return local, "", veggie, ""


def extract_dish(lines: list[str]) -> tuple[str, str]:
    non_blank = [line.strip() for line in lines if line.strip()]
    name = non_blank[0] if non_blank else ""
    desc = non_blank[1] if len(non_blank) > 1 else ""
    return name, desc


if __name__ == "__main__":
    main()
