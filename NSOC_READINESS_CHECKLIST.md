# NSoC Winter Edition: Project Kernel Readiness

This checklist compares the repository with the Project Kernel responsibilities described on the official NSoC Winter Edition website. It is a preparation aid, not an official scoring rubric or guarantee of acceptance.

## What NSoC publicly says about Project Kernel

The official site describes Project Kernel as a path to submit an open-source project to the program. It says project maintainers should:

- Curate issues for contributors with different experience levels.
- Review pull requests and mentor contributors through the codebase.
- Bring a real project where contributions can result in meaningful work.

See the [official NSoC site](https://www.nsoc.in/) and its [project directory](https://www.nsoc.in/projects). The public pages reviewed for this checklist do not publish a weighted selection rubric, a complete project-application form, or a guaranteed acceptance process. Confirm the current submission route and deadline with NSoC before assuming that registration alone submits a project.

## Current public timing

The NSoC site currently describes a 45-day Winter Edition. Its timeline lists registration through November 30, 2026, contributions beginning October 19, 2026, the program ending December 2, 2026, and winners announced December 10, 2026. These dates may change; check the [official site](https://www.nsoc.in/) and ask the organizers whether Project Kernel applications are still being accepted.

The public [registration page](https://www.nsoc.in/register) currently offers account creation. It does not visibly provide a project-submission form, so ask through the official [NSoC Discord](https://discord.gg/bZ47fac2jn) for the correct Project Kernel application process and current deadline.

## Repository readiness checklist

### Project submission and ownership

- [x] Public GitHub repository with an open-source license.
- [x] README identifies the project and links to NSoC without claiming acceptance or official affiliation.
- [ ] Confirm the project-submission workflow, application deadline, and any eligibility requirements with NSoC organizers.
- [ ] Submit a concise project proposal: problem, intended users, current working features, architecture, stack, and what contributors can ship during the program.
- [ ] State who maintains the repository, how contributors contact the maintainer, and expected review availability during the program.

### Contributor-ready issue backlog

- [ ] Publish a small, real backlog before the program starts; do not create misleading or filler tasks to inflate issue counts.
- [ ] Include at least one verified, low-risk onboarding task, a few bounded feature or bug-fix tasks, and one or more deeper tasks appropriate to the available mentoring capacity.
- [ ] For each issue, give context, expected result, scope, acceptance criteria, relevant files, setup/test instructions, and known dependencies.
- [ ] Label difficulty and area consistently, and identify which tasks are open for contributors to claim.
- [ ] Keep issue status current and close or update stale, duplicate, or already-completed tasks.
- [ ] Add screenshots or a short demo of the current application so contributors can understand the product before changing it.

### Engineering and review quality

- [ ] Add automated tests for core flows and make CI fail when required checks fail.
- [ ] Keep linting, syntax checks, and dependency/security checks actionable; a check that always passes after an error does not demonstrate a passing quality gate.
- [ ] Test installation and the main user journey from a clean environment; document exact commands and known limitations.
- [ ] Give contributors a reproducible local setup, sample environment configuration, and safe test data.
- [ ] Review pull requests promptly, explain requested changes, and document acceptance criteria before contributors begin large tasks.
- [ ] Ensure pull requests describe the change, link an issue, and report tests run or not run.

### Trust, privacy, and maintainability

- [ ] Document what resume data is stored locally, what is sent to the Gemini API, retention/deletion behavior, and any relevant user consent or privacy limitations.
- [ ] Keep real resumes, database files, generated reports, API keys, and other sensitive artifacts out of Git; use synthetic examples for demos and tests.
- [ ] Provide a clear demo URL or screenshots, without exposing real user information or secrets.
- [ ] Replace repository placeholders and ensure issue, clone, security-reporting, and project links work.
- [ ] Keep the README claims aligned with the implementation and label planned features as planned rather than complete.

## Gaps visible in this repository

These are observations from the repository as it stands, not claims about NSoC's private evaluation decisions:

1. **The project needs demonstrable, contributor-sized work.** The official Project Kernel description emphasizes issues across experience levels, review, and mentorship. A completed feature list alone does not show a prepared issue backlog or available mentoring.
2. **There is no public contributor backlog yet.** At review time (October 25, 2026), GitHub showed zero open issues and no pull requests. This is not a stated NSoC rejection criterion, but it leaves no visible proof that the repository is ready to receive and mentor contributors. GitHub Discussions are also disabled, so direct contributors to Issues instead.
3. **A CI formatting gate is failing.** The [CI run recorded on October 25, 2026](https://github.com/deepikagandla74/ai-campus-placement-agent/actions/runs/40210888265) failed at `black --check .`, reporting 12 Python files that need formatting; the downstream build/test job was skipped. The separate Docker build passed. Format those files, rerun CI, and address any checks that fail afterward.
4. **Automated test evidence is thin.** The root `test.py` is a manual Gemini API smoke script, not a project test suite, and no `tests/` directory was found. The CI workflow runs syntax/import checks; its lint and security steps are configured not to fail the workflow on findings. Add focused tests and make required checks meaningful.
5. **A public demo is missing from the README.** A reviewer should be able to see the application quickly through a deployed demo or sanitized screenshots/video.
6. **Resume data needs explicit privacy documentation.** The code saves uploaded PDF resumes locally, extracts their text, sends that text as part of a Gemini prompt, and stores the job description and analysis results in SQLite. Explain this data flow, storage locations, deletion/retention behavior, and relevant user consent or limitations in plain language. Use synthetic data in demos.
7. **Some documentation may still overstate completeness.** Verify that described features and setup steps match the current code; prioritize a reliable, repeatable core flow over a long roadmap.
8. **Application timing needs confirmation.** The public program timeline already lists contributions as started on October 19, 2026. Contact NSoC to confirm whether a new Project Kernel can still be added during the active program.

## Recommended next steps

1. Ask NSoC organizers through the official Discord for the Project Kernel application link, deadline, current acceptance requirements, and whether late project onboarding is possible.
2. Prepare a short proposal with the project problem, live demo, tested setup, roadmap for the program period, maintainer availability, and examples of starter/intermediate/advanced issues.
3. Add and verify real contributor issues, then test the complete clone-to-run workflow and CI on a clean environment.
4. Add a privacy/data-flow section and sanitized screenshots or a demo recording.
5. Submit only after the project links, GitHub ownership, tests, and contributor instructions are verified.
