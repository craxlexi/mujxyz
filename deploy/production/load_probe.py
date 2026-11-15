"""Bounded, externally generated dashboard load using disposable fixture sessions."""
import asyncio
import hashlib
import json
import math
import os
import time
from collections import Counter
from pathlib import Path

import httpx


def percentile(values, fraction):
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)] if values else 0


async def stage(client, origin, seed, rate, seconds):
    latencies, statuses = [], Counter()
    started = time.perf_counter()

    async def request(index):
        token = hashlib.sha256(f'{seed}:{index % 1000}'.encode()).hexdigest()
        tick = time.perf_counter()
        try:
            response = await client.get(origin + '/api/dashboard', headers={'Cookie': f'pulse_session={token}'})
            valid = response.status_code == 200 and response.json().get('user', {}).get('email', '').endswith('@load-test.invalid')
            statuses[str(response.status_code) if valid else 'invalid-' + str(response.status_code)] += 1
        except (httpx.HTTPError, ValueError) as error:
            statuses[type(error).__name__] += 1
        latencies.append((time.perf_counter() - tick) * 1000)

    tasks = []
    for index in range(rate * seconds):
        await asyncio.sleep(max(0, started + index / rate - time.perf_counter()))
        tasks.append(asyncio.create_task(request(index)))
    await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - started
    total = len(latencies)
    return {'origin': origin, 'target_rps': rate, 'seconds': seconds, 'requests': total,
            'achieved_rps': round(total / elapsed, 1), 'p50_ms': round(percentile(latencies, .5)),
            'p95_ms': round(percentile(latencies, .95)), 'p99_ms': round(percentile(latencies, .99)),
            'max_ms': round(max(latencies)), 'errors': total - statuses['200'], 'statuses': dict(statuses)}


async def main():
    seed = os.environ['MUJ_LOAD_SEED']
    report = []
    limits = httpx.Limits(max_connections=120, max_keepalive_connections=120)
    async with httpx.AsyncClient(timeout=5, limits=limits, trust_env=False) as client:
        for origin in ['https://api-mujheky.lyaxsh.com', 'https://mujheky.lyaxsh.com']:
            warmup = await stage(client, origin, seed, 10, 5)
            assert warmup['errors'] == 0, 'Warm-up requests failed'
            for rate, seconds in [(10, 15), (25, 15), (50, 15), (100, 15), (100, 60)]:
                result = await stage(client, origin, seed, rate, seconds)
                report.append(result)
                print(json.dumps(result), flush=True)
                Path('deploy/artifacts/load-results.json').write_text(json.dumps(report, indent=2))
                if result['errors'] > result['requests'] * .01 or result['p95_ms'] > 2000:
                    print('Ramp stopped: error rate >1% or p95 >2s.', flush=True)
                    break
                await asyncio.sleep(3)


if __name__ == '__main__':
    assert percentile([1, 2, 3, 4], .95) == 4
    asyncio.run(main())
