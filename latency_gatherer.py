import time
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import timedelta, datetime
import requests

SERIE = 0


def get_latency(limit=20):

    url = "http://localhost:16686/api/traces"
    now = datetime.now()
    end = int(datetime.timestamp(now)*1000000)
    start = int(datetime.timestamp(now - timedelta(0, 2))*1000000)

    params = dict(
        start=str(start),
        end=str(end),
        limit=limit,
        # loopback='1h',
        service="frontend"
    )
    resp = requests.get(url, params)
    data = resp.json()
    traces = data['data']
    if traces:
        latencies = [max(trace['spans'], key=lambda span: span['duration'])[
            'duration'] for trace in traces]
        avg = sum(latencies) / max(len(latencies), 1)
        return avg
    return 0


def show():
    global SERIE
    start = time.time()
    avg = get_latency()
    end = time.time()
    print(f'{SERIE} interval finished in {end - start} with value {avg}')
    SERIE += 1


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(show, 'interval', seconds=2)
    scheduler.start()
