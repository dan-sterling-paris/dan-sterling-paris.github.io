#!/usr/bin/env python3
"""
generate_post.py — daily football news blog generator.

For each channel in channels.yaml, fetches the YouTube RSS feed, finds videos
published in the last 24 hours, retrieves transcripts (with title+description
fallback), then calls the Anthropic API to write a single cohesive roundup in
Markdown, grouped by the themes in topic.yaml.

If combined transcript content exceeds SYNTHESIS_CHAR_LIMIT it runs a
per-video summarisation pass first (map), then synthesises the roundup from
those summaries (reduce).

Usage:
    python scripts/generate_post.py [options]

    --dry-run          Print the generated post to stdout; do not write to disk.
    --window-hours N   Hours to look back for new videos (default: 24).
    --config-dir DIR   Directory containing channels.yaml and topic.yaml
                       (default: repo root, inferred from this script's location).
"""

import argparse
import datetime
import logging
import os
import sys
import textwrap
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error

import yaml
import anthropic

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

YOUTUBE_RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
YOUTUBE_WATCH_URL = "https://www.youtube.com/watch?v={video_id}"
ATOM_NS = "http://www.w3.org/2005/Atom"
MEDIA_NS = "http://search.yahoo.com/mrss/"
YT_NS = "http://www.youtube.com/xml/schemas/2015"

# If combined raw content exceeds this, run per-video summaries first.
# ~500 k chars ≈ ~125 k tokens — leaves headroom for the synthesis prompt.
SYNTHESIS_CHAR_LIMIT = 500_000

# Seconds to wait between transcript fetch attempts (avoids rate-limiting).
TRANSCRIPT_DELAY = 1.5

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config(config_dir: Path) -> tuple[dict, dict]:
    with open(config_dir / "channels.yaml") as f:
        channels_cfg = yaml.safe_load(f)
    with open(config_dir / "topic.yaml") as f:
        topic_cfg = yaml.safe_load(f)
    return channels_cfg, topic_cfg

# ---------------------------------------------------------------------------
# RSS fetching
# ---------------------------------------------------------------------------

def fetch_rss(channel_id: str, channel_name: str) -> Optional[ET.Element]:
    url = YOUTUBE_RSS_URL.format(channel_id=channel_id)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; DailyBlogBot/1.0; +https://github.com)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return ET.fromstring(resp.read())
    except urllib.error.HTTPError as exc:
        log.warning("RSS %s (%s) — HTTP %s", channel_name, channel_id, exc.code)
    except urllib.error.URLError as exc:
        log.warning("RSS %s (%s) — %s", channel_name, channel_id, exc.reason)
    except Exception as exc:
        log.warning("RSS %s (%s) — %s", channel_name, channel_id, exc)
    return None


def parse_entries(root: ET.Element, since: datetime.datetime, channel_name: str) -> list[dict]:
    """Return entries published after `since` (UTC-aware)."""
    ns = {"atom": ATOM_NS, "media": MEDIA_NS, "yt": YT_NS}
    results = []

    for entry in root.findall("atom:entry", ns):
        published_el = entry.find("atom:published", ns)
        if published_el is None:
            continue

        try:
            published = datetime.datetime.fromisoformat(published_el.text.strip())
            if published.tzinfo is None:
                published = published.replace(tzinfo=datetime.timezone.utc)
            published = published.astimezone(datetime.timezone.utc)
        except ValueError:
            log.debug("Unparseable date: %s", published_el.text)
            continue

        if published < since:
            continue

        video_id_el = entry.find("yt:videoId", ns)
        title_el = entry.find("atom:title", ns)
        link_el = entry.find("atom:link", ns)
        group = entry.find("media:group", ns)

        video_id = video_id_el.text if video_id_el is not None else None
        title = title_el.text if title_el is not None else "Untitled"
        url = (
            link_el.get("href")
            if link_el is not None
            else (YOUTUBE_WATCH_URL.format(video_id=video_id) if video_id else "#")
        )

        description = ""
        if group is not None:
            desc_el = group.find("media:description", ns)
            if desc_el is not None and desc_el.text:
                description = desc_el.text.strip()[:3000]

        results.append({
            "video_id": video_id,
            "title": title,
            "url": url,
            "published": published,
            "description": description,
            "channel": channel_name,
            "transcript": None,
            "summary": None,
        })

    return results

# ---------------------------------------------------------------------------
# Transcript fetching
# ---------------------------------------------------------------------------

