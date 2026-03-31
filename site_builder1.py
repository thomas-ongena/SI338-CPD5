import csv
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt

ATHLETE_ID = "21615274"
ATHLETE_NAME = "Garrett Comer"
ATHLETE_URL = f"https://www.athletic.net/athlete/{ATHLETE_ID}/cross-country/"
ATHLETE_PROFILE_PIC = f"../../images/athletes/{ATHLETE_ID}/profile.jpg"
PERFORMANCE_GRAPH = f"../../images/athletes/{ATHLETE_ID}/performance.png"


def build_gallery_images(athlete_id: str, base_dir: Path) -> str:
    images_dir = base_dir / "images" / "athletes" / athlete_id

    if not images_dir.exists():
        return ""

    image_tags = []

    for img_path in sorted(images_dir.iterdir()):
        if not img_path.is_file():
            continue

        if img_path.name.lower() == "profile.jpg" or img_path.name.lower() == "performance.png":
            continue

        if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue

        src = f"../../images/athletes/{athlete_id}/{img_path.name}"


        label = img_path.stem.replace("-", " ").replace("_", " ").title()

        image_tags.append(
            f'<img src="{src}" alt="Race gallery photo: {label}" loading="lazy" />'
        )

    return "\n".join(image_tags)

def seconds_to_time_str(seconds):
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m}:{s:04.1f}"

def generate_performance_graph(records, output_path: Path):
    import re

    def clean_meet_name(name: str) -> str:
        return re.sub(r"\s*\([^)]*\)", "", name).strip()

    data = []

    for r in records:
        meet_raw = safe(r, "Meet Name")
        if meet_raw == "N/A":
            continue

        meet = clean_meet_name(meet_raw)

        date = parse_date(safe(r, "Date"))
        secs = time_to_seconds(safe(r, "Time"))
        grade = safe(r, "Grade")
        place = safe(r, "Overall Place")

        if date is None or secs is None or not is_valid_grade(grade):
            continue

        data.append({
            "meet": meet,
            "date": date,
            "secs": secs,
            "grade": int(grade),
            "place": place,
        })

    data.sort(key=lambda x: x["date"])
    if not data:
        return

    grade_colors = {
        9: "#60a5fa",
        10: "#34d399",
        11: "#fbbf24",
        12: "#f87171",
    }

    x = list(range(len(data)))
    y = [d["secs"] for d in data]

    min_secs = min(y)
    max_secs = max(y)
    padding = 5

    colors = [grade_colors.get(d["grade"], "#9ca3af") for d in data]

    labels = [
        f'{d["meet"]}\n({d["date"].strftime("%Y")})'
        for d in data
    ]

    fig, ax = plt.subplots(figsize=(18, 6))

    bars = ax.bar(x, y, color=colors)

    ax.set_ylim(min_secs - padding, max_secs + padding)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right")

    ax.set_ylabel("Time (seconds)")
    ax.set_title("Performance Progression by Meet")

    ax.margins(x=0.02)

    for bar, d in zip(bars, data):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f'#{d["place"]}',
            ha="center",
            va="bottom",
            fontsize=9,
        )

    fig.subplots_adjust(bottom=0.30)

    fig.savefig(output_path, dpi=150)
    plt.close(fig)


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

def safe(row, key, default="N/A"):
    val = (row.get(key) or "").strip()
    val = val if val else default
    return html_escape(val)


def read_csv_after_header(path: Path):
    with path.open(encoding="utf-8") as f:
        lines = f.read().splitlines()

    header_idx = next(
        i for i, line in enumerate(lines) if line.startswith("Name,")
    )

    reader = csv.DictReader(lines[header_idx:])
    return list(reader)


def time_to_seconds(t):
    if ":" not in t:
        return None
    t = t.replace("PR", "").strip()
    m, s = t.split(":")
    return int(m) * 60 + float(s)


def parse_date(d):
    try:
        return datetime.strptime(d, "%b %d %Y")
    except Exception:
        return None


def build_rows(records):
    rows = []

    for r in records:
        meet = safe(r, "Meet Name")
        if meet == "N/A":
            continue
        date = safe(r, "Date")
        location = "N/A"
        distance = "5K"
        time = safe(r, "Time")
        place = safe(r, "Overall Place")
        grade = safe(r, "Grade")
        url = safe(r, "Meet Results URL", "")

        link = f'<a href="{url}" target="_blank">View Results</a>' if url != "N/A" else "N/A"

        rows.append(
            "<tr>"
            f"<td>{meet}</td>"
            f"<td>{date}</td>"
            f"<td>{location}</td>"
            f"<td>{distance}</td>"
            f"<td>{time}</td>"
            f"<td>{place}</td>"
            f"<td>{grade}</td>"
            f"<td>{link}</td>"
            "</tr>"
        )

    return "\n".join(rows)


def is_valid_grade(g):
    try:
        g = int(g)
        return 7 <= g <= 12
    except ValueError:
        return False

def build_summary(records):
    dated_rows = []
    pr_secs = None
    pr_str = "N/A"

    for r in records:
        d = parse_date(safe(r, "Date"))
        if d:
            dated_rows.append((d, r))

        t_str = safe(r, "Time")
        secs = time_to_seconds(t_str)
        if secs is not None and (pr_secs is None or secs < pr_secs):
            pr_secs = secs
            pr_str = t_str.strip()

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

            t_str = safe(r, "Time")
            secs = time_to_seconds(t_str)
            if secs is not None and (sr_secs is None or secs < sr_secs):
                sr_secs = secs
                sr_str = t_str.strip()

    return pr_str, sr_str, current_grade

def fill_template(template, values):
    for k, v in values.items():
        template = template.replace(f"{{{{{k}}}}}", str(v))
    return template


def main():
    base = Path(__file__).parent
    template_path = base / "player-template.html"
    athlete_out_dir = base / "athletes" / ATHLETE_ID
    out_path = athlete_out_dir / "index.html"
    csv_path = athlete_out_dir / "garrett.csv"

    records = read_csv_after_header(csv_path)

    rows_html = build_rows(records)
    pr, sr, grade = build_summary(records)

    template = template_path.read_text(encoding="utf-8")

    gallery_html = build_gallery_images(ATHLETE_ID, base)


    graph_path = base / "images" / "athletes" / ATHLETE_ID / "performance.png"
    generate_performance_graph(records, graph_path)

    html = fill_template(
        template,
        {
            "NAME": ATHLETE_NAME,
            "ATHLETE_URL": ATHLETE_URL,
            "GRADE": grade,
            "SEASON_RECORD": sr,
            "PERSONAL_RECORD": pr,
            "ATHLETE_PROFILE_PIC": ATHLETE_PROFILE_PIC,
            "PERFORMANCE_GRAPH": PERFORMANCE_GRAPH,
            "ATHLETE_GALLERY_IMAGES": gallery_html,
        },
    )

    html = html.replace("</tbody>", rows_html + "\n</tbody>")

    out_path.write_text(html, encoding="utf-8")
    print("index.html generated")


if __name__ == "__main__":
    main()
