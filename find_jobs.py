"""
job-shortlist: find new jobs, filter them with your rules, and shortlist them.

Searches job boards through JobSpy (public listings only, no login), applies the
filters in a YAML config, removes jobs already shown in earlier runs, pre-scores
the rest by keywords, and writes:
  output/<output_prefix>_YYYY-MM-DD.csv   (new, filtered jobs with descriptions)
  output/<output_prefix>_YYYY-MM-DD.html  (clickable list, best pre-score first)

Optional: open Claude Code in this folder and say "score today's jobs" (see CLAUDE.md).

Usage:
  python find_jobs.py                          # full run with config.yaml
  python find_jobs.py --quick                  # 3 terms x 2 locations, for testing
  python find_jobs.py --config my-search.yaml  # another search profile
"""

import argparse
import datetime as dt
import html
import os
import random
import re
import sys
import time

import pandas as pd
import yaml

try:
    from jobspy import scrape_jobs
except ImportError:
    sys.exit("JobSpy not installed. Run:  pip install -U python-jobspy pyyaml pandas")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "output")

LIST_KEYS = ["search_terms", "locations", "sites", "priority_titles", "exclude_title_words",
             "exclude_description_phrases", "exclude_companies", "boost_words",
             "require_title_words", "require_any_words"]
DEFAULTS = {"sites": ["linkedin", "indeed", "naukri"], "hours_old": 72, "results_per_search": 25,
            "min_salary_lpa": 0, "output_prefix": "jobs", "seen_file": "seen_jobs.csv",
            "country": "India", "fetch_linkedin_descriptions": True, "pause_seconds": [3, 6]}


