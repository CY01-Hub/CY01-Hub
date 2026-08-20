import json
import os
import time
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


USERNAME = os.getenv("GITHUB_USERNAME", "CY01-Hub")
TOKEN = os.getenv("PROFILE_TOKEN", "").strip()

OUTPUT_DIR = Path("assets")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BLUE = "#38BDF8"
BLUE2 = "#2563EB"
PURPLE = "#7C3AED"
BACKGROUND = "#07111F"
PANEL = "#0B1628"
TEXT = "#F8FAFC"
MUTED = "#94A3B8"
GRID = "#1E293B"


def api(url, token=None):

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "CY01-Hub-GitHub-Dashboard",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(
        url,
        headers=headers
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def api_safe(url, token=None, fallback=None):

    try:
        return api(url, token)

    except Exception as error:

        print(f"API request failed: {url}")
        print(error)

        return fallback


def escape(value):

    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def text(
    x,
    y,
    value,
    size=16,
    color=TEXT,
    weight=400,
    anchor="start"
):

    return (
        f'<text x="{x}" y="{y}" '
        f'fill="{color}" '
        f'font-family="Arial, sans-serif" '
        f'font-size="{size}px" '
        f'font-weight="{weight}" '
        f'text-anchor="{anchor}">'
        f'{escape(value)}</text>'
    )


def svg_start(width, height):

    return f'''
<svg
xmlns="http://www.w3.org/2000/svg"
width="{width}"
height="{height}"
viewBox="0 0 {width} {height}"
>

<defs>

<linearGradient
id="background"
x1="0"
y1="0"
x2="1"
y2="1"
>

<stop
offset="0%"
stop-color="#050B14"
/>

<stop
offset="55%"
stop-color="#172554"
/>

<stop
offset="100%"
stop-color="#312E81"
/>

</linearGradient>

<linearGradient
id="accent"
x1="0"
y1="0"
x2="1"
y2="0"
>

<stop
offset="0%"
stop-color="#38BDF8"
/>

<stop
offset="50%"
stop-color="#2563EB"
/>

<stop
offset="100%"
stop-color="#7C3AED"
/>

</linearGradient>

</defs>

<rect
width="100%"
height="100%"
rx="18"
fill="url(#background)"
/>

<rect
x="1"
y="1"
width="{width - 2}"
height="{height - 2}"
rx="18"
fill="none"
stroke="#334155"
/>
'''


def svg_end():

    return "</svg>"


def collect_github_data():

    user = api(
        f"https://api.github.com/users/{USERNAME}"
    )

    repositories = api(
        f"https://api.github.com/users/"
        f"{USERNAME}/repos"
        f"?per_page=100&type=owner&sort=updated"
    )

    repositories = [
        repo
        for repo in repositories
        if not repo.get("fork", False)
    ]

    language_totals = Counter()

    total_stars = 0
    total_forks = 0

    for repository in repositories:

        total_stars += repository.get(
            "stargazers_count",
            0
        )

        total_forks += repository.get(
            "forks_count",
            0
        )

        languages = api_safe(
            repository.get("languages_url"),
            TOKEN,
            {}
        )

        for language, amount in (
            languages or {}
        ).items():

            language_totals[language] += amount

    total_language_bytes = (
        sum(language_totals.values())
        or 1
    )

    languages = []

    for language, amount in (
        language_totals.most_common(6)
    ):

        percentage = (
            amount /
            total_language_bytes
        ) * 100

        languages.append(
            (
                language,
                round(percentage, 1)
            )
        )

    return {

        "followers":
            user.get("followers", 0),

        "following":
            user.get("following", 0),

        "repositories":
            len(repositories),

        "stars":
            total_stars,

        "forks":
            total_forks,

        "languages":
            languages,

        "repositories_raw":
            repositories,

        "updated":
            datetime.now(
                timezone.utc
            ).strftime(
                "%d %b %Y %H:%M UTC"
            )
    }


def generate_status(data):

    width = 1200
    height = 570

    svg = [
        svg_start(width, height)
    ]

    svg.append(
        text(
            48,
            55,
            "CY01-HUB // GITHUB STATUS",
            26,
            BLUE,
            700
        )
    )

    svg.append(
        text(
            48,
            82,
            "Repository-controlled • automatically generated",
            13,
            MUTED
        )
    )

    cards = [

        ("REPOSITORIES", data["repositories"]),

        ("STARS", data["stars"]),

        ("FORKS", data["forks"]),

        ("FOLLOWERS", data["followers"]),

        ("FOLLOWING", data["following"])

    ]

    positions = [
        40,
        270,
        500,
        730,
        960
    ]

    for (label, value), x in zip(
        cards,
        positions
    ):

        svg.append(
            f'''
<rect
x="{x}"
y="110"
width="200"
height="100"
rx="14"
fill="{PANEL}"
stroke="{GRID}"
/>
'''
        )

        svg.append(
            text(
                x + 18,
                140,
                label,
                11,
                MUTED,
                700
            )
        )

        svg.append(
            text(
                x + 18,
                183,
                value,
                30,
                TEXT,
                700
            )
        )

    svg.append(
        text(
            48,
            258,
            "MOST USED LANGUAGES",
            18,
            TEXT,
            700
        )
    )

    language_colors = [
        "#38BDF8",
        "#818CF8",
        "#A78BFA",
        "#22C55E",
        "#F59E0B",
        "#F472B6"
    ]

    y = 300

    for index, (
        language,
        percentage
    ) in enumerate(
        data["languages"]
    ):

        bar_width = max(
            20,
            percentage * 7.2
        )

        svg.append(
            text(
                50,
                y + 15,
                language,
                13,
                TEXT,
                600
            )
        )

        svg.append(
            f'''
<rect
x="190"
y="{y}"
width="720"
height="18"
rx="9"
fill="#111C2E"
/>
'''
        )

        svg.append(
            f'''
<rect
x="190"
y="{y}"
width="{bar_width}"
height="18"
rx="9"
fill="{language_colors[index % len(language_colors)]}"
/>
'''
        )

        svg.append(
            text(
                930,
                y + 15,
                f"{percentage}%",
                13,
                MUTED,
                600
            )
        )

        y += 38

    svg.append(
        f'''
<rect
x="40"
y="515"
width="1120"
height="1"
fill="url(#accent)"
/>
'''
    )

    svg.append(
        text(
            48,
            545,
            f"LAST UPDATED // {data['updated']}",
            11,
            MUTED,
            600
        )
    )

    svg.append(
        svg_end()
    )

    (
        OUTPUT_DIR /
        "github-status.svg"
    ).write_text(
        "\n".join(svg),
        encoding="utf-8"
    )


def get_contributions_from_graphql():

    if not TOKEN:
        return None

    query = """
    query($login:String!) {

      user(login:$login) {

        contributionsCollection {

          contributionCalendar {

            totalContributions

            weeks {

              contributionDays {

                date

                contributionCount

              }

            }

          }

        }

      }

    }
    """

    payload = json.dumps({

        "query": query,

        "variables": {
            "login": USERNAME
        }

    }).encode()

    request = urllib.request.Request(

        "https://api.github.com/graphql",

        data=payload,

        headers={

            "Accept":
                "application/vnd.github+json",

            "Content-Type":
                "application/json",

            "Authorization":
                f"Bearer {TOKEN}",

            "User-Agent":
                "CY01-Hub-GitHub-Dashboard"

        },

        method="POST"
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:

            result = json.loads(
                response.read().decode()
            )

        calendar = (
            result
            .get("data", {})
            .get("user", {})
            .get("contributionsCollection", {})
            .get("contributionCalendar")
        )

        if not calendar:
            return None

        counts = {}

        for week in calendar["weeks"]:

            for day in week[
                "contributionDays"
            ]:

                date = datetime.fromisoformat(
                    day["date"]
                ).date()

                counts[date] = (
                    day["contributionCount"]
                )

        dates = sorted(counts)

        return (
            counts,
            dates[0],
            dates[-1],
            "GitHub contribution calendar"
        )

    except Exception as error:

        print(
            "GraphQL contribution request failed:"
        )

        print(error)

        return None


def get_public_contributions(repositories):

    end = datetime.now(
        timezone.utc
    ).date()

    start = (
        end -
        timedelta(days=364)
    )

    counts = defaultdict(int)

    for repository in repositories[:40]:

        full_name = repository[
            "full_name"
        ]

        url = (

            "https://api.github.com/repos/"
            f"{full_name}/commits"
            f"?author={USERNAME}"
            f"&since={start.isoformat()}T00:00:00Z"
            f"&until={end.isoformat()}T23:59:59Z"
            f"&per_page=100"

        )

        commits = api_safe(
            url,
            TOKEN,
            []
        )

        for commit in (
            commits or []
        ):

            date_string = (
                commit
                .get("commit", {})
                .get("author", {})
                .get("date", "")
            )

            if not date_string:
                continue

            try:

                date = datetime.fromisoformat(
                    date_string.replace(
                        "Z",
                        "+00:00"
                    )
                ).date()

                counts[date] += 1

            except ValueError:

                pass

        time.sleep(0.05)

    return (
        counts,
        start,
        end,
        "Public repository commit activity"
    )


def generate_contributions(data):

    contribution_data = (
        get_contributions_from_graphql()
    )

    if contribution_data is None:

        contribution_data = (
            get_public_contributions(
                data["repositories_raw"]
            )
        )

    counts, start, end, source = (
        contribution_data
    )

    width = 1200
    height = 360

    svg = [
        svg_start(
            width,
            height
        )
    ]

    svg.append(
        text(
            48,
            50,
            "CY01-HUB // CONTRIBUTION ACTIVITY",
            24,
            BLUE,
            700
        )
    )

    svg.append(
        text(
            48,
            75,
            source,
            11,
            MUTED
        )
    )

    cell = 14
    gap = 4

    grid_x = 48
    grid_y = 105

    first_sunday = (
        start -
        timedelta(
            days=(
                start.weekday() + 1
            ) % 7
        )
    )

    max_count = max(
        counts.values(),
        default=1
    )

    for column in range(53):

        for row in range(7):

            date = (
                first_sunday +
                timedelta(
                    days=(
                        column * 7 +
                        row
                    )
                )
            )

            if date > end:
                continue

            count = counts.get(
                date,
                0
            )

            if count == 0:

                fill = "#111C2E"

            else:

                ratio = min(
                    1,
                    count / max_count
                )

                if ratio < 0.25:
                    fill = "#164E63"

                elif ratio < 0.50:
                    fill = "#0E7490"

                elif ratio < 0.75:
                    fill = "#0284C7"

                else:
                    fill = "#38BDF8"

            x = (
                grid_x +
                column * (cell + gap)
            )

            y = (
                grid_y +
                row * (cell + gap)
            )

            svg.append(
                f'''
<rect
x="{x}"
y="{y}"
width="{cell}"
height="{cell}"
rx="3"
fill="{fill}"
/>
'''
            )

    total = sum(
        counts.values()
    )

    svg.append(
        text(
            48,
            255,
            f"VISIBLE ACTIVITY: {total}",
            14,
            TEXT,
            700
        )
    )

    svg.append(
        text(
            48,
            282,
            f"RANGE: {start.strftime('%d %b %Y')} → {end.strftime('%d %b %Y')}",
            12,
            MUTED,
            500
        )
    )

    svg.append(
        text(
            48,
            325,
            "Dashboard generated by CY01-Hub GitHub Actions",
            11,
            MUTED
        )
    )

    svg.append(
        svg_end()
    )

    (
        OUTPUT_DIR /
        "contribution-calendar.svg"
    ).write_text(
        "\n".join(svg),
        encoding="utf-8"
    )


def main():

    print(
        f"Generating dashboard for {USERNAME}"
    )

    data = collect_github_data()

    generate_status(data)

    generate_contributions(data)

    print(
        "Dashboard generation complete."
    )


if __name__ == "__main__":
    main()
