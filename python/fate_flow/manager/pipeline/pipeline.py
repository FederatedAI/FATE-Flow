from fate_flow.manager.operation.job_saver import JobSaver
from fate_flow.entity.spec.dag import DAGSchema
from fate_flow.controller.parser import JobParser
from fate_flow.utils import job_utils


def pipeline_dag_dependency(job):
    component_list = []
    component_module, dependence_dict, component_stage = {}, {}, {}
    job_parser = JobParser(DAGSchema(**job.f_dag))
    task_list = job_parser.party_topological_sort(role=job.f_role, party_id=job.f_party_id)
    for task_name in task_list:
        task_node = job_parser.get_task_node(role=job.f_role, party_id=job.f_party_id, task_name=task_name)
        parties = job_parser.get_task_runtime_parties(task_name=task_name)
        need_run = job_utils.check_party_in(job.f_role, job.f_party_id, parties)
        if not need_run:
            continue
        component_list.append(task_name)
        component_module[task_name] = task_node.component_ref
        dependence_dict[task_name] = []

        component_stage[task_name] = task_node.stage
        upstream_inputs = task_node.upstream_inputs
        model_type_list = list(upstream_inputs.keys())
        for model_type in model_type_list:
            for data_type in list(upstream_inputs[model_type].keys()):
                data_value = upstream_inputs[model_type][data_type]
                if isinstance(data_value, list):
                    for value in data_value:
                        up_output_info = [value.output_artifact_key]
                        if task_name == value.producer_task:
                            continue
                        dependence_dict[task_name].append({
                            "type": data_type,
                            "model_type": model_type,
                            "component_name": value.producer_task if up_output_info else None,
                            "up_output_info": up_output_info
                        })
                else:
                    up_output_info = [data_value.output_artifact_key]

                    if task_name == data_value.producer_task:
                        continue
                    dependence_dict[task_name].append({
                        "type": data_type,
                        "model_type": model_type,
                        "component_name": data_value.producer_task if up_output_info else None,
                        "up_output_info": up_output_info
                    })
        if not model_type_list:
            dependence_dict[task_name].append({"up_output_info": []})

    base_dependency = {
        "component_list": component_list,
        "component_stage": component_stage,
        "component_module": component_module,
        "dependencies": dependence_dict
    }

    return base_dependency
