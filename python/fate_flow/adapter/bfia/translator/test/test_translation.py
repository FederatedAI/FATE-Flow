import json
import pathlib
import argparse
import pprint

from fate_client.pipeline.adapters.bfia.translator.component_spec import BFIAComponentSpec
from fate_client.pipeline.adapters.bfia.translator.dag_spec import DagSchemaSpec, BFIADagSpec
from fate_client.pipeline.adapters.bfia.translator.dsl_translator import Translator
from fate_client.pipeline.scheduler.dag_parser import DagParser


def load_component_specs(component_spec_directory):
    files = {
        "HeteroLR": "hetero_lr.json",
        "Intersection": "rsa.json",
        "HeteroSecureBoost": "hetero_sbt.json"
    }

    _component_specs = dict()
    for cpn, file_path in files.items():
        path = pathlib.Path(component_spec_directory).joinpath(file_path)
        with open(path, "r") as fin:
            buf = json.loads(fin.read())

        _component_specs[cpn] = BFIAComponentSpec(**buf)

    return _component_specs


def load_bfia_dag_schema(bfia_dag_path):
    with open(bfia_dag_path, "r") as fin:
        buf = json.loads(fin.read())

    dag_spec = BFIADagSpec(**buf)
    bfia_schema = DagSchemaSpec(kind="bfia", schema_version="2.0.0", dag=dag_spec)

    return bfia_schema


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test translation')
    parser.add_argument("--component_definition_directory", help="directory to load component specs")
    parser.add_argument("--bfia_dag_schema", help="path to load bfia_dag")

    args = parser.parse_args()

    component_specs = load_component_specs(args.component_definition_directory)
    bfia_dag_schema = load_bfia_dag_schema(args.bfia_dag_schema)

    dag_schema = Translator.translate_bfia_dag_to_dag(bfia_dag_schema, component_specs)
    pprint.pprint(dag_schema.dict(exclude_defaults=True))
    print("\n\n\n")

    dag_parser = DagParser()
    dag_parser.parse_dag(dag_schema)
    party_id = "JG0100001100000000"
    print (f"runtime roles on party_id = {party_id} is {dag_parser.get_runtime_roles_on_party('intersect_rsa_1', party_id=party_id)}")
    nodes = list(dag_parser.topological_sort())
    assert nodes == ["intersect_rsa_1", "hetero_secureboost_1"], nodes
    intersect_rsa_1 = dag_parser.get_task_node(nodes[0])
    hetero_secureboost_1 = dag_parser.get_task_node(nodes[1])
    print("########## parameters is : ##########")
    pprint.pprint(intersect_rsa_1.runtime_parameters)
    print("\n")
    pprint.pprint(hetero_secureboost_1.runtime_parameters)
    print ("########## show parameters over #########\n")

    print("########## runtime parties ##########")
    pprint.pprint(intersect_rsa_1.runtime_parties)
    print("\n")
    pprint.pprint(hetero_secureboost_1.runtime_parties)
    print("######### show runtime parties over ##########\n")

    print("########## runtime roles ##########")
    pprint.pprint(intersect_rsa_1.runtime_roles)
    print("\n")
    pprint.pprint(hetero_secureboost_1.runtime_roles)
    print("######### show runtime roles over ##########\n")

    print("########## upstream inputs ##########")
    pprint.pprint(intersect_rsa_1.upstream_inputs)
    print("\n")
    pprint.pprint(hetero_secureboost_1.upstream_inputs)
    print("######### show upstream inputs over ##########\n")

    print("########## component ref ##########")
    pprint.pprint(intersect_rsa_1.component_ref)
    print("\n")
    pprint.pprint(hetero_secureboost_1.component_ref)
    print("######### show component ref over ##########\n")

    print("########## conf ##########")
    pprint.pprint(intersect_rsa_1.conf)
    print("\n")
    pprint.pprint(hetero_secureboost_1.conf)
    print("######### show conf over ##########\n")

    print("########## outputs ##########")
    pprint.pprint(intersect_rsa_1.outputs)
    print("\n")
    pprint.pprint(hetero_secureboost_1.outputs)
    print("######### show outputs over ##########\n")

    pprint.pprint(dag_parser.translate_dag("bfia", "fate", bfia_dag_schema, component_specs=component_specs))
    pprint.pprint(dag_parser.translate_dag("fate", "bfia", dag_schema, component_specs=component_specs))
    """
    translated_bfia_dag_schema = Translator.translate_dag_to_bfia_dag(dag_schema, component_specs)
    print("\n\n\n\n")

    pprint.pprint(translated_bfia_dag_schema.dict(exclude_defaults=True))

    print("\n\n\n\n")
    pprint.pprint(bfia_dag_schema.dict(exclude_defaults=True))
    """
