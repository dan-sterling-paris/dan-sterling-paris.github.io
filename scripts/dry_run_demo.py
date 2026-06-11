#!/usr/bin/env python3
"""
dry_run_demo.py — injects mock video data to test the AI generation layer
without needing live YouTube access.

Run:  ANTHROPIC_API_KEY=sk-... python scripts/dry_run_demo.py
"""
import os, sys, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Patch generate_post to skip the real RSS step
import generate_post as gp
import yaml

REPO_ROOT = Path(__file__).parent.parent

_, topic_cfg = gp.load_config(REPO_ROOT)

MOCK_VIDEOS = [
    {
        "video_id": "demo1",
        "title": "2026 World Cup Opening Ceremony Highlights",
        "channel": "FIFA",
        "url": "https://www.youtube.com/watch?v=demo1",
        "published": datetime.datetime.now(datetime.timezone.utc),
        "description": "Official highlights of the 2026 FIFA World Cup opening ceremony at MetLife Stadium, New Jersey.",
        "transcript": (
            "Welcome to the 2026 FIFA World Cup. Tonight's opening ceremony at MetLife Stadium "
            "drew 82,000 fans as hosts USA, Canada and Mexico kick off the expanded 48-team tournament. "
            "The ceremony lasted 90 minutes and featured performances from top artists. "
            "FIFA president Gianni Infantino declared the tournament open to tremendous applause. "
            "The opening match kicks off tomorrow with Mexico facing off in the first group stage game. "
            "Security was tight around the stadium with significant police presence throughout. "
            "This is the largest FIFA World Cup ever held in terms of teams and host cities, "
            "with 16 cities across three countries staging matches over the next four weeks."
        ),
        "summary": None,
    },
    {
        "video_id": "demo2",
        "title": "England's World Cup Squad Arrives — Gareth Southgate Press Conference",
        "channel": "BBC Sport",
        "url": "https://www.youtube.com/watch?v=demo2",
        "published": datetime.datetime.now(datetime.timezone.utc),
        "description": "Gareth Southgate addresses the media as England arrive at their New York base camp.",
        "transcript": (
            "England manager Gareth Southgate confirmed the squad have arrived in New York and training "
            "begins tomorrow morning. When asked about Jude Bellingham's fitness, Southgate said he is "
            "fully fit and ready to go. Harry Kane spoke briefly and said the squad is the most "
            "prepared he's seen an England team going into a major tournament. Southgate confirmed "
            "that Bukayo Saka will start in the first group game against Serbia on Saturday. "
            "There were some questions about Trent Alexander-Arnold's form after a difficult end "
            "to the season at Real Madrid, but Southgate backed him to perform. Kyle Walker has "
            "been named club captain for the tournament in the absence of an official announcement. "
            "Asked about the pressure after reaching the Euro 2020 and Euro 2024 finals, "
            "Southgate said 'this squad knows how to handle big occasions.'"
        ),
        "summary": None,
    },
    {
        "video_id": "demo3",
        "title": "TACTICAL BREAKDOWN: How Spain Plan to Win the 2026 World Cup",
        "channel": "Tifo Football",
        "url": "https://www.youtube.com/watch?v=demo3",
        "published": datetime.datetime.now(datetime.timezone.utc),
        "description": "Tifo Football breaks down Spain's tactical system ahead of the 2026 World Cup.",
        "transcript": (
            "Spain enter the 2026 World Cup as one of the tactical favourites. Under manager "
            "Luis de la Fuente, they've moved to a 4-3-3 that can shift into a 4-2-3-1 in possession. "
            "The key to their system is Pedri in the number eight role, dictating tempo from deep. "
            "Lamine Yamal on the right wing is the explosive element — he's only 18 but already "
            "operating at an elite level. Spain's pressing triggers are specifically designed to "
            "win the ball in the opponent's half within five seconds. "
            "The interesting tactical question is how they handle opponents who sit deep. "
            "Against Morocco in the qualifiers, they struggled to break through a low block for "
            "the first 60 minutes. The solution was bringing on Morata to hold the line and "
            "using overlapping fullbacks to stretch the shape. Fabian Ruiz provides the engine "
            "in midfield, covering tremendous ground defensively. Their set-piece delivery "
            "from Pedri has also been outstanding — six goals from set pieces in qualifying."
        ),
        "summary": None,
    },
    {
        "video_id": "demo4",
        "title": "Neymar Returns? Brazil's World Cup Squad Drama Explained",
        "channel": "talkSPORT",
        "url": "https://www.youtube.com/watch?v=demo4",
        "published": datetime.datetime.now(datetime.timezone.utc),
        "description": "talkSPORT debate whether Neymar's inclusion in Brazil's World Cup squad was the right call.",
        "transcript": (
            "The biggest story around Brazil's World Cup squad has been the inclusion of Neymar "
            "after his ACL recovery. The talkSPORT panel were divided — Simon Jordan argued it was "
            "a sentimental pick that could disrupt the team's structure, while Andy Goldstein "
            "pointed out that Neymar in his final World Cup is still a massive threat in the "
            "final third. Brazil manager Dorival Junior has not confirmed whether Neymar starts "
            "against Croatia in their opener. Vinicius Junior remains the focal point of Brazil's "
            "attack and there are concerns about how the two will coexist on the left flank. "
            "Rodrygo has been in the best form of his career at Real Madrid and some pundits "
            "feel he should be the automatic starter ahead of Neymar. The panel also discussed "
            "Brazil's defensive vulnerabilities — they conceded 14 goals in qualifying, "
            "their worst record in a decade. Goalkeeper Ederson has been in mixed form."
        ),
        "summary": None,
    },
    {
        "video_id": "demo5",
        "title": "2026 World Cup Schedule & Groups: Everything You Need to Know",
        "channel": "Sky Sports Football",
        "url": "https://www.youtube.com/watch?v=demo5",
        "published": datetime.datetime.now(datetime.timezone.utc),
        "description": "Sky Sports run through the complete 2026 World Cup group stage schedule and key fixtures.",
        "transcript": (
            "Sky Sports presenter David Jones walks through the complete group stage schedule. "
            "Group A sees hosts USA face Wales in their opener in Dallas on June 12th. "
            "Group B is widely regarded as the group of death with France, Argentina, Denmark and Morocco. "
            "France open against Denmark in Los Angeles on June 13th. Argentina play Morocco "
            "in Miami on the same day. "
            "England are in Group C with Serbia, Hungary and Panama — most analysts consider "
            "that a very manageable group for the Three Lions. "
            "Germany face Japan in their first match, which will be a fascinating rematch of "
            "their shock defeat at Qatar 2022. "
            "Brazil and Portugal are in the same half of the draw and could meet in the quarter-finals. "
            "The final is scheduled for Sunday 19th July at MetLife Stadium, New Jersey. "
            "There are 104 matches in total — 12 more than Qatar — with the expanded 48-team format "
            "meaning three teams qualify from each group of four via a best third-place rule."
        ),
        "summary": None,
    },
]

import anthropic

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not set")
    sys.exit(1)

client = anthropic.Anthropic(api_key=api_key)

date_label = "11 June 2026"
print(f"Generating roundup for {date_label} using {len(MOCK_VIDEOS)} mock videos …\n")

roundup = gp.generate_roundup(client, MOCK_VIDEOS, topic_cfg, date_label)
filename, post_content = gp.build_post(roundup, topic_cfg, datetime.datetime(2026, 6, 11))

print("─" * 72)
print(post_content)
print("─" * 72)
print(f"\nGenerated post: {filename}")
