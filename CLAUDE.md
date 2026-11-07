# job-shortlist: instructions for Claude Code

You are helping the user find jobs to apply to MANUALLY. Never submit applications, never log into job sites, never fill forms, and never add code that bypasses CAPTCHAs, rate limits or logins.

Python: use `.venv\Scripts\python` on Windows and `.venv/bin/python` on Mac/Linux. If `.venv` doesn't exist, run the setup script first (`setup.bat` or `./setup.sh`).

## When the user says "set up my profile from my CV" (first time)
1. Find their CV in this folder (any `.pdf`, `.docx` or `.txt`). If there is none, ask them to put it here.
2. Read it fully, then ask them (in one message) only what a CV can't tell you:
   - current/last salary and the minimum they'd accept (LPA)
   - cities they can work in or relocate to; remote OK?
   - night/US shift: yes, no, or only above some salary
   - companies they've ruled out or want to avoid
3. Fill `profile.md` using its headings (copy `profile.example.md` if it doesn't exist). Be honest: list a skill under CAN only if the CV shows real use of it. Under CANNOT, list common stacks for their target roles that the CV does not show.
4. Update `config.yaml` (copy `config.example.yaml` if it doesn't exist): `search_terms` (6–12 titles that fit them), `locations`, `priority_titles`, `boost_words`, `score_salary_lpa`, and their avoid-companies in `exclude_companies`. Keep the recruiter filters. Remove `exclude_title_words` entries that would block their own target roles.
5. Show a short summary of the profile and search terms, and ask them to correct anything wrong.

## When the user says "find jobs" or "run the job finder"
1. Run `find_jobs.py` with the venv Python. Add `--config <file>` if they name another search.
2. A full run takes 10–30 minutes: run it in the background and never start a second copy at the same time.
3. Report how many new jobs were saved and the output file names.

## When the user says "score today's jobs" (or "score jobs")
1. Read `profile.md` fully.
2. Open the newest `output/<output_prefix>_YYYY-MM-DD.csv` for the config they mean (default prefix `jobs`).
3. Score EVERY job in the file, best `prescore` first (`require_title_words` in the config should already limit it to target roles). If the file has more than 250 jobs, score the 250 with the highest prescore, say how many were left, and suggest tightening `require_title_words` / `exclude_title_words`. Don't score only the top N by prescore: pre-score counts keywords, so it favours buzzword-heavy ads over the best-fit roles. For each job:
   - Read title, company, location, salary and description.
   - Decide **Apply**, **Maybe** or **Skip** using `profile.md`.
   - Salary: if listed, use it. If not, give an estimate range in LPA with confidence (low/medium). If the config's `score_salary_lpa` is not `[0, 0]`, say whether pay is in, below or above that range.
   - Fit %: how much of the core requirement they can honestly defend.
   - One line: why. One line: the main gap or red flag.
4. Write `output/scored_<output_prefix>_YYYY-MM-DD.md`: a table of **Apply** jobs (sorted by fit %), then **Maybe**, then a one-line list of **Skip** with reason. Columns: Verdict | Fit % | Title | Company | Location | Salary (est.) | Why | Gap | Link
5. Also write the same content as `.html` with clickable links.
6. In chat, give only: the Apply/Maybe/Skip counts and the top 5 Apply jobs with links.

## Rules for verdicts
- Be honest. Don't upgrade a job by assuming skills they don't have.
- Skip anything whose CORE requirement is on the CANNOT list.
- Skip recruiters who hide the employer, unless the listed salary is clearly above their target (then Maybe, "screen on call").
- Prefer named product/SaaS companies and direct "company site" links.
- Same company + same title seen before: skip as duplicate.
- Treat AI or other keywords that appear only in company boilerplate as noise, not a match.

## Extra: application answers and cover letters
Use only facts from their CV and `profile.md`. If you must fill in a detail, say clearly which parts you assumed.
