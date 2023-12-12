import logging
import logging.config
import os

import pydantic
from typing import Optional

_LOGGER_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]


class FlowLogger(pydantic.BaseModel):
    config: dict

    def install(self):
        for _name, _conf in self.config.get("handlers", {}).items():
            if _conf.get("filename"):
                os.makedirs(os.path.dirname(_conf.get("filename")), exist_ok=True)
        logging.config.dictConfig(self.config)

    @classmethod
    def create(
        cls,
        task_log_dir: str,
        job_party_log_dir: Optional[str],
        level: str,
        delay: bool,
        formatters: Optional[dict] = None,
    ):
        return FlowLogger(
            config=LoggerConfigBuilder(
                level, formatters, delay, task_log_dir, job_party_log_dir
            ).build()
        )


class LoggerConfigBuilder:
    def __init__(self, level, formatters, delay, log_base_dir, aggregate_log_base_dir):
        self.version = 1
        self.formatters = formatters
        if self.formatters is None:
            default_format = (
                "[%(levelname)s][%(asctime)-8s][%(process)s][%(module)s.%(funcName)s][line:%(lineno)d]: %(message)s"
            )
            self.formatters = {
                "root": {"format": default_format},
                "component": {"format": default_format},
            }
        self.handlers = {}
        self.filters = {}
        self.loggers = {}
        self.root = {
            "handlers": [],
            "level": level,
        }
        self.disable_existing_loggers = False

        # add loggers
        root_logger_dir = os.path.join(log_base_dir, "root")
        os.makedirs(root_logger_dir, exist_ok=True)
        self._add_root_loggers(
            log_base_dir=root_logger_dir, formatter_name="root", delay=delay
        )

        component_logger_dir = os.path.join(log_base_dir, "component")
        os.makedirs(component_logger_dir, exist_ok=True)
        self._add_component_loggers(
            log_base_dir=component_logger_dir,
            formatter_name="component",
            delay=delay,
            loglevel=level,
        )

        os.makedirs(aggregate_log_base_dir, exist_ok=True)
        self._add_party_id_loggers(
            aggregate_log_base_dir=aggregate_log_base_dir, formatter_name="root", delay=delay
        )

        if aggregate_log_base_dir is not None:
            self._add_aggregate_error_logger(
                aggregate_log_base_dir, formatter_name="root", delay=delay
            )

    def build(self):
        return dict(
            version=self.version,
            formatters=self.formatters,
            handlers=self.handlers,
            filters=self.filters,
            loggers=self.loggers,
            root=self.root,
            disable_existing_loggers=self.disable_existing_loggers,
        )

    def _add_root_loggers(self, log_base_dir, formatter_name, delay):
        for level in _LOGGER_LEVELS:
            handler_name = f"root_{level.lower()}"
            self.handlers[handler_name] = self._create_file_handler(
                level, formatter_name, delay, os.path.join(log_base_dir, level)
            )
            self.root["handlers"].append(handler_name)

    def _add_party_id_loggers(self, aggregate_log_base_dir, formatter_name, delay):
        for level in _LOGGER_LEVELS:
            handler_name = f"root_{level.lower()}"
            self.handlers[handler_name] = self._create_file_handler(
                level, formatter_name, delay, os.path.join(aggregate_log_base_dir, level)
            )
            self.root["handlers"].append(handler_name)

    def _add_aggregate_error_logger(self, log_base_dir, formatter_name, delay):
        # error from all component
        handler_name = "global_error"
        self.handlers[handler_name] = self._create_file_handler(
            "ERROR", formatter_name, delay, os.path.join(log_base_dir, "ERROR")
        )
        self.root["handlers"].append(handler_name)

    def _add_component_loggers(
        self, log_base_dir, formatter_name: str, loglevel: str, delay: bool
    ):
        # basic component logger handlers
        # logger structure:
        #   component/
        #       DEBUG
        #       INFO
        #       WARNING
        #       ERROR
        component_handlers_names = []
        for level in _LOGGER_LEVELS:
            handler_name = f"component_{level.lower()}"
            self.handlers[handler_name] = self._create_file_handler(
                level, formatter_name, delay, os.path.join(log_base_dir, level)
            )
            component_handlers_names.append(handler_name)

        # add profile logger handler
        # logger structure:
        #   component/
        #       PROFILE
        handler_name = "component_profile"
        filter_name = "component_profile_filter"
        self.filters[filter_name] = {
            "name": "fate.arch.computing._profile",
            "()": "logging.Filter",
        }
        self.handlers[handler_name] = self._create_file_handler(
            "DEBUG",
            formatter_name,
            delay,
            os.path.join(log_base_dir, "PROFILE"),
            [filter_name],
        )
        component_handlers_names.append(handler_name)

        # the "fate" name means the logger only log the logs from fate package
        # so, don't change the name or the logger will not work
        self.loggers["fate"] = dict(
            handlers=component_handlers_names,
            level=loglevel,
        )

    @staticmethod
    def _create_file_handler(level, formatter, delay, filename, filters=None):
        return {
            "class": "logging.FileHandler",
            "level": level,
            "formatter": formatter,
            "delay": delay,
            "filename": filename,
            "filters": [] if filters is None else filters,
        }
