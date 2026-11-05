# job-shortlist

Find new job listings from several job boards, filter out the noise with your own rules, and get a ranked shortlist. Optionally, have [Claude Code](https://claude.com/claude-code) score every job against your CV with an honest **Apply / Maybe / Skip** verdict.

**You apply manually.** This tool never logs in to any site, never fills forms and never submits applications.

```
search job boards  →  filter (titles, phrases, companies, salary)  →  drop jobs already shown
  →  rank by your keywords  →  output/jobs_<date>.html + .csv  →  (optional) AI scoring vs your CV
```

## Features

- Searches **LinkedIn, Indeed, Naukri and Glassdoor** (public listings, via [JobSpy](https://github.com/speedyapply/JobSpy)).
- Everything is set in one YAML file: titles, cities, how recent, filters and ranking.
- **Must-match filters** for focused searches, e.g. "title has *engineer* and the description mentions *AI*".
- **Several searches side by side**: each config has its own output files and its own memory of jobs already shown.
- **Only new jobs** on each run, so a daily run takes minutes to review.
- A clickable **HTML list** plus a **CSV** with full descriptions (opens in Excel).
- Optional **AI scoring with Claude Code**: fit %, salary estimate, main gap and the reason for each verdict.
- Works on **Windows, Mac and Linux**.

## Responsible use

- **Personal use only.** It reads publicly visible listings, the same ones you'd see in a browser without signing in.
- **You are responsible for following each site's terms of service.** Some job boards don't allow automated access. Use modest settings and run it once a day at most.
- It pauses between searches and runs one search at a time. **Don't** remove the pauses, run several copies at once, or add CAPTCHA solving, proxy rotation or logins. Pull requests that do any of these won't be accepted.
- Don't republish or sell the job data it collects.
- No affiliation with LinkedIn, Indeed, Naukri, Glassdoor or any other site. Names are used only to describe compatibility.
- Provided "as is" under the MIT licence, with no warranty. If a site owner asks for something to be removed, it will be.

## Requirements

- **Python 3.10 or newer**
  - Windows: install from [python.org](https://www.python.org/downloads/) and tick **"Add python.exe to PATH"** on the first installer screen.
  - Mac: `brew install python` or the python.org installer.
- An internet connection.
- Optional: [Claude Code](https://claude.com/claude-code) for profile setup and AI scoring.

## Quick start

### Windows

1. Download this repository (**Code → Download ZIP**), right-click the zip, choose **Extract All**, and open the folder.
2. Double-click **`setup.bat`**. It creates a private Python environment (`.venv`), installs the libraries, and creates your own `config.yaml` and `profile.md`.
   If Windows shows "Windows protected your PC", click **More info → Run anyway**.
3. Right-click `config.yaml` → **Open with → Notepad**. Set your job titles and cities (see [Configuration](#configuration)), then save.
4. Test run (about 2 minutes): click the folder's address bar, type `cmd`, press Enter, then run:
   ```bat
   run.bat --quick
   ```
5. Full run: double-click **`run.bat`**. When it prints `Saved:`, open `output\jobs_<date>.html`.

### Mac / Linux

```bash
git clone https://github.com/<your-username>/job-shortlist.git
```
```bash
cd job-shortlist
```
```bash
./setup.sh
```
Edit `config.yaml`, then test with:
```bash
./run.sh --quick
```
And for a full run:
```bash
./run.sh
```
Results are written to `output/jobs_<date>.html` and `.csv`.

## Configuration

`config.yaml` is your personal copy of [`config.example.yaml`](config.example.yaml). It's in `.gitignore`, so your choices never get committed.

**Formatting rules** (YAML is fussy):
- One item per line: two spaces, a dash, a space, then the text in quotes: `  - "Data Analyst"`
- Use spaces, never Tab.
- Don't delete section names (the words ending in `:`). To turn a filter off, leave it empty: `exclude_companies: []`
- If the file has a mistake, the script stops before searching and names the line.

### Parameter reference

| Parameter | Default | What it does |
|---|---|---|
| `sites` | `linkedin, indeed, naukri` | Job boards to search: `linkedin`, `indeed`, `naukri` (India only), `glassdoor`, `google` (see [Site notes](#site-notes)). Each site is queried separately, so one blocked site doesn't lose the others' results. |
| `country` | `"India"` | Country for Indeed/Glassdoor, and the area searched when a location is `"Remote"`. |
| `hours_old` | `72` | Only jobs posted in the last N hours. `24` = 1 day, `72` = 3 days, `168` = 7 days. |
| `results_per_search` | `25` | Max results per site, per search term, per location. |
| `search_terms` | required | Job titles to search. Every term is searched in every location. |
| `locations` | required | Cities, or `"Remote"`. |
| `require_title_words` | empty (keep all) | Keep a job only if its **title** contains at least one of these. |
| `require_any_words` | empty (keep all) | Keep a job only if its **title or description** contains at least one of these. |
| `exclude_title_words` | see example | Drop a job if its **title** contains any of these. |
| `exclude_description_phrases` | see example | Drop a job if its **description** contains any of these (good for recruiters who hide the employer). |
| `exclude_companies` | empty | Drop jobs from these companies. Partial names work. |
| `min_salary_lpa` | `0` (off) | Drop jobs whose **listed** salary is below this, in lakhs per annum. Jobs with no listed salary (most of them) are always kept. |
| `priority_titles` | empty | A title containing one of these gets **+5** pre-score, so it ranks near the top. |
| `boost_words` | empty | **+1** pre-score for each one found in the title or description. |
| `output_prefix` | `"jobs"` | Output file names: `output/<prefix>_YYYY-MM-DD.csv` and `.html`. |
| `seen_file` | `"seen_jobs.csv"` | Remembers jobs already shown so each run lists only new ones. Use a different file per config. Delete it to start fresh. |
| `fetch_linkedin_descriptions` | `true` | Fetch full LinkedIn descriptions. Slower, but description filters and AI scoring need them. |
| `pause_seconds` | `[3, 6]` | Random pause between searches, in seconds. Minimum 2; higher means fewer blocks. |
| `score_salary_lpa` | `[0, 0]` (off) | Used only by AI scoring: pay outside this range (e.g. `[8, 18]`) is flagged. It is **not** a search filter, because most listings don't show pay. |

**Matching rules:** all word lists are case-insensitive and match anywhere in the text, including inside longer words. The text is padded with a space at each end. So for short words, add spaces: `" ai "` matches "AI" as a word but not "maintain", and `" intern "` matches "Intern" but not "International".

**How long a run takes:** about (terms × locations) × 20–40 seconds. For example, 6 terms × 4 locations ≈ 10–15 minutes.

### Several searches

Keep your everyday search in `config.yaml`, and add focused ones as separate files. [`examples/ai-roles.yaml`](examples/ai-roles.yaml) is a 7-day search for AI engineering roles that uses the must-match filters.

```bat
run.bat --config examples\ai-roles.yaml
```
```bash
./run.sh --config examples/ai-roles.yaml
```

To make your own, copy the example next to `config.yaml` (for example `my-ai-search.yaml`) and edit it. Root-level `.yaml` files other than the example are ignored by git. Give each config its own `output_prefix` and `seen_file`.

## Output

| File | What's in it |
|---|---|
| `output/<prefix>_<date>.html` | Clickable list, best pre-score first: title, company, location, site, salary (if listed), date posted. |
| `output/<prefix>_<date>.csv` | Same jobs with full descriptions, plus links. Opens in Excel or Google Sheets. |
| `seen_*.csv` | Jobs already shown (the run's memory). |

**Pre-score** is a keyword count, not a judgement. Use AI scoring, or your own reading, for the final call.

## AI scoring (optional)

### With Claude Code

[`CLAUDE.md`](CLAUDE.md) tells Claude Code how to work in this folder. Open a terminal in the folder, run `claude`, and type:

| Type this | What happens |
|---|---|
| `set up my profile from my CV` | Put your CV (`.pdf` / `.docx`) in the folder first. Claude reads it, asks a few questions (salary floor, cities, shifts, companies to avoid), fills `profile.md` and tailors `config.yaml`. |
| `find jobs` | Runs the search in the background. |
| `score today's jobs` | For each job: **Apply / Maybe / Skip**, fit %, salary estimate, why and the main gap. Writes `output/scored_<prefix>_<date>.html` and `.md`. |

Claude is instructed to be honest: it won't upgrade a job by assuming skills your CV doesn't show, and it skips roles whose core requirement is on your "can't defend" list.

### Without Claude Code

Upload `output/<prefix>_<date>.csv` and your CV to any AI chat assistant and ask:

> For each job, say Apply / Maybe / Skip based on my CV, with fit %, a salary estimate and the main gap. Be honest. Don't assume skills I don't have.

## Your data stays on your computer

`config.yaml`, `profile.md`, your CV, `output/` and `seen_*.csv` are all in `.gitignore`. Nothing is uploaded anywhere except the search requests themselves.

## Site notes

These depend on the job boards and on JobSpy, and they change over time:

| Site | Status |
|---|---|
| LinkedIn | Works. Sometimes answers `429` (too many requests); wait and run later. |
| Indeed | Works. |
| Glassdoor | Works for India. Salary figures it reports can be unreliable. |
| Naukri | Works, but may start asking for a CAPTCHA after many searches. The run then finds 0 Naukri jobs; try again after a few hours. This tool will not bypass CAPTCHAs. |
| Google Jobs | Often returns nothing, because Google blocks automated searches. |

## Troubleshooting

| You see | Fix |
|---|---|
| `'py' is not recognized` / `Python 3 not found` | Install Python 3.10+ and, on Windows, tick "Add python.exe to PATH". |
| `'setup.bat' is not recognized` | You're in the wrong folder. Run `dir` (Windows) or `ls` (Mac); if there's a folder inside, `cd` into it. |
| `Run setup.bat first.` / `Run ./setup.sh first.` | Run the setup script and wait for "Setup done". |
| `Config file not found` | Run the setup script, or copy `config.example.yaml` to `config.yaml`. |
| `... has a formatting error` | Check the line it names: two spaces, dash, space, quotes. No Tab characters. |
| `needs at least one entry under: search_terms` | Add at least one search term and one location. |
| `No jobs returned` | Internet issue, or every site is limiting you. Try again in an hour. |
| `Nothing new since last run` | No new jobs since the last run. Raise `hours_old`, or delete the config's `seen_file` to see everything again. |
| Mac: `permission denied: ./setup.sh` | Run `chmod +x setup.sh run.sh` once. |

Run only one search at a time. Two at once get you blocked and can overwrite each other's results.

## Contributing

Issues and pull requests are welcome for bug fixes, documentation and new filters. Changes that get around site protections (CAPTCHA solving, proxy rotation, logins, auto-apply) won't be merged.

## Credits

Built on [JobSpy](https://github.com/speedyapply/JobSpy) (MIT), [pandas](https://pandas.pydata.org/) and [PyYAML](https://pyyaml.org/).

## Licence

[MIT](LICENSE)
