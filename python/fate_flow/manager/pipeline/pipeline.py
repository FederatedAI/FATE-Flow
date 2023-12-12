from fate_flow.manager.operation.job_saver import JobSaver
from fate_flow.entity.spec.dag import DAGSchema
from fate_flow.controller.parser import JobParser


def pipeline_dag_dependency(job):
    component_list = []
    component_module, dependence_dict, component_need_run, component_stage = {}, {}, {}, {}
    job_parser = JobParser(DAGSchema(**job.f_dag))
    tasks = job.f_dag["dag"].get("tasks")
    for name, components in tasks.items():
        component_list.append(name)
        component_module[name] = components["component_ref"]
        dependence_dict[name] = []

    tasks = JobSaver.query_task(job_id=job.f_job_id, party_id=job.f_party_id, role=job.f_role, only_latest=True)
    for task in tasks:
        need_run = task.f_component_parameters.get("ComponentParam", {}).get("need_run", True)
        component_need_run[task.f_task_name] = need_run
        task_node = job_parser.get_task_node(role=job.f_role, party_id=job.f_party_id, task_name=task.f_task_name)
        component_stage[task.f_task_name] = task_node.stage
        upstream_inputs = task_node.upstream_inputs
        model_type_list = list(upstream_inputs.keys())
        for model_type in model_type_list:
            for data_type in list(upstream_inputs[model_type].keys()):
                data_value = upstream_inputs[model_type][data_type]
                if isinstance(data_value, list):
                    for value in data_value:
                        up_output_info = [value.output_artifact_key]
                        if task.f_task_name == value.producer_task:
                            continue
                        dependence_dict[task.f_task_name].append({
                            "type": data_type,
                            "model_type": model_type,
                            "component_name": value.producer_task if up_output_info else None,
                            "up_output_info": up_output_info,
                            "name": value.name if not up_output_info else None,
                            "name_space": value.name if not up_output_info else None,
                        })
                else:
                    up_output_info = [data_value.output_artifact_key]

                    if task.f_task_name == data_value.producer_task:
                        continue
                    dependence_dict[task.f_task_name].append({
                        "type": data_type,
                        "model_type": model_type,
                        "component_name": data_value.producer_task if up_output_info else None,
                        "up_output_info": up_output_info
                    })
        if not model_type_list:
            dependence_dict[task.f_task_name].append({"up_output_info": []})

    base_dependency = {
        "component_list": component_list,
        "component_stage": component_stage,
        "component_module": component_module,
        "dependencies": dependence_dict
    }

    return base_dependency
