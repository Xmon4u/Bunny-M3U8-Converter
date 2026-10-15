#!/usr/bin/env python3
"""Bunny Stream play/embed link to HLS playlist.m3u8."""

from __future__ import annotations

import argparse
import html
import re
import sys
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

PLAY_RE = re.compile(
    rf"(?:(?P<scheme>https?://)(?:www\.)?|(?<![A-Za-z0-9./]))"
    rf"(?P<host>player|iframe)\.mediadelivery\.net/"
    rf"(?P<kind>play|embed)/"
    rf"(?P<lib>\d+)/"
    rf"(?P<vid>{_UUID})"
    rf"/?"
    rf"(?P<query>\?[^\s\"'<>]*)?",
    re.I,
)

M3U8_RE = re.compile(
    r"https?://[^\s\"'<>]+?playlist\.m3u8(?:\?[^\s\"'<>]*)?",
    re.I,
)

PLAYLIST_RE = re.compile(
    r"https://[^\s\"'<>\\]+?playlist\.m3u8(?:\?[^\s\"'<>\\]*)?",
    re.I,
)

_SKIP_HOST = ("mediadelivery.net", "fonts.bunny.net", "w3.org", "schema.org")


@dataclass(frozen=True)
class PlayRef:
    library_id: str
    video_id: str
    host: str
    kind: str
    query: str
    raw: str

    @property
    def display(self) -> str:
        host = (
            "iframe.mediadelivery.net"
            if self.host == "iframe"
            else "player.mediadelivery.net"
        )
        query = f"?{self.query}" if self.query else ""
        return f"https://{host}/{self.kind}/{self.library_id}/{self.video_id}{query}"

    def candidate_urls(self) -> list[str]:
        query = f"?{self.query}" if self.query else ""
        iframe = (
            f"https://iframe.mediadelivery.net/embed/{self.library_id}/{self.video_id}{query}"
        )
        player = (
            f"https://player.mediadelivery.net/embed/{self.library_id}/{self.video_id}{query}"
        )
        play = (
            f"https://player.mediadelivery.net/play/{self.library_id}/{self.video_id}{query}"
        )
        if self.host == "player":
            return [player, iframe, play]
        return [iframe, player, play]


@dataclass(frozen=True)
class DirectPlaylist:
    url: str

    @property
    def display(self) -> str:
        return self.url


@dataclass(frozen=True)
class Invalid:
    raw: str

    @property
    def display(self) -> str:
        text = " ".join(self.raw.split())
        if len(text) <= 96:
            return text
        return text[:93] + "..."


Job = PlayRef | DirectPlaylist | Invalid


@dataclass
class Result:
    ok: bool
    source: str
    m3u8: str = ""
    title: str = ""
    error: str = ""


