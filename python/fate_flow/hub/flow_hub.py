from fate_flow.hub.parser.default import DAGSchema


class FlowHub:
    @staticmethod
    def load_job_parser(dag):
        if isinstance(dag, DAGSchema):
            from fate_flow.hub.parser.default import JobParser
            return JobParser(dag)

    @staticmethod
    def load_task_parser(*args, **kwargs):
        from fate_flow.hub.parser.default import TaskParser
        return TaskParser(*args, **kwargs)
