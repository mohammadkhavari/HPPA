
from sqlalchemy import create_engine
from kubernetes import client, config, utils
from pprint import pprint
from models import Service
from apscheduler.schedulers.blocking import BlockingScheduler

SERVICES = ['profile', 'rate', 'recommendation',
            'reservation', 'search', 'user', 'frontend', 'geo']
SERIE = 0

# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()

# v1 = client.CoreV1Api()
# print("Listing pods with their IPs:")
# ret = v1.list_pod_for_all_namespaces(watch=False)
# for i in ret.items:
#     print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))


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
    print(k8s_nodes.keys())
    for item in k8s_nodes['items']:
        service = item["metadata"]["labels"]["io.kompose.service"]
        time = item["metadata"]["creationTimestamp"]
        if service in SERVICES:
            for container in item['containers']:
                services_metrics[service].append(
                    {"cpu": container['usage']['cpu'], "memory": container['usage']['memory'], "time": time})
    return services_metrics


def save_metrics():
    services_metrics = get_metrics()
    metrics = []
    for service, pods in services_metrics.items():
        acc_cpu = 0
        acc_mem = 0
        for pod in pods:
            acc_cpu += utils.parse_quantity(pod["cpu"])
            acc_mem += utils.parse_quantity(pod["memory"])
        metrics.append(Service(cpu=acc_cpu, memory=acc_mem, replicas=len(
            pods), time_serie=SERIE, name=service, time=pods[0]["time"]))
    save_db_metrics(metrics)
    SERIE += 1


pprint(get_metrics())


scheduler = BlockingScheduler()
scheduler.add_job(save_metrics, 'interval', seconds=2)
scheduler.start()