def clean_text(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = re.sub(r"[\u200b\u200c\u200d]", "", text)
    text = text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    text = html.unescape(text)
    return text.replace("\\/", "/")


def _strip_url(url: str) -> str:
    return url.rstrip(").,;\"'")


def parse_inputs(text: str) -> list[Job]:
    """Pull every Bunny link out of messy pasted text, one job per link."""
    jobs: list[Job] = []
    for line in clean_text(text).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        plays = list(PLAY_RE.finditer(stripped))
        if plays:
            for match in plays:
                query = (match.group("query") or "").lstrip("?")
                jobs.append(
                    PlayRef(
                        library_id=match.group("lib"),
                        video_id=match.group("vid"),
                        host=match.group("host").lower(),
                        kind=match.group("kind").lower(),
                        query=query,
                        raw=match.group(0),
                    )
                )
            continue
        playlists = [_strip_url(match.group(0)) for match in M3U8_RE.finditer(stripped)]
        if playlists:
            jobs.extend(DirectPlaylist(url) for url in playlists)
            continue
        jobs.append(Invalid(stripped))
    return jobs


def _request(url: str, referer: str | None) -> str:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if referer:
        headers["Referer"] = referer
    req = Request(url, headers=headers)
    with urlopen(req, timeout=18) as res:
        return res.read().decode("utf-8", errors="replace")


def fetch_html(url: str) -> str:
    try:
        return _request(url, referer=None)
    except HTTPError as err:
        if err.code in (401, 403, 429):
            if err.code == 429:
                time.sleep(0.8)
            return _request(url, referer="https://player.mediadelivery.net/")
        raise
    except (URLError, TimeoutError, OSError):
        return _request(url, referer=None)


def _is_missing_page(page: str) -> bool:
    match = re.search(r"<title>(.*?)</title>", page, re.I | re.S)
    if not match:
        return False
    title = re.sub(r"\s+", " ", match.group(1)).strip().lower()
    return title.startswith("404") or title.startswith("403") or title.startswith("401")


def extract_title(page: str) -> str:
    patterns = (
        r'property=["\']og:title["\'][^>]*content=["\']([^"\']*)',
        r'content=["\']([^"\']*)["\'][^>]*property=["\']og:title["\']',
        r"<title>(.*?)</title>",
    )
    for pattern in patterns:
        match = re.search(pattern, page, re.I | re.S)
        if not match:
            continue
        title = html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()
        if title and not title.lower().startswith("404"):
            return title
    return ""


def _playlist_score(url: str, video_id: str) -> int:
    lowered = url.lower()
    score = 0
    if video_id.lower() in lowered:
        score += 10
    if "b-cdn.net" in lowered:
        score += 3
    if "token=" in lowered or "bcdn_token=" in lowered:
        score += 4
    return score


def extract_m3u8(page: str, video_id: str) -> str | None:
    page = clean_text(page)
    found = [_strip_url(match.group(0)) for match in PLAYLIST_RE.finditer(page)]
    owned = [url for url in found if video_id.lower() in url.lower()]
    pool = owned or found
    if pool:
        return max(pool, key=lambda url: _playlist_score(url, video_id))

    asset_re = re.compile(
        rf"https://(?P<host>[^/\"'\s<>]+)/{re.escape(video_id)}/",
        re.I,
    )
    hosts: list[str] = []
    for match in asset_re.finditer(page):
        host = match.group("host")
        if any(skip in host.lower() for skip in _SKIP_HOST):
            continue
        if host not in hosts:
            hosts.append(host)
    if not hosts:
        return None
    hosts.sort(key=lambda host: (0 if "b-cdn.net" in host.lower() else 1, len(host)))
    return f"https://{hosts[0]}/{video_id}/playlist.m3u8"


def _failure_message(saw_html: bool, saw_403: bool, saw_404: bool, net_error: str) -> str:
    if saw_html:
        return "Playlist not found. The video may still be encoding."
    if saw_403 and not saw_404:
        return "Bunny returned 403. If the video uses a token, paste the full link with ?token= and expires."
    if saw_404:
        return "Video not found. Check that the link is correct."
    if net_error:
        return f"Network error: {net_error}"
    return "Could not convert."


def convert_job(job: Job, fetch=fetch_html) -> Result:
    if isinstance(job, DirectPlaylist):
        return Result(ok=True, source=job.display, m3u8=job.url, title="Direct playlist")
    if isinstance(job, Invalid):
        return Result(ok=False, source=job.display, error="This is not a Bunny play or embed link.")

    saw_html = False
    saw_403 = False
    saw_404 = False
    net_error = ""
    for page_url in job.candidate_urls():
        try:
            page = fetch(page_url)
        except HTTPError as err:
            err.close()
            if err.code in (401, 403):
                saw_403 = True
            elif err.code == 404:
                saw_404 = True
            else:
                net_error = f"HTTP {err.code}"
            continue
        except (URLError, TimeoutError, OSError) as err:
            reason = err.reason if isinstance(err, URLError) and err.reason else err
            net_error = str(reason)
            continue
        if _is_missing_page(page):
            saw_404 = True
            continue
        saw_html = True
        playlist = extract_m3u8(page, job.video_id)
        if playlist:
            return Result(
                ok=True,
                source=job.display,
                m3u8=playlist,
                title=extract_title(page),
            )
    return Result(
        ok=False,
        source=job.display,
        error=_failure_message(saw_html, saw_403, saw_404, net_error),
    )


def convert(play_url: str) -> str:
    jobs = parse_inputs(play_url)
    if len(jobs) != 1 or isinstance(jobs[0], Invalid):
        raise ValueError(
            "URL must look like:\n"
            "https://player.mediadelivery.net/play/LIBRARY_ID/VIDEO_ID"
        )
    result = convert_job(jobs[0])
    if not result.ok:
        raise RuntimeError(result.error)
    return result.m3u8


def _stdin_is_tty() -> bool:
    try:
        return bool(sys.stdin and sys.stdin.isatty())
    except Exception:
        return False


def _read_cli_text(urls: list[str]) -> str:
    if urls:
        return "\n".join(urls)
    if not _stdin_is_tty():
        return sys.stdin.read()
    print("Paste Bunny links. An empty line starts conversion.")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip():
            break
        lines.append(line)
    return "\n".join(lines)


def run_cli(urls: list[str] | None = None) -> int:
    jobs = parse_inputs(_read_cli_text(urls or []))
    if not jobs:
        print("No links found.", file=sys.stderr)
        return 1
    failed = 0
    for job in jobs:
        result = convert_job(job)
        if result.ok:
            print(result.m3u8)
        else:
            failed += 1
            print(f"Error: {result.error} [{result.source}]", file=sys.stderr)
    return 1 if failed else 0


def run_gui() -> int:
    try:
        from gui_app import launch
    except ImportError:
        print(
            "Install customtkinter to open the window:\n"
            "  py -3 -m pip install customtkinter",
            file=sys.stderr,
        )
        return 1
    return launch()


def main(argv: list[str] | None = None) -> int:
    if getattr(sys, "frozen", False):
        return run_gui()

    parser = argparse.ArgumentParser(description="Convert Bunny play URL to HLS m3u8")
    parser.add_argument("urls", nargs="*", help="Bunny play/embed URL")
    parser.add_argument("--cli", action="store_true", help="Force interactive CLI mode")
    parser.add_argument("--gui", action="store_true", help="Force GUI mode")
    args = parser.parse_args(argv)

    if args.urls and not args.gui:
        return run_cli(args.urls)
    if args.cli:
        return run_cli()
    if args.gui or _stdin_is_tty():
        code = run_gui()
        if code == 0 or args.gui:
            return code
        print("Falling back to CLI…", file=sys.stderr)
        return run_cli()
    return run_cli()


if __name__ == "__main__":
    raise SystemExit(main())
