from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

from app.schemas.marketplace_preview import MarketplaceFeaturedItem, MarketplacePreviewRecord


TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
NEXT_RE = re.compile(r'rel="next"[^>]*href="([^"]+)"|id="seo-next"[^>]*href="([^"]+)"', re.IGNORECASE)
JSON_LD_RE = re.compile(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', re.IGNORECASE | re.DOTALL)
URL_RE = re.compile(r"https?://[^\s\"'<>]+")


class MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "meta":
            return
        self.meta.append({key.lower(): value or "" for key, value in attrs})


@dataclass
class ParsedJsonLdItem:
    title: str
    url: str | None = None
    image_url: str | None = None
    rating_value: float | None = None
    rating_count: int | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _marketplace_from_path(path: Path) -> str:
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
    return path.stem


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_preamble(text: str) -> str:
    lower_text = text.lower()
    html_index = lower_text.find("<html")
    if html_index == -1:
        return text
    return text[:html_index]


def _extract_source_url(text: str) -> str | None:
    preamble = _extract_preamble(text)
    match = URL_RE.search(preamble)
    return match.group(0) if match else None


def _extract_title(text: str) -> str | None:
    match = TITLE_RE.search(text)
    if not match:
        return None
    return unescape(match.group(1).strip()) or None


def _extract_meta_description(text: str) -> str | None:
    parser = MetaParser()
    parser.feed(text)
    for meta in parser.meta:
        name = meta.get("name", "").lower()
        prop = meta.get("property", "").lower()
        if name in {"description", "og:description"} or prop in {"description", "og:description"}:
            content = meta.get("content", "").strip()
            if content:
                return unescape(content)
    return None


def _extract_json_ld_types(text: str) -> list[str]:
    types: set[str] = set()
    for block in JSON_LD_RE.findall(text):
        try:
            payload = json.loads(block)
        except json.JSONDecodeError:
            continue

        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            if not isinstance(item, dict):
                continue
            item_type = item.get("@type")
            if isinstance(item_type, str):
                types.add(item_type)
            elif isinstance(item_type, list):
                types.update(entry for entry in item_type if isinstance(entry, str))
    return sorted(types)


def _extract_featured_items(text: str) -> list[MarketplaceFeaturedItem]:
    featured: list[MarketplaceFeaturedItem] = []
    for block in JSON_LD_RE.findall(text):
        try:
            payload = json.loads(block)
        except json.JSONDecodeError:
            continue

        payloads = payload if isinstance(payload, list) else [payload]
        for item in payloads:
            if not isinstance(item, dict):
                continue

            if item.get("@type") == "Product":
                title = str(item.get("name") or "").strip()
                if not title:
                    continue
                rating = item.get("aggregateRating") if isinstance(item.get("aggregateRating"), dict) else {}
                featured.append(
                    MarketplaceFeaturedItem(
                        title=title,
                        url=str(item.get("url")) if item.get("url") else None,
                        image_url=str(item.get("image")) if item.get("image") else None,
                        rating_value=float(rating.get("ratingValue")) if rating.get("ratingValue") else None,
                        rating_count=int(rating.get("ratingCount")) if rating.get("ratingCount") else None,
                    )
                )
                continue

            if item.get("@type") == "ItemList":
                for entry in item.get("itemListElement", [])[:3]:
                    if not isinstance(entry, dict):
                        continue
                    entry_item = entry.get("item") if isinstance(entry.get("item"), dict) else {}
                    title = str(entry_item.get("name") or "").strip()
                    if not title:
                        continue
                    rating = entry_item.get("aggregateRating") if isinstance(entry_item.get("aggregateRating"), dict) else {}
                    featured.append(
                        MarketplaceFeaturedItem(
                            title=title,
                            url=str(entry_item.get("url")) if entry_item.get("url") else None,
                            image_url=str(entry_item.get("image")) if entry_item.get("image") else None,
                            rating_value=float(rating.get("ratingValue")) if rating.get("ratingValue") else None,
                            rating_count=int(rating.get("ratingCount")) if rating.get("ratingCount") else None,
                        )
                    )

        if featured:
            break

    if not featured:
        # Last-resort extraction: any visible URL from the page body.
        for url in URL_RE.findall(text):
            if "/p/" in url or "/products/" in url:
                featured.append(MarketplaceFeaturedItem(title="Featured listing", url=url))
                break

    return featured[:3]


def _verification_hint(text: str) -> str | None:
    lowered = text.lower()
    for hint in ["human verification", "captcha", "verification", "please enable javascript", "access denied"]:
        if hint in lowered:
            return hint
    return None


def load_marketplace_previews() -> list[MarketplacePreviewRecord]:
    previews: list[MarketplacePreviewRecord] = []
    for path in sorted(_repo_root().glob("*info.txt")):
        text = _read_text(path)
        previews.append(
            MarketplacePreviewRecord(
                marketplace=_marketplace_from_path(path),
                source_file=path.name,
                source_url=_extract_source_url(text),
                page_title=_extract_title(text),
                meta_description=_extract_meta_description(text),
                has_next_page=bool(NEXT_RE.search(text) or re.search(r"page=2|seo-next", text, re.IGNORECASE)),
                has_json_ld=bool(JSON_LD_RE.search(text)),
                json_ld_types=_extract_json_ld_types(text),
                verification_hint=_verification_hint(text),
                featured_items=_extract_featured_items(text),
            )
        )
    return previews
