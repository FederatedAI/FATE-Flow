from fate_flow.operation.job_saver import JobSaver
from fate_flow.utils.log_utils import schedule_logger



def pipeline_dag_dependency(job):
    component_list = []
    component_module, dependence_dict, component_need_run = {}, {}, {}

    tasks = job.f_dag["dag"].get("tasks")
    for name, components in tasks.items():
        component_list.append(name)
        component_module[name] = components["component_ref"]
        dependence_dict[name] = []

    for name, components in tasks.items():
        dependence_tasks = components["dependent_tasks"]
        inputs = components.get("inputs", None)
        if 'data' in inputs:
            data_input = inputs["data"]
            for data_key, data_dct in data_input.items():
                for _k, dataset in data_dct.items():
                    if isinstance(dataset, list):
                        dataset = dataset[0]
                    up_component_name = dataset.get("producer_task")
                    # up_pos = component_list.index(up_component_name)
                    # up_component = components[up_pos]
                    # data_name = dataset.split(".", -1)[1]
                    # if up_component.get_output().get("data"):
                    #     data_pos = up_component.get_output().get("data").index(data_name)
                    # else:
                    #     data_pos = 0

                    if data_key == "data" or data_key == "train_data":
                        data_type = data_key
                    else:
                        data_type = "validate_data"

                    dependence_dict[name].append({"component_name": up_component_name,
                                                  "type": data_type,
                                                  "up_output_info": [data_type, 0]})

        input_keyword_type_mapping = {"model": "model",
                                      "isometric_model": "model",
                                      "cache": "cache"}
        for keyword, v_type in input_keyword_type_mapping.items():
            if keyword in inputs:
                input_list = inputs[keyword]
                if not input_list or not isinstance(input_list, dict):
                    continue
                # if isinstance(input_list, list):
                #     input_list = input_list[0]
                for _k, _input in input_list.items():
                    if isinstance(_input, list):
                        _input = _input[0]
                    up_component_name = _input.get("producer_task")
                    if up_component_name == "pipeline":
                        continue
                    # link_alias = _input.split(".", -1)[1]
                    # up_pos = component_list.index(up_component_name)
                    # up_component = self.components[up_pos]
                    # if up_component.get_output().get(v_type):
                    #     dep_pos = up_component.get_output().get(v_type).index(link_alias)
                    # else:
                    dep_pos = 0
                    dependence_dict[name].append({"component_name": up_component_name,
                                                  "type": v_type,
                                                  "up_output_info": [v_type, dep_pos]})

        if not dependence_dict[name]:
            del dependence_dict[name]

    tasks = JobSaver.query_task(job_id=job.f_job_id, party_id=job.f_party_id, role=job.f_role, only_latest=True)
    for task in tasks:
        need_run = task.f_component_parameters.get("ComponentParam", {}).get("need_run", True)
        component_need_run[task.f_task_name] = need_run

    base_dependency = {"component_list": component_list,
                       "dependencies": dependence_dict,
                       "component_module": component_module,
                       "component_need_run": component_need_run }

    return base_dependency
