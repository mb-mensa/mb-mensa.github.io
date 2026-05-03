#!/usr/bin/env python3
"""Fetch the weekly PDF menu from the Migros Bank restaurant page."""

import datetime
import os
import re
import sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.betriebsrestaurants-migros.ch"
PAGE_URL = f"{BASE_URL}/landingpages/migrosbank/info-menueplan"
PDF_DIR = "pdf_menus"


def main() -> None:
    filepath = get_pdf_filepath()
    if os.path.exists(filepath):
        print(f"Already exists: {filepath}")
        return
    try:
        url = get_pdf_url()
        print(f"PDF URL: {url}")
        download_pdf(url, filepath)
        print(f"Downloaded: {filepath}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def get_pdf_filepath() -> str:
    today = datetime.date.today()
    year, kw, _ = today.isocalendar()
    return os.path.join(PDF_DIR, f"{year}_KW{kw:02d}.pdf")


def get_pdf_url() -> str:
    response = requests.get(PAGE_URL, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup.find_all("a-link", attrs={"namespace": "download"}):
        href = str(tag.get("href", ""))
        if href.lower().endswith(".pdf"):
            return urljoin(BASE_URL, href)

    for tag in soup.find_all("a", href=re.compile(r"\.pdf$", re.IGNORECASE)):
        return urljoin(BASE_URL, str(tag["href"]))

    raise RuntimeError("No PDF link found on the page.")


def download_pdf(url: str, filepath: str) -> None:
    os.makedirs(PDF_DIR, exist_ok=True)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    with open(filepath, "wb") as f:
        f.write(response.content)


if __name__ == "__main__":
    main()
