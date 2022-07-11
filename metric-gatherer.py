from operator import contains
from kubernetes import client, config
from pprint import pprint

SERVICES = ['profile', 'rate', 'recommendation', 'reservation', 'search', 'user', 'frontend', 'geo']

# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()

v1 = client.CoreV1Api()
print("Listing pods with their IPs:")
ret = v1.list_pod_for_all_namespaces(watch=False)
for i in ret.items:
    print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))


def get_metrics():
    services_metrics = {}
    for service in SERVICES:
        services_metrics[service] = []

    api = client.CustomObjectsApi()
    k8s_nodes = api.list_namespaced_custom_object("metrics.k8s.io", "v1beta1","default", "pods")
    print(k8s_nodes.keys())
    for item in k8s_nodes['items']:
        service = item["metadata"]["labels"]["io.kompose.service"]
        if service in SERVICES:     
            for container in item['containers']:
                services_metrics[service].append({"cpu" : container['usage']['cpu'], "memory": container['usage']['memory']})
    return services_metrics

pprint(get_metrics())