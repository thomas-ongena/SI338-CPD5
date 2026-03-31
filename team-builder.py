from pathlib import Path
import csv
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(__file__).parent
ATHLETES_DIR = BASE_DIR / "athletes"
IMAGES_DIR = BASE_DIR / "images" / "athletes"

TEAM_TEMPLATE = BASE_DIR / "team-template.html"
OUTPUT_PATH = BASE_DIR / "index.html"

def html_escape(text: str) -> str:
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )

def build_athlete_options(athletes: dict, selected_id: str | None = None) -> str:
    options = []

    for athlete_id, a in sorted(athletes.items(), key=lambda x: x[1]["name"]):
        selected = " selected" if athlete_id == selected_id else ""
        options.append(
            f'<option value="{athlete_id}"{selected}>{a["name"]}</option>'
        )

    return "\n".join(options)

def choose_default_comparison(athletes: dict):
    DEFAULT_ID = "21615274"

    a = athletes.get(DEFAULT_ID)
    b = athletes.get(DEFAULT_ID)

    if a and b:
        return a, b

    values = list(athletes.values())
    if len(values) >= 2:
        return values[0], values[1]

    return None, None

def gather_all_athlete_stats():
    athletes = {}

    for athlete_dir in ATHLETES_DIR.iterdir():
        if athlete_dir.is_dir():
            stats = build_athlete_stats(athlete_dir.name)
            if stats:
                athletes[athlete_dir.name] = stats

    return athletes

def safe(row, key, default="N/A"):
    val = (row.get(key) or "").strip()
    val = val if val else default
    return html_escape(val)


def parse_date(d):
    try:
        return datetime.strptime(d, "%b %d %Y")
    except Exception:
        return None


def time_to_seconds(t):
    if ":" not in t:
        return None
    t = t.replace("PR", "").strip()
    m, s = t.split(":")
    return int(m) * 60 + float(s)


def is_valid_grade(g):
    try:
        g = int(g)
        return 7 <= g <= 12
    except Exception:
        return False


def read_csv_after_header(path: Path):
    with path.open(encoding="utf-8") as f:
        lines = f.read().splitlines()

    header_idx = next(
        i for i, line in enumerate(lines) if line.startswith("Name,")
    )

    return list(csv.DictReader(lines[header_idx:]))



def build_athlete_stats(athlete_id: str) -> dict:
    athlete_dir = ATHLETES_DIR / athlete_id
    csv_files = list(athlete_dir.glob("*.csv"))
    if not csv_files:
        return {}

    records = read_csv_after_header(csv_files[0])
    if not records:
        return {}

    pr, sr, grade = build_summary(records)

    meets = {}
    for r in records:
        meet = safe(r, "Meet Name")
        place = safe(r, "Overall Place")
        if meet != "N/A" and place.isdigit():
            meets[meet] = int(place)

    return {
        "id": athlete_id,
        "name": safe(records[0], "Name"),
        "grade": grade,
        "sr": sr,
        "pr": pr,
        "profile_pic": f"./images/athletes/{athlete_id}/profile.jpg",
        "meet_count": len(meets),
        "meets": meets,
    }

def build_shared_meet_rows(a, b) -> str:
    shared = set(a["meets"]) & set(b["meets"])
    if not shared:
        return ""

    rows = []
    for meet in sorted(shared):
        rows.append(
            "<tr>"
            f"<td>{meet}</td>"
            f"<td>{a['meets'][meet]}</td>"
            f"<td>{b['meets'][meet]}</td>"
            "</tr>"
        )

    return "\n".join(rows)

def build_player_comparison_html(athletes: dict) -> str:
    a, b = choose_default_comparison(athletes)
    if not a or not b:
        return "<p>Not enough athletes to compare.</p>"

    shared_rows = build_shared_meet_rows(a, b)

    shared_html = ""
    if shared_rows:
        shared_html = f"""
        <div class="shared-meets">
          <h3>Shared Meets</h3>
          <table>
            <thead>
              <tr>
                <th>Meet</th>
                <th>{a['name']} Place</th>
                <th>{b['name']} Place</th>
              </tr>
            </thead>
            <tbody>
              {shared_rows}
            </tbody>
          </table>
        </div>
        """

    return f"""
    <div class="comparison-cards">

      <div class="comparison-card">
        <img src="{a['profile_pic']}" alt="{a['name']} profile picture" />
        <h3>{a['name']}</h3>
        <p>Grade: {a['grade']}</p>
        <p>Season Record: {a['sr']}</p>
        <p>Personal Record: {a['pr']}</p>
        <p>Meets Competed: {a['meet_count']}</p>
      </div>

      <div class="comparison-card">
        <img src="{b['profile_pic']}" alt="{b['name']} profile picture" />
        <h3>{b['name']}</h3>
        <p>Grade: {b['grade']}</p>
        <p>Season Record: {b['sr']}</p>
        <p>Personal Record: {b['pr']}</p>
        <p>Meets Competed: {b['meet_count']}</p>
      </div>

    </div>

    {shared_html}
    """

