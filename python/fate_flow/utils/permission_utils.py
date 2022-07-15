from fate_flow.db.component_registry import ComponentRegistry
from fate_flow.entity.permission_parameters import DataSet
from fate_flow.hook.common.parameters import PermissionCheckParameters
from fate_flow.utils import schedule_utils, job_utils


def get_permission_parameters(role, party_id, src_role, src_party_id, job_info) -> PermissionCheckParameters:
    dsl = job_info['dsl']
    runtime_conf = job_info['runtime_conf']
    train_runtime_conf = job_info['train_runtime_conf']

    dsl_parser = schedule_utils.get_job_dsl_parser(
        dsl=dsl,
        runtime_conf=runtime_conf,
        train_runtime_conf=train_runtime_conf
    )
    provider_detail = ComponentRegistry.REGISTRY
    job_providers = dsl_parser.get_job_providers(provider_detail=provider_detail)
    component_parameters = job_utils.get_component_parameters(job_providers, dsl_parser, provider_detail, role, int(party_id))
    dataset_dict = job_utils.get_job_dataset(False, role, int(party_id), runtime_conf.get("role"), dsl_parser.get_args_input())

    dataset_list = []
    if dataset_dict.get(role, {}).get(int(party_id)):
        for _, v in dataset_dict[role][int(party_id)].items():
            dataset_list.append(DataSet(namespace=v.split('.')[0], name=v.split('.')[1]))
    component_list = job_utils.get_job_all_components(dsl)
    return PermissionCheckParameters(
        src_role=src_role,
        src_party_id=src_party_id,
        role=role,
        party_id=party_id,
        initiator=runtime_conf['initiator'],
        roles=runtime_conf['role'],
        component_list=component_list,
        dataset_list=dataset_list,
        runtime_conf=runtime_conf,
        dsl=dsl,
        component_parameters=component_parameters
    )