def load_config(name="config.yaml"):
    """Read a config file. Missing or empty sections are treated as empty lists, so a
    deleted filter never crashes the run after a long scrape."""
    path = name if os.path.isabs(name) else os.path.join(HERE, name)
    try:
        with open(path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except FileNotFoundError:
        sys.exit(f"Config file not found: {path}\n"
                 "Run the setup script, or copy config.example.yaml to config.yaml and edit it.")
    except yaml.YAMLError as e:
        sys.exit(f"{name} has a formatting error (check spaces and dashes near the line below):\n{e}")
    for k, v in DEFAULTS.items():
        if cfg.get(k) in (None, "", []):
            cfg[k] = v
    for k in LIST_KEYS:
        v = cfg.get(k) or []
        cfg[k] = [str(w) for w in (v if isinstance(v, list) else [v]) if w is not None]
    missing = [k for k in ("search_terms", "locations") if not cfg[k]]
    if missing:
        sys.exit(f"{name} needs at least one entry under: {', '.join(missing)}")
    cfg["seen_path"] = os.path.join(HERE, cfg["seen_file"])
    p = cfg["pause_seconds"] if isinstance(cfg["pause_seconds"], list) else [cfg["pause_seconds"]]
    lo = max(2.0, float(p[0]))  # never faster than 2s between searches
    cfg["pause"] = (lo, max(lo, float(p[-1])))
    return cfg


def scrape(cfg, quick=False):
    terms = cfg["search_terms"][:3] if quick else cfg["search_terms"]
    locs = cfg["locations"][:2] if quick else cfg["locations"]
    frames = []
    total = len(terms) * len(locs)
    n = 0
    for term in terms:
        for loc in locs:
            n += 1
            is_remote = loc.lower() == "remote"
            print(f"[{n}/{total}] {term} | {loc}")
            counts = []
            for site in cfg["sites"]:  # one call per site, so a blocked site doesn't lose the others
                try:
                    df = scrape_jobs(
                        site_name=site,
                        search_term=term,
                        location=cfg["country"] if is_remote else loc,
                        is_remote=is_remote,
                        results_wanted=cfg["results_per_search"],
                        hours_old=cfg["hours_old"],
                        country_indeed=cfg["country"],
                        linkedin_fetch_description=bool(cfg["fetch_linkedin_descriptions"]),
                        verbose=0,
                    )
                    got = 0 if df is None else len(df)
                    if got:
                        df["search_term"] = term
                        frames.append(df)
                    counts.append(f"{site} {got}")
                except Exception as e:  # one failing site/search shouldn't stop the run
                    counts.append(f"{site} skipped ({type(e).__name__})")
                time.sleep(random.uniform(1, 2))
            print("     " + ", ".join(counts))
            time.sleep(random.uniform(*cfg["pause"]))  # be polite, avoid rate limits
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def col(df, name):
    return df[name].fillna("").astype(str) if name in df.columns else pd.Series([""] * len(df), index=df.index)


def contains_any(text, words):
    t = f" {text.lower()} "
    return any(w.lower() in t for w in words)


def to_lpa(row):
    """Best-effort annual salary in LPA from JobSpy fields (None if unknown)."""
    try:
        amt = row.get("max_amount") or row.get("min_amount")
        if amt in (None, "") or pd.isna(amt):
            return None
        amt = float(amt)
        interval = str(row.get("interval") or "yearly").lower()
        mult = {"yearly": 1, "monthly": 12, "weekly": 52, "daily": 260, "hourly": 2080}.get(interval, 1)
        annual = amt * mult
        cur = str(row.get("currency") or "INR").upper()
        if cur == "USD":
            annual *= 85  # rough
        return round(annual / 100000, 1)
    except Exception:
        return None


def filter_jobs(df, cfg):
    if df.empty:
        return df
    df = df.copy()
    df["title_s"] = col(df, "title")
    df["company_s"] = col(df, "company")
    df["desc_s"] = col(df, "description")

    before = len(df)
    df = df[~df["title_s"].apply(lambda t: contains_any(t, cfg["exclude_title_words"]))]
    df = df[~df["desc_s"].apply(lambda d: contains_any(d, cfg["exclude_description_phrases"]))]
    df = df[~df["company_s"].apply(lambda c: contains_any(c, cfg["exclude_companies"]))]
    if cfg["require_title_words"]:
        df = df[df["title_s"].apply(lambda t: contains_any(t, cfg["require_title_words"]))]
    if cfg["require_any_words"]:
        df = df[(df["title_s"] + " " + df["desc_s"]).apply(lambda t: contains_any(t, cfg["require_any_words"]))]

    df["salary_lpa"] = df.apply(to_lpa, axis=1)
    floor = float(cfg["min_salary_lpa"])
    df = df[df["salary_lpa"].isna() | (df["salary_lpa"] >= floor)]

    # de-duplicate the same job found by several searches/sites
    df["key"] = (df["title_s"].str.lower().str.replace(r"\W+", " ", regex=True).str.strip()
                 + "|" + df["company_s"].str.lower().str.strip())
    df = df.drop_duplicates(subset="key")
    print(f"Filtered {before} -> {len(df)} jobs")
    return df


def drop_seen(df, seen_file):
    if df.empty or not os.path.exists(seen_file):
        return df
    seen = set(pd.read_csv(seen_file)["key"].astype(str))
    new = df[~df["key"].isin(seen)]
    print(f"Removed {len(df) - len(new)} already-seen jobs -> {len(new)} new")
    return new


def remember(df, seen_file):
    if df.empty:
        return
    keep = df[["key"]].copy()
    keep["first_seen"] = dt.date.today().isoformat()
    if os.path.exists(seen_file):
        keep = pd.concat([pd.read_csv(seen_file), keep], ignore_index=True).drop_duplicates("key")
    keep.to_csv(seen_file, index=False)


def prescore(df, cfg):
    def score(row):
        text = f"{row['title_s']} {row['desc_s']}".lower()
        s = sum(1 for w in cfg["boost_words"] if w.lower() in text)
        if any(t.lower() in row["title_s"].lower() for t in cfg["priority_titles"]):
            s += 5
        return s
    df = df.copy()
    df["prescore"] = df.apply(score, axis=1)
    return df.sort_values("prescore", ascending=False)


def write_outputs(df, prefix="jobs"):
    os.makedirs(OUT_DIR, exist_ok=True)
    today = dt.date.today().isoformat()
    cols = ["prescore", "title_s", "company_s", "location", "site", "salary_lpa",
            "date_posted", "job_url", "job_url_direct", "search_term", "desc_s"]
    cols = [c for c in cols if c in df.columns]
    out = df[cols].rename(columns={"title_s": "title", "company_s": "company", "desc_s": "description"})
    csv_path = os.path.join(OUT_DIR, f"{prefix}_{today}.csv")
    out.to_csv(csv_path, index=False)

    rows = []
    for _, r in out.iterrows():
        link = r.get("job_url_direct") or r.get("job_url") or ""
        sal = f"{r['salary_lpa']} LPA" if pd.notna(r.get("salary_lpa")) and r.get("salary_lpa") not in ("", None) else "not listed"
        rows.append(
            f"<tr><td>{r['prescore']}</td><td><a href='{html.escape(str(link))}' target='_blank'>"
            f"{html.escape(str(r['title']))}</a></td><td>{html.escape(str(r['company']))}</td>"
            f"<td>{html.escape(str(r.get('location', '')))}</td><td>{html.escape(str(r.get('site', '')))}</td>"
            f"<td>{sal}</td><td>{html.escape(str(r.get('date_posted', '')))}</td></tr>"
        )
    page = f"""<!doctype html><meta charset="utf-8"><title>Jobs {today}</title>
<style>body{{font-family:system-ui;margin:24px}}table{{border-collapse:collapse;width:100%}}
td,th{{border-bottom:1px solid #ddd;padding:6px 8px;text-align:left;font-size:14px}}th{{background:#f4f4f4}}</style>
<h2>New jobs: {today} ({len(out)})</h2>
<p>Pre-score = keyword match only. Ask Claude Code to "score today's jobs" for real verdicts.</p>
<table><tr><th>Pre-score</th><th>Title</th><th>Company</th><th>Location</th><th>Site</th><th>Salary</th><th>Posted</th></tr>
{''.join(rows)}</table>"""
    html_path = os.path.join(OUT_DIR, f"{prefix}_{today}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"\nSaved:\n  {csv_path}\n  {html_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="small test run")
    ap.add_argument("--config", default="config.yaml", help="config file to use (default config.yaml)")
    args = ap.parse_args()
    cfg = load_config(args.config)
    raw = scrape(cfg, quick=args.quick)
    if raw.empty:
        print("No jobs returned. Try again later (sites may rate-limit) or check your internet.")
        return
    jobs = drop_seen(filter_jobs(raw, cfg), cfg["seen_path"])
    if jobs.empty:
        print("Nothing new since last run.")
        return
    jobs = prescore(jobs, cfg)
    write_outputs(jobs, cfg["output_prefix"])
    remember(jobs, cfg["seen_path"])


if __name__ == "__main__":
    main()