def build_summary(records):
    dated_rows = []
    pr_secs = None
    pr_str = "N/A"

    for r in records:
        d = parse_date(safe(r, "Date"))
        if d:
            dated_rows.append((d, r))

        secs = time_to_seconds(safe(r, "Time"))
        if secs is not None and (pr_secs is None or secs < pr_secs):
            pr_secs = secs
            pr_str = safe(r, "Time")

    dated_rows.sort(key=lambda x: x[0], reverse=True)

    current_grade = "N/A"
    for _, r in dated_rows:
        g = safe(r, "Grade")
        if is_valid_grade(g):
            current_grade = str(int(g))
            break

    sr_secs = None
    sr_str = "N/A"
    if current_grade != "N/A":
        for r in records:
            g = safe(r, "Grade")
            if not is_valid_grade(g):
                continue
            if str(int(g)) != current_grade:
                continue

            secs = time_to_seconds(safe(r, "Time"))
            if secs is not None and (sr_secs is None or secs < sr_secs):
                sr_secs = secs
                sr_str = safe(r, "Time")

    return pr_str, sr_str, current_grade



def build_athlete_card(athlete_id: str) -> str:
    athlete_dir = ATHLETES_DIR / athlete_id
    csv_files = list(athlete_dir.glob("*.csv"))

    if not csv_files:
        return ""

    records = read_csv_after_header(csv_files[0])
    if not records:
        return ""

    name = safe(records[0], "Name", "Athlete")
    pr, sr, grade = build_summary(records)

    profile_pic = f"./images/athletes/{athlete_id}/profile.jpg"
    athlete_link = f"./athletes/{athlete_id}/index.html"

    return f"""
    <div class="athlete-card"
         data-name="{name}"
         data-grade="{grade}"
         data-sr="{sr}"
         data-pr="{pr}">

      <div class="card-inner">

        <div class="card-front">
          <img
            src="{profile_pic}"
            alt="{name} profile picture"
            class="athlete-photo"
            loading="lazy"
          />
          <h3 class="athlete-name">{name}</h3>
        </div>

        <div class="card-back">
          <h3 class="athlete-name">{name}</h3>
          <p class="athlete-grade">Grade: {grade}</p>
          <p class="athlete-sr">Season Record: {sr}</p>
          <p class="athlete-pr">Personal Record: {pr}</p>

          <a href="{athlete_link}" class="athlete-link">
            View Profile
          </a>
        </div>

      </div>
    </div>
    """



def gather_all_records():
    rows = []

    for athlete_dir in ATHLETES_DIR.iterdir():
        if not athlete_dir.is_dir():
            continue

        csv_files = list(athlete_dir.glob("*.csv"))
        if not csv_files:
            continue

        rows.extend(read_csv_after_header(csv_files[0]))

    return rows


def build_team_accomplishments(rows):
    items = []

    fastest = None
    fastest_row = None
    for r in rows:
        secs = time_to_seconds(safe(r, "Time"))
        if secs is not None and (fastest is None or secs < fastest):
            fastest = secs
            fastest_row = r

    if fastest_row:
        items.append(
            f"<li><strong>Fastest Time:</strong> "
            f"{fastest_row['Name']} — {fastest_row['Time']}</li>"
        )

    best_place = None
    best_place_row = None
    for r in rows:
        p = safe(r, "Overall Place")
        if p.isdigit():
            p = int(p)
            if best_place is None or p < best_place:
                best_place = p
                best_place_row = r

    if best_place_row:
        items.append(
            f"<li><strong>Highest Placement:</strong> "
            f"{best_place_row['Name']} — {best_place} place</li>"
        )

    best_by_grade = {}

    for r in rows:
        g = safe(r, "Grade")
        secs = time_to_seconds(safe(r, "Time"))

        if not is_valid_grade(g) or secs is None:
            continue

        g = int(g)
        if g not in best_by_grade or secs < best_by_grade[g][0]:
            best_by_grade[g] = (secs, r)

    for grade in sorted(best_by_grade):
        _, r = best_by_grade[grade]
        items.append(
            f"<li><strong>Best Grade {grade} Athlete:</strong> "
            f"{r['Name']} — {r['Time']}</li>"
        )

    meet_counts = defaultdict(int)
    for r in rows:
        name = safe(r, "Name")
        meet = safe(r, "Meet Name")
        if name != "N/A" and meet != "N/A":
            meet_counts[name] += 1

    if meet_counts:
        top = max(meet_counts, key=lambda name: meet_counts[name])
        items.append(
            f"<li><strong>Most Meets Competed:</strong> "
            f"{top} — {meet_counts[top]} meets</li>"
        )

    return "\n".join(items)


