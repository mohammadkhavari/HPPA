from multiprocessing import Pool
from sqlalchemy import create_engine
from kubernetes import client, config, utils
from pprint import pprint
from latency_gatherer import get_latency
from models import Service
from apscheduler.schedulers.blocking import BlockingScheduler
import time

SERVICES = ['profile', 'rate', 'recommendation',
            'reservation', 'search', 'user', 'frontend', 'geo']
SERIE = 0

INTERVAL = 5

# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()

engine = create_engine(
    "postgresql://postgres:password@localhost:5432/metrics")


def save_db_metrics(metrics):
    from sqlalchemy.orm import Session
    with Session(engine) as session:
        session.add_all(metrics)
        session.commit()


def get_metrics():
    services_metrics = {}
    for service in SERVICES:
        services_metrics[service] = []

    api = client.CustomObjectsApi()
    k8s_nodes = api.list_namespaced_custom_object(
        "metrics.k8s.io", "v1beta1", "default", "pods")
    for item in k8s_nodes['items']:
        service = item["metadata"]["labels"]["io.kompose.service"]
        time = item["metadata"]["creationTimestamp"]
        if service in SERVICES:
            for container in item['containers']:
                services_metrics[service].append(
                    {"cpu": container['usage']['cpu'], "memory": container['usage']['memory'], "time": time})
    return services_metrics


def save_metrics():
    start = time.time()
    global SERIE

    if SERIE > 450 / INTERVAL:
        return

    latency_process = pool.apply_async(get_latency, [2])
    # metrics_process = pool.apply_async(get_metrics,[])
    services_metrics = get_metrics()
    latency = latency_process.get(timeout=4)
    # services_metrics = metrics_process.get(timeout=0.5)

    # latency = get_latency(2)

    metrics = []
    for service, pods in services_metrics.items():
        acc_cpu = 0
        acc_mem = 0
        for pod in pods:
            acc_cpu += utils.parse_quantity(pod["cpu"]) * 1000000000
            acc_mem += utils.parse_quantity(pod["memory"])
        metrics.append(Service(latency=latency, cpu=acc_cpu, memory=acc_mem, replicas=len(
            pods), time_serie=SERIE, name=service, time=pods[0]["time"]))
    save_db_metrics(metrics)
    end = time.time()
    print(f'{SERIE} interval finished in {end - start}')
    SERIE += 1


if __name__ == "__main__":
    pool = Pool()
    scheduler = BlockingScheduler()
    scheduler.add_job(save_metrics, 'interval', seconds=INTERVAL)
    scheduler.start()
