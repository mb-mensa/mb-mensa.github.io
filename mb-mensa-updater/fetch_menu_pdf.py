#!/usr/bin/env python3
"""Fetch the weekly PDF menu from the Migros Bank restaurant page."""

import datetime
import glob
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
        content = fetch_pdf_content(url)
        prev_path = get_previous_pdf_path(filepath)
        if prev_path is not None and read_bytes(prev_path) == content:
            print(f"Content unchanged from {prev_path}, skipping save.")
            delete_old_pdfs(keep=filepath)
            return
        save_pdf(content, filepath)
        delete_old_pdfs(keep=filepath)
        print(f"Downloaded: {filepath}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def get_pdf_filepath() -> str:
    today = datetime.date.today()
    year, kw, _ = today.isocalendar()
    return os.path.join(PDF_DIR, f"{year}_KW{kw:02d}.pdf")


def get_previous_pdf_path(current_filepath: str) -> str | None:
    existing = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
    others = [p for p in existing if p != current_filepath]
    return others[-1] if others else None


def delete_old_pdfs(keep: str) -> None:
    for path in glob.glob(os.path.join(PDF_DIR, "*.pdf")):
        if path != keep:
            os.remove(path)
            print(f"Removed old PDF: {path}")


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


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


def fetch_pdf_content(url: str) -> bytes:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def save_pdf(content: bytes, filepath: str) -> None:
    os.makedirs(PDF_DIR, exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(content)


if __name__ == "__main__":
    main()