def build_team_events_rows(rows):
    """
    Build a unique set of team events across all athletes.
    """
    events = {}

    for r in rows:
        meet = safe(r, "Meet Name")
        if meet == "N/A":
            continue

        date = parse_date(safe(r, "Date"))
        place = safe(r, "Overall Place")
        url = safe(r, "Meet Results URL", "")

        place_val = int(place) if place.isdigit() else None

        if meet not in events:
            events[meet] = {
                "date": date,
                "best_place": place_val,
                "url": url,
            }
        else:
            if date and (events[meet]["date"] is None or date < events[meet]["date"]):
                events[meet]["date"] = date

            if place_val is not None:
                cur = events[meet]["best_place"]
                if cur is None or place_val < cur:
                    events[meet]["best_place"] = place_val

            if not events[meet]["url"] and url != "N/A":
                events[meet]["url"] = url

    rows_html = []

    for meet, data in sorted(
        events.items(),
        key=lambda x: x[1]["date"] or datetime.max
    ):
        date_str = (
            data["date"].strftime("%Y-%m-%d")
            if data["date"] else "N/A"
        )

        place_str = (
            f"{data['best_place']} place"
            if data["best_place"] is not None else "N/A"
        )

        link_html = (
            f'<a href="{data["url"]}" target="_blank">View Results</a>'
            if data["url"] and data["url"] != "N/A"
            else "N/A"
        )

        rows_html.append(
            "<tr>"
            f"<td>{meet}</td>"
            f"<td>{date_str}</td>"
            f"<td>{place_str}</td>"
            f"<td>{link_html}</td>"
            "</tr>"
        )

    return "\n".join(rows_html)

def build_team_gallery_images(max_per_athlete=2) -> str:
    image_tags = []

    for athlete_dir in sorted(ATHLETES_DIR.iterdir()):
        if not athlete_dir.is_dir():
            continue

        athlete_id = athlete_dir.name
        images_dir = IMAGES_DIR / athlete_id

        if not images_dir.exists():
            continue

        count = 0
        for img_path in sorted(images_dir.iterdir()):
            if count >= max_per_athlete:
                break

            if not img_path.is_file():
                continue

            name = img_path.name.lower()
            if name in {"profile.jpg", "performance.png"}:
                continue

            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue

            src = f"./images/athletes/{athlete_id}/{img_path.name}"

            image_tags.append(
                f'<img src="{src}" alt="Team event photo" loading="lazy" />'
            )

            count += 1

    return "\n".join(image_tags)

def main():
    cards = []

    for athlete_dir in sorted(ATHLETES_DIR.iterdir()):
        if athlete_dir.is_dir():
            card = build_athlete_card(athlete_dir.name)
            if card:
                cards.append(card)

    cards_html = "\n".join(cards)

    all_records = gather_all_records()
    events_html = build_team_events_rows(all_records)
    accomplishments_html = build_team_accomplishments(all_records)
    gallery_html = build_team_gallery_images()

    athletes = gather_all_athlete_stats()

    a_default, _ = choose_default_comparison(athletes)
    default_id = a_default["id"] if a_default else None

    athlete_options_html = build_athlete_options(
        athletes,
        selected_id=default_id
    )

    comparison_html = build_player_comparison_html(athletes)

    template = TEAM_TEMPLATE.read_text(encoding="utf-8")

    html = template
    html = html.replace("{{TEAM_GALLERY_IMAGES}}", gallery_html)
    html = html.replace("{{ATHLETE_OPTIONS}}", athlete_options_html)
    html = html.replace("{{TEAM_EVENTS_ROWS}}", events_html)
    html = html.replace("{{ATHLETE_CARDS}}", cards_html)
    html = html.replace("{{TEAM_ACCOMPLISHMENTS}}", accomplishments_html)
    html = html.replace("{{PLAYER_COMPARISON}}", comparison_html)

    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print("Team page generated → index.html")

if __name__ == "__main__":
    main()
