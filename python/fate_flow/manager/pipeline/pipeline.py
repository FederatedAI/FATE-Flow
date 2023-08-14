from fate_flow.operation.job_saver import JobSaver


def pipeline_dag_dependency(job):
    try:
        component_need_run, dependency = {}, {}
        component_need_run = {}
        tasks = JobSaver.query_task(job_id=job.f_job_id, party_id=job.f_party_id, role=job.f_role, only_latest=True)
        for task in tasks:
            need_run = task.f_component_parameters.get("ComponentParam", {}).get("need_run", True)
            component_need_run[task.f_task_name] = need_run
        dependency["component_need_run"] = component_need_run
        return dependency
    except Exception as e:
        raise e