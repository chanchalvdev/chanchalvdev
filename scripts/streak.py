#!/usr/bin/env python3
"""Render a GitHub contribution streak card (streak.svg) from the public contributions page.

Reads https://github.com/users/<user>/contributions for each year. That page includes
private contributions when "Private contributions" is enabled on the profile, so no
token is needed.
"""
import datetime as dt
import re
import sys
import urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "chanchalvdev"
FIRST_YEAR = int(sys.argv[2]) if len(sys.argv) > 2 else 2021
OUT = sys.argv[3] if len(sys.argv) > 3 else "streak.svg"

C = dict(bg="#0C0C0E", stroke="#4C3FD0", ring="#6E5FE8", fire="#B3AAFF",
         curr_label="#B3AAFF", side_label="#F4F4F5", dates="#9B99A3",
         curr_num="#F4F4F5", side_num="#F4F4F5")


def fetch_year(year):
    url = f"https://github.com/users/{USER}/contributions?from={year}-01-01&to={year}-12-31"
    req = urllib.request.Request(url, headers={"User-Agent": "streak-card"})
    html = urllib.request.urlopen(req, timeout=30).read().decode()
    ids = dict(re.findall(r'data-date="(\d{4}-\d\d-\d\d)" id="([^"]+)"', html))
    tips = {i: n for i, n in re.findall(r'for="([^"]+)"[^>]*>(\d+|No) contribution', html)}
    days = {}
    for date, i in ids.items():
        if date.startswith(str(year)):
            n = tips.get(i, "No")
            days[dt.date.fromisoformat(date)] = 0 if n == "No" else int(n)
    if not days:
        raise SystemExit(f"no data parsed for {year}")
    return days


def fmt(d, with_year=False):
    s = f"{d.strftime('%b')} {d.day}"
    return f"{s}, {d.year}" if with_year else s


def span(a, b, today):
    if a is None:
        return ""
    wy = a.year != today.year or b.year != today.year
    return fmt(a, wy) if a == b else f"{fmt(a, wy)} - {fmt(b, wy)}"


def main():
    today = dt.datetime.now(dt.timezone.utc).date()
    days = {}
    for y in range(FIRST_YEAR, today.year + 1):
        days.update(fetch_year(y))
    days = {d: n for d, n in days.items() if d <= today}
    order = sorted(days)
    total = sum(days.values())
    first = next((d for d in order if days[d]), order[0])

    best, best_s, best_e = 0, None, None
    run, run_s = 0, None
    for d in order:
        if days[d]:
            run_s = d if run == 0 else run_s
            run += 1
            if run > best:
                best, best_s, best_e = run, run_s, d
        else:
            run = 0

    # Current streak: today may still be empty without breaking it.
    end = today if days.get(today) else today - dt.timedelta(days=1)
    cur, d = 0, end
    while days.get(d):
        cur += 1
        d -= dt.timedelta(days=1)
    cur_s = d + dt.timedelta(days=1) if cur else None
    cur_range = span(cur_s, end, today) if cur else fmt(today)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 495 195" width="495" height="195">
<style>
.n{{font:700 28px 'Segoe UI',Ubuntu,sans-serif}}
.l{{font:400 14px 'Segoe UI',Ubuntu,sans-serif}}
.cl{{font:700 14px 'Segoe UI',Ubuntu,sans-serif}}
.d{{font:400 12px 'Segoe UI',Ubuntu,sans-serif}}
</style>
<rect width="495" height="195" rx="4.5" fill="{C['bg']}"/>
<line x1="165" y1="28" x2="165" y2="170" stroke="{C['stroke']}" stroke-width="1"/>
<line x1="330" y1="28" x2="330" y2="170" stroke="{C['stroke']}" stroke-width="1"/>
<g text-anchor="middle">
  <text x="82.5" y="79" class="n" fill="{C['side_num']}">{total:,}</text>
  <text x="82.5" y="115" class="l" fill="{C['side_label']}">Total Contributions</text>
  <text x="82.5" y="145" class="d" fill="{C['dates']}">{fmt(first, True)} - Present</text>

  <circle cx="247.5" cy="71" r="40" fill="none" stroke="{C['ring']}" stroke-width="5"/>
  <rect x="235" y="22" width="25" height="16" fill="{C['bg']}"/>
  <path d="M247.5 19c-3 6-8 9-8 15a8 8 0 0 0 16 0c0-4-2-6-3-9-1 3-3 4-4 4 1-4 0-7-1-10z" fill="{C['fire']}"/>
  <text x="247.5" y="81" class="n" fill="{C['curr_num']}">{cur}</text>
  <text x="247.5" y="138" class="cl" fill="{C['curr_label']}">Current Streak</text>
  <text x="247.5" y="160" class="d" fill="{C['dates']}">{cur_range}</text>

  <text x="412.5" y="79" class="n" fill="{C['side_num']}">{best}</text>
  <text x="412.5" y="115" class="l" fill="{C['side_label']}">Longest Streak</text>
  <text x="412.5" y="145" class="d" fill="{C['dates']}">{span(best_s, best_e, today)}</text>
</g>
</svg>
"""
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"total={total} current={cur} ({cur_range}) longest={best} ({span(best_s, best_e, today)})")


if __name__ == "__main__":
    main()
