from fate_flow.adapter.bfia.translator.component_spec import BFIAComponentSpec
from fate_flow.adapter.bfia.translator.dsl_translator import Translator
from fate_flow.adapter.bfia.utils.spec.artifact import ArtifactAddress, Engine, S3Address
from fate_flow.adapter.bfia.utils.spec.job import DagSchemaSpec
from fate_flow.adapter.bfia.utils.spec.task import TaskRuntimeEnv, RuntimeComponent, RuntimeConf, Config, SystemConf
from fate_flow.adapter.bfia.wheels.output import OutputMeta
from fate_flow.entity.spec.dag import DataWarehouseChannelSpec, RuntimeTaskOutputChannelSpec, OutputArtifactSpec
from fate_flow.hub.parser import JobParserABC
from fate_flow.hub.parser.fate import TaskParser, JobParser
from fate_flow.manager.service.provider_manager import ProviderManager


class BfiaTaskParser(TaskParser):
    @property
    def need_run(self):
        return self.party_id in self.parties

    @property
    def task_parameters(self):
        return TaskRuntimeEnv(
            runtime=RuntimeComponent(component=RuntimeConf(
                name=self.task_node.component_ref,
                parameter=self.input_parameters,
                input=self.runtime_inputs,
                output=self.runtime_outputs
            )
        ),
            config=Config(inst_id={}, node_id={}, self_role=self.role),
            system=SystemConf(storage="", transport="")
        )

    @property
    def runtime_inputs(self):
        inputs = {}
        for type, upstream_input in self.task_node.upstream_inputs.get(self.role, {}).get(self.party_id, {}).items():
            for key, channel in upstream_input.items():
                if isinstance(channel, DataWarehouseChannelSpec):
                    inputs[key] = ArtifactAddress(name=channel.name, namespace=channel.namespace)
                elif isinstance(channel, RuntimeTaskOutputChannelSpec):
                    metas = OutputMeta.query(
                        job_id=self.job_id, role=self.role, party_id=self.party_id,
                        task_name=channel.producer_task, key=channel.output_artifact_key,
                        type=channel.output_artifact_type_alias
                    )
                    if metas:
                        meta = metas[0]
                        inputs[key] = ArtifactAddress(**meta.f_address)
        return inputs

    @property
    def runtime_outputs(self):
        outputs = {}
        for type, output in self.task_node.outputs.get(self.role, {}).get(self.party_id, {}).items():
            for key, channel in output.items():
                if isinstance(channel, OutputArtifactSpec):
                    if self.role in channel.roles:
                        outputs[key] = self.create_output_address(channel)
        return outputs

    def create_output_address(self, channel: OutputArtifactSpec):
        namespace = f"{self.task_id}"
        name = f"{channel.output_artifact_type_alias}-{channel.output_artifact_key_alias}"
        address = ArtifactAddress(name=namespace, namespace=name)
        engine = Engine(name="s3", address=S3Address(url="s3://abc"))
        meta = dict(
            job_id=self.job_id, role=self.role, node_id=self.party_id, task_name=self.task_name,
            component=self.task_node.component_ref, task_id=self.task_id,
            type=channel.output_artifact_type_alias,  key=channel.output_artifact_key_alias,
            engine=engine.dict(), address=address.dict()
        )
        try:
            OutputMeta.save(**meta)
        except Exception as e:
            raise Exception(f"{e}, {meta}")
        return address

    @property
    def provider(self):
        provider_name = self.task_runtime_conf.get("provider")
        version = self.task_runtime_conf.get("version")
        device = "docker"
        self._provider = ProviderManager.generate_provider_name(provider_name, version, device)
        return self._provider


class BfiaDagParser(JobParser, JobParserABC):
    def check_job_params(self, **kwargs):
        pass

    @property
    def task_parser(self):
        return BfiaTaskParser


def get_dag_parser(dag: DagSchemaSpec) -> BfiaDagParser:
    return BfiaDagParser(translate_bfia_dag_to_dag(dag))


def translate_bfia_dag_to_dag(dag):
    components_desc = {}
    for name, desc in ProviderManager.query_component_description(protocol=dag.kind).items():
        components_desc[name] = BFIAComponentSpec.parse_obj(desc)
    return Translator.translate_bfia_dag_to_dag(dag, components_desc)
