from .client import FlowClient

client = FlowClient()
# create job
client.scheduler.create_job()
client.federated.create_job()
client.federated.start_job()