def fetch_transcript(video_id: str) -> Optional[str]:
    """Return transcript text, or None if unavailable / disabled."""
    if not video_id:
        return None

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Priority: manual English → auto-generated English → translate whatever's available
        transcript = None
        try:
            transcript = transcript_list.find_transcript(["en", "en-GB", "en-US"])
        except NoTranscriptFound:
            try:
                transcript = transcript_list.find_generated_transcript(["en", "en-GB", "en-US"])
            except NoTranscriptFound:
                available = list(transcript_list)
                if available:
                    try:
                        transcript = available[0].translate("en")
                    except Exception:
                        pass

        if transcript is None:
            return None

        segments = transcript.fetch()
        text = " ".join(getattr(seg, "text", "") for seg in segments)
        return text.strip() or None

    except Exception as exc:
        log.debug("Transcript unavailable for %s: %s", video_id, exc)
        return None

# ---------------------------------------------------------------------------
# Content assembly
# ---------------------------------------------------------------------------

def video_content_block(video: dict) -> str:
    """Build the raw-content block we feed to the AI for one video."""
    parts = [
        f"Title: {video['title']}",
        f"Channel: {video['channel']}",
        f"URL: {video['url']}",
    ]
    if video.get("transcript"):
        # Cap individual transcripts to keep prompt manageable
        parts.append(f"Transcript:\n{video['transcript'][:10_000]}")
    elif video.get("description"):
        parts.append(f"Description:\n{video['description']}")
    else:
        parts.append("(No transcript or description available — use the title only.)")
    return "\n".join(parts)

# ---------------------------------------------------------------------------
# AI generation
# ---------------------------------------------------------------------------

