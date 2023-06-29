import logging
import os
from typing import Literal

import pydantic
import logging.config


class FlowLogger(pydantic.BaseModel):
    class FlowLoggerMetadata(pydantic.BaseModel):
        basepath: str
        level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    type: Literal["flow"]
    metadata: FlowLoggerMetadata

    def install(self):
        os.makedirs(self.metadata.basepath, exist_ok=True)
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        formatters = {"brief": {"format": "'%(asctime)s %(levelname)-8s %(name)s:%(lineno)s %(message)s'"}}
        handlers = {}
        filters = {}

        def add_file_handler(
            name,
            filename,
            level,
            formater="brief",
            filters=[]
        ):
            handlers[name] = {
                "class": "logging.FileHandler",
                "level": level,
                "formatter": formater,
                "filters": filters,
                "filename": filename
            }

        # add root logger
        root_handlers = []
        root_base_path = os.path.join(self.metadata.basepath, "root")
        os.makedirs(root_base_path, exist_ok=True)
        for level in levels:
            handler_name = f"root_{level.lower()}"
            add_file_handler(
                name=handler_name,
                filename=os.path.join(root_base_path, level),
                level=level,
            )
            root_handlers.append(handler_name)

        # add component logger
        component_handlers = []
        component_base_path = os.path.join(self.metadata.basepath, "component")
        os.makedirs(component_base_path, exist_ok=True)
        filters["components"] = {"name": "fate_flow.components"}
        for level in levels:
            handler_name = f"component_{level.lower()}"
            add_file_handler(
                name=handler_name,
                filename=os.path.join(component_base_path, level),
                level=level,
            )
            component_handlers.append(handler_name)
        component_loggers = {
            "fate_flow.components": dict(
                handlers=component_handlers,
                filters=["components"],
                level=self.metadata.level,
            )
        }

        logging.config.dictConfig(
            dict(
                version=1,
                formatters=formatters,
                handlers=handlers,
                filters=filters,
                loggers=component_loggers,
                root=dict(handlers=root_handlers, level=self.metadata.level),
                disable_existing_loggers=False,
            )
        )