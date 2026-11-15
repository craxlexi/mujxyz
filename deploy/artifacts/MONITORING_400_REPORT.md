# 400-account monitoring simulation — 14 November 2026

**Simulation passed. This is not a live 400-student SLCM test.** Only three real accounts were connected; the user confirmed simulation scope.

## Method

Executed the deployed worker code on the same 1-vCPU/1-GB VPS, alongside the production services. A separate temporary SQLite database contained 400 synthetic, non-demo accounts, encrypted synthetic credentials, baseline snapshots and synthetic push subscriptions. Every account was due at the same time.

Only the SLCM fetch and external web-push transports were mocked. Database claims, the two-poller executor, successful snapshot persistence, change detection, transactional events/outbox, failure scheduling, push retry handling and worker cleanup used the real application code.

Each synthetic SLCM fetch waited **one second** before succeeding or failing. This is an assumption, not a measured SLCM response time. No real SLCM or push-provider traffic was sent by the test.

## Results

| Check | Result |
| --- | --- |
| Accounts refreshed successfully | 400 / 400 |
| Unique change events | 400 |
| Synthetic notifications delivered | 400 / 400 |
| Peak simultaneous portal checks | 2 |
| Overlapping checks for the same account | 0 |
| Injected transient portal failures | 20 |
| Total portal attempts | 420 |
| Injected transient push failures | 8 |
| Total push attempts | 408 |
| First pass observed complete | 210.05s |
| All successful snapshots observed | 230.06s |
| All notifications observed delivered / test finished | 290.08s |
| Test-process peak RSS | 59.7 MiB |

Progress was sampled every ten seconds, so reported completion times include up to about ten seconds of observation delay. The temporary database setup occurred before the timed worker run.

All 20 portal failures retained their previous snapshots and received future retry dates. To test recovery promptly, their due times were explicitly brought forward in the **test database** after the initial pass. Their normal one-hour backoff was not waited out. All eight push failures retried naturally through the existing retry schedule.

Assertions verified exact snapshot contents, event and delivery counts, cleared leases/failure counters, the two-check limit, no overlapping same-account jobs, private notification payloads, SQLite integrity and foreign-key consistency.

## Production check and cleanup

- Temporary 400-account database removed automatically.
- Production database was not used for fixtures. Three real connected accounts remain; database integrity is `ok`.
- Production API, worker and Caddy remained active, with no service restarts.
- Local production API health returned HTTP 200 after the test.

Probe source: `../production/monitoring_probe.py`. Raw metrics/progress: `monitoring-400-results.json`.

## Interpretation and limits

The actual worker successfully handled a 400-account due-job batch, persisted changes and recovered from injected failures on this VPS. Two pollers process a batch progressively; they do not finish all accounts at the same instant.

This validates the queue and persistence pipeline under the stated synthetic latency. It does not establish actual SLCM throughput, portal throttling, concurrent session behavior, response parsing at scale, real push-provider delivery capacity, browser traffic during the batch or long-term stability. Real 400-student monitoring still requires 400 independently authorized connected accounts. Duplicating the three existing students' credentials would not provide a valid test.
