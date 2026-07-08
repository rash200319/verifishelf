"""Generate a quick intake report from marketplace HTML samples.

The repository keeps marketplace evidence in `*info.txt` files at the repo root.
This script scans those files and summarizes what each sample appears to cover,
which makes it easier to see what is still missing before scraper work starts.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


URL_RE = re.compile(r"https?://[^\s\"'<>]+")
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
NEXT_RE = re.compile(r'rel="next"[^>]*href="([^"]+)"|id="seo-next"[^>]*href="([^"]+)"', re.IGNORECASE)
JSON_LD_RE = re.compile(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', re.IGNORECASE | re.DOTALL)
SECTION_HEADER_RE = re.compile(
    r"^(?!<)(?P<header>.*?(?P<kind>search|product|seller|store)[^\n]*?[-:])\s*(?P<url>https?://\S+)",
    re.IGNORECASE,
)


class MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "meta":
            return
        attr_map = {key.lower(): value or "" for key, value in attrs}
        self.meta.append(attr_map)


@dataclass
class MarketplaceSample:
    marketplace: str
    source_file: str
    sample_kind: str
    source_url: str | None
    page_title: str | None
    has_search_page: bool
    has_product_page: bool
    has_seller_page: bool
    has_next_page: bool
    has_json_ld: bool
    json_ld_types: list[str]
    meta_description: str | None
    verification_hint: str | None
    likely_missing: list[str]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_preamble(text: str) -> str:
    lower_text = text.lower()
    html_index = lower_text.find("<html")
    if html_index == -1:
        return text
    return text[:html_index]


def first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    groups = [group for group in match.groups() if group]
    return groups[0] if groups else match.group(0)


def detect_sample_kind(text: str) -> str:
    section_types = detect_section_types(text)
    if len(section_types) == 1:
        return next(iter(section_types))
    if "search" in section_types:
        return "search"
    if "product" in section_types:
        return "product"
    if "seller" in section_types:
        return "seller"
    return "unknown"


def detect_section_types(text: str) -> set[str]:
    kinds: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<"):
            continue
        match = SECTION_HEADER_RE.match(stripped)
        if not match:
            continue
        kind = match.group("kind").lower()
        if kind == "store":
            kind = "seller"
        kinds.add(kind)
    return kinds


def detect_marketplace(path: Path, text: str) -> str:
    stem = path.stem.lower()
    if stem.startswith("daraz"):
        return "Daraz"
    if stem.startswith("amazon"):
        return "Amazon"
    if stem.startswith("flipkart"):
        return "Flipkart"
    if stem.startswith("lazada"):
        return "Lazada"
    if stem.startswith("tokopedia"):
        return "Tokopedia"

    first_line = text.splitlines()[0].lower() if text.splitlines() else ""
    if "daraz" in first_line:
        return "Daraz"
    if "amazon" in first_line:
        return "Amazon"
    if "flipkart" in first_line:
        return "Flipkart"
    if "lazada" in first_line:
        return "Lazada"
    if "tokopedia" in first_line:
        return "Tokopedia"
    return path.stem


def extract_json_ld_types(text: str) -> list[str]:
    types: list[str] = []
    for block in JSON_LD_RE.findall(text):
        try:
            payload = json.loads(block)
        except json.JSONDecodeError:
            continue
        items: Iterable[object]
        if isinstance(payload, list):
            items = payload
        else:
            items = [payload]
        for item in items:
            if isinstance(item, dict):
                item_type = item.get("@type")
                if isinstance(item_type, str):
                    types.append(item_type)
                elif isinstance(item_type, list):
                    types.extend([entry for entry in item_type if isinstance(entry, str)])
    return sorted(set(types))


def extract_meta_description(text: str) -> str | None:
    parser = MetaParser()
    parser.feed(text)
    for meta in parser.meta:
        name = meta.get("name", "").lower()
        prop = meta.get("property", "").lower()
        if name in {"description", "og:description"} or prop in {"description", "og:description"}:
            content = meta.get("content", "").strip()
            if content:
                return content
    return None


def classify_and_summarize(path: Path) -> MarketplaceSample:
    text = read_text(path)
    marketplace = detect_marketplace(path, text)
    sample_kind = detect_sample_kind(text)
    urls = URL_RE.findall(text)
    source_url = urls[0] if urls else None
    page_title = first_match(TITLE_RE, text)
    next_page = bool(NEXT_RE.search(text) or re.search(r"page=2|page/2|seo-next", text, re.IGNORECASE))
    json_ld_types = extract_json_ld_types(text)
    has_json_ld = bool(json_ld_types)
    meta_description = extract_meta_description(text)

    section_types = detect_section_types(text)
    has_search_page = "search" in section_types
    has_product_page = "product" in section_types
    has_seller_page = "seller" in section_types

    verification_hint = None
    lowered = text.lower()
    for hint in ["human verification", "captcha", "js required", "verification", "access denied", "please enable javascript"]:
        if hint in lowered:
            verification_hint = hint
            break

    likely_missing: list[str] = []
    if not has_search_page:
        likely_missing.append("search page sample")
    if not has_product_page:
        likely_missing.append("product detail sample")
    if not has_seller_page:
        likely_missing.append("seller/store page sample")
    if not next_page and has_search_page:
        likely_missing.append("pagination sample")
    if not has_json_ld:
        likely_missing.append("structured data sample")
    if not meta_description:
        likely_missing.append("meta description sample")

    return MarketplaceSample(
        marketplace=marketplace,
        source_file=path.name,
        sample_kind=sample_kind,
        source_url=source_url,
        page_title=page_title,
        has_search_page=has_search_page,
        has_product_page=has_product_page,
        has_seller_page=has_seller_page,
        has_next_page=next_page,
        has_json_ld=has_json_ld,
        json_ld_types=json_ld_types,
        meta_description=meta_description,
        verification_hint=verification_hint,
        likely_missing=likely_missing,
    )


def format_report(samples: list[MarketplaceSample]) -> str:
    lines: list[str] = []
    lines.append("Marketplace intake report")
    lines.append("")
    for sample in samples:
        lines.append(f"## {sample.marketplace}")
        lines.append(f"Source file: {sample.source_file}")
        lines.append(f"Sample kind: {sample.sample_kind}")
        if sample.source_url:
            lines.append(f"Source URL: {sample.source_url}")
        if sample.page_title:
            lines.append(f"Title: {sample.page_title}")
        if sample.meta_description:
            lines.append(f"Description: {sample.meta_description}")
        lines.append(
            "Coverage: "
            + ", ".join(
                [
                    f"search={sample.has_search_page}",
                    f"product={sample.has_product_page}",
                    f"seller={sample.has_seller_page}",
                    f"next_page={sample.has_next_page}",
                    f"json_ld={sample.has_json_ld}",
                ]
            )
        )
        if sample.json_ld_types:
            lines.append(f"JSON-LD types: {', '.join(sample.json_ld_types)}")
        if sample.verification_hint:
            lines.append(f"Verification hint: {sample.verification_hint}")
        if sample.likely_missing:
            lines.append(f"Likely missing: {', '.join(sample.likely_missing)}")
        else:
            lines.append("Likely missing: none detected from this sample")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a marketplace intake report from *info.txt files.")
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root that contains the marketplace info files.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of markdown.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    files = sorted(root.glob("*info.txt"))
    samples = [classify_and_summarize(path) for path in files]

    if args.json:
        print(json.dumps([asdict(sample) for sample in samples], indent=2, ensure_ascii=True))
    else:
        print(format_report(samples))


if __name__ == "__main__":
    main()