def summarise_video(client: anthropic.Anthropic, video: dict, topic_cfg: dict) -> str:
    """Map step: produce a concise summary of a single video."""
    content = video_content_block(video)
    model = topic_cfg.get("summary_model", "claude-sonnet-4-6")

    prompt = textwrap.dedent(f"""
        You are summarising a YouTube video for a daily {topic_cfg['topic']} roundup.

        Write a concise 2–3 paragraph summary in UK English. Capture:
        - Key facts, results, or arguments made
        - Any notable quotes or specific claims
        - Why it matters for today's {topic_cfg['topic']} coverage

        Do NOT add a heading. Just write the prose summary.

        VIDEO:
        {content}
    """).strip()

    resp = client.messages.create(
        model=model,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def generate_roundup(
    client: anthropic.Anthropic,
    videos: list[dict],
    topic_cfg: dict,
    date_str: str,
) -> str:
    """Reduce step: write the full daily roundup from video summaries / raw content."""
    model = topic_cfg.get("roundup_model", "claude-opus-4-8")
    themes = topic_cfg.get("themes", [])
    tone = topic_cfg.get("editorial_tone", "").strip()

    source_blocks = []
    for v in videos:
        if v.get("summary"):
            block = "\n".join([
                f"### {v['title']} ({v['channel']})",
                f"URL: {v['url']}",
                v["summary"],
            ])
        else:
            block = video_content_block(v)
        source_blocks.append(block)

    source_text = "\n\n---\n\n".join(source_blocks)
    themes_list = "\n".join(f"- {t}" for t in themes)

    prompt = textwrap.dedent(f"""
        You are writing the daily {topic_cfg['topic']} roundup for {date_str}.

        EDITORIAL TONE:
        {tone}

        STRUCTURE:
        Write a single cohesive blog post. Organise content under these sections
        using ## headings, in order:
        {themes_list}

        Only include a section if there is genuine content for it today.
        If a theme has nothing to say, skip it entirely.

        RULES:
        - Write in UK English throughout.
        - This is a single narrative piece, NOT a listicle of video summaries. Weave
          information from multiple sources together naturally.
        - Credit source channels inline (e.g. "BBC Sport report that…",
          "according to Tifo Football's analysis…"). Do not add a references section.
        - Link each credited video using Markdown inline links within the relevant
          sentence: [descriptive anchor text](URL).
        - Open with a sharp 2–3 sentence intro paragraph before the first ## heading
          that captures the day in a sentence or two.
        - Be direct. No padding. No "in conclusion". No "it's worth noting".
        - End with a "What's On Tomorrow" section if the material mentions upcoming
          fixtures or events; otherwise omit it.

        SOURCE MATERIAL (from YouTube channels — {date_str}):

        {source_text}

        Write the blog post now. Start directly with the intro paragraph — no title,
        no date header (those go in the frontmatter).
    """).strip()

    resp = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()

# ---------------------------------------------------------------------------
# Post output
# ---------------------------------------------------------------------------

def build_post(content: str, topic_cfg: dict, date: datetime.datetime) -> tuple[str, str]:
    """Return (filename, full_markdown_string)."""
    date_str = date.strftime("%Y-%m-%d")
    slug = f"{date_str}-daily-roundup"
    display_date = date.strftime("%-d %B %Y")

    frontmatter = textwrap.dedent(f"""\
        ---
        title: "{topic_cfg.get('topic', 'Daily Briefing')} — {display_date}"
        date: "{date_str}"
        description: "Everything that happened on {display_date}: match results, team news, talking points."
        ---
    """)

    return f"{slug}.md", f"{frontmatter}\n{content}\n"


def write_or_print(
    post_filename: str,
    post_content: str,
    output_dir: Path,
    dry_run: bool,
) -> Optional[Path]:
    if dry_run:
        divider = "─" * 72
        log.info("DRY RUN — generated post (%d chars):\n%s", len(post_content), divider)
        print(post_content)
        log.info(divider)
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    post_path = output_dir / post_filename
    post_path.write_text(post_content, encoding="utf-8")
    log.info("Written → %s", post_path)
    return post_path

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate daily football blog post")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the generated post to stdout instead of writing to disk")
    parser.add_argument("--window-hours", type=int, default=24,
                        help="How many hours back to scan for new videos (default: 24)")
    parser.add_argument("--config-dir", type=Path, default=None,
                        help="Directory containing channels.yaml and topic.yaml "
                             "(default: repo root, two levels up from this script)")
    args = parser.parse_args()

    config_dir = args.config_dir or (Path(__file__).parent.parent)

    channels_cfg, topic_cfg = load_config(config_dir)
    log.info("Topic: %s", topic_cfg.get("topic", "unknown"))

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    since = now_utc - datetime.timedelta(hours=args.window_hours)
    # The "date" of the post is yesterday in UK time (the day being covered)
    uk_tz = datetime.timezone(datetime.timedelta(hours=1))  # BST approx; good enough for labelling
    post_date = (now_utc - datetime.timedelta(hours=12)).astimezone(uk_tz)

    log.info("Scanning %dh window: %s → %s UTC",
             args.window_hours, since.strftime("%Y-%m-%dT%H:%M"), now_utc.strftime("%Y-%m-%dT%H:%M"))

    # ── 1. Collect new videos from all channels ──────────────────────────────

    all_videos: list[dict] = []
    for ch in channels_cfg.get("channels", []):
        name, cid = ch["name"], ch["channel_id"]
        log.info("Fetching RSS: %s …", name)
        root = fetch_rss(cid, name)
        if root is None:
            log.warning("  Skipping %s — RSS fetch failed", name)
            continue
        entries = parse_entries(root, since, name)
        log.info("  → %d new video(s)", len(entries))
        all_videos.extend(entries)

    if not all_videos:
        log.info("No new videos in the past %dh. Nothing to publish today.", args.window_hours)
        sys.exit(0)

    log.info("Total new videos: %d", len(all_videos))

    # ── 2. Fetch transcripts ─────────────────────────────────────────────────

    for i, video in enumerate(all_videos):
        log.info("Transcript %d/%d: %s", i + 1, len(all_videos), video["title"][:70])
        transcript = fetch_transcript(video["video_id"])
        if transcript:
            video["transcript"] = transcript
            log.info("  → %d chars", len(transcript))
        else:
            log.info("  → no transcript; using title + description")
        if i < len(all_videos) - 1:
            time.sleep(TRANSCRIPT_DELAY)

    # ── 3. Initialise Anthropic client ───────────────────────────────────────

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("ANTHROPIC_API_KEY environment variable is not set.")
        sys.exit(1)
    client = anthropic.Anthropic(api_key=api_key)

    # ── 4. Map: per-video summaries if content is very large ─────────────────

    total_chars = sum(
        len(v.get("transcript") or "")
        + len(v.get("description") or "")
        + len(v.get("title") or "")
        for v in all_videos
    )
    log.info("Total raw content: ~%d chars", total_chars)

    if total_chars > SYNTHESIS_CHAR_LIMIT:
        log.info("Content exceeds threshold — running per-video summary pass (map step)")
        for i, video in enumerate(all_videos):
            log.info("Summarising %d/%d: %s", i + 1, len(all_videos), video["title"][:60])
            try:
                video["summary"] = summarise_video(client, video, topic_cfg)
                log.info("  → %d chars", len(video["summary"]))
            except Exception as exc:
                log.warning("  Summary failed: %s — falling back to description", exc)
                video["summary"] = video.get("description") or video["title"]

    # ── 5. Reduce: generate the full roundup ─────────────────────────────────

    date_label = post_date.strftime("%-d %B %Y")
    log.info("Generating roundup for %s …", date_label)
    try:
        roundup = generate_roundup(client, all_videos, topic_cfg, date_label)
    except Exception as exc:
        log.error("Failed to generate roundup: %s", exc)
        sys.exit(1)

    # ── 6. Write / print ─────────────────────────────────────────────────────

    output_dir = config_dir / "blog" / "src" / "content" / "posts"
    post_filename, post_content = build_post(roundup, topic_cfg, post_date)
    write_or_print(post_filename, post_content, output_dir, dry_run=args.dry_run)

    log.info("Done.")


if __name__ == "__main__":
    main()
