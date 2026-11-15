# MUJhe ky VPS load test — 14 November 2026

## Scope and setup

- Production VPS: 1 vCPU, 957 MiB RAM, 1 GiB swap, 25 GB disk (83% used).
- One API process, one polling process; each has a 256 MiB service memory limit.
- Other VPS services remained running. Three existing accounts and their polling remained active.
- Inserted 1,000 disposable synthetic users, each with a session, six-course snapshot and 30 history events (30,000 total). Their monitoring was paused and they had no credentials or push subscriptions.
- Generated requests externally from the operator's Windows machine against both the VPS HTTPS API and the actual Vercel app domain. Responses were checked for the expected synthetic account identity, not only HTTP 200.
- Open-loop request ramps: 15 seconds per rate, stopping after p95 exceeded 2 seconds or errors exceeded 1%. Sustained confirmation: 60 seconds. HTTPX timeout: 5 seconds per operation, not a total request deadline. Initial cold-connection run retained separately; later ramp used a warm-up.

## External results

| Path | Target req/s | Duration | Requests | p50 | p95 | Errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct API | 10 | 15s | 150 | 100ms | 394ms | 0 |
| Direct API | 25 | 15s | 375 | 91ms | 266ms | 0 |
| Direct API | 50 | 15s | 750 | 888ms | 1,385ms | 0 |
| Direct API | 100 | 15s + drain | 1,500 | 2,725ms | 9,303ms | 0 |
| Vercel app | 10 | 15s | 150 | 112ms | 261ms | 0 |
| Vercel app | 25 | 15s | 375 | 105ms | 211ms | 0 |
| Vercel app | 50 | 15s + drain | 750 | 1,185ms | 1,991ms | 0 |
| Vercel app | 25 | 60s | 1,500 | 116ms | 349ms | 24 read timeouts (1.6%) |
| Direct API | 25 | 60s | 1,500 | 99ms | 691ms | 0 |
| Vercel app | 10 | 60s | 600 | 109ms | 167ms | 0 |

At 100 req/s offered to the API, completion throughput including drain fell to 41.7 req/s and maximum latency reached 22.4 seconds. This is saturation, despite HTTP 200 responses. The public-app ramp was manually stopped after its 50 req/s stage to avoid repeating the already-established overload.

Cold-run tails were considerably worse (up to 3.4s p95 at 25 req/s); they must not be mistaken for warm steady-state latency. The 25 req/s app-path timeout source is unresolved. Direct API confirmation passed, so the full proxy/network path needs separate diagnosis before claiming the same reliability at that rate.

## Server observations

- No API or worker restarts. Sampled API service memory rose from about 133 MiB to 178 MiB during load, reaching 184 MiB after cleanup and smoke checks; worker stayed around 70–72 MiB.
- During the 90-second window surrounding the 25 req/s app sustain, system CPU busy averaged 39.3%, peaked at 69%; swap-out was zero.
- Across the wider diagnostic window CPU busy reached 100%. This includes a loopback generator sharing the VPS CPU, so that peak alone is not an isolated API CPU measurement.
- Loopback diagnostic: 25 req/s p95 77ms. The 50 req/s loopback stage slowed significantly, but briefly overlapped a warm-up attempt and included generator CPU; use external results for capacity planning.
- SQLite query plan for history: `SCAN events` plus `USE TEMP B-TREE FOR ORDER BY`. Dashboard refresh currently scans the event table and sorts per user. An index on `(user_id, created)` is the first optimization to implement and measure. No production schema or tuning changes were made during this test.

## Interpretation

The frontend refreshes `/api/dashboard` every 10 seconds. Thus 1,000 continuously open dashboards average roughly 100 req/s before manual refreshes, logins or other actions. The current configuration did not handle that rate smoothly.

The app path sustained 10 req/s cleanly in this short run, equivalent to about 100 regularly refreshed dashboards under evenly staggered arrivals. Direct API sustained 25 req/s cleanly. These are observations, not guaranteed user limits. Plan around 75–100 active dashboards until the history-query bottleneck and app-path timeouts are fixed and the same test passes for longer. Registered or idle accounts are a different count.

## Cleanup and smoke checks

- Removed exactly 1,000 test users and their cascading sessions, accounts, snapshots and history records; remaining users: 3, active monitored accounts: 3.
- SQLite `quick_check`: `ok`; foreign-key errors: 0.
- Post-test HTTPS smoke suite: 12 checks passed, including authenticated dashboard, Secure/HttpOnly/SameSite cookie, anonymous denial, authorization, CSRF protection, logout/login and disposable-account cleanup.

## Limits

This measured authenticated dashboard reads with synthetic academic data. It did not measure 1,000 live SLCM accounts, portal throughput, mass signup/login, push fan-out, synchronized refresh bursts, browser rendering or a long soak. Existing real polling continued, but synthetic accounts never contacted SLCM. No other services were stopped. Network results reflect one external client location.

Raw results: `load-results-cold.json`, `load-results.json`, `load-sustained.json`, `load-confirmation.json`. Reusable external probe: `../production/load_probe.py`; it requires disposable sessions matching `MUJ_LOAD_SEED`, which were removed after this run.
