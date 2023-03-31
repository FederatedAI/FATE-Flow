import base64
import json
import os
import subprocess
import sys

from fate_flow.settings import PDSH


class PDSHRunner:
    def __init__(self) -> None:
        ...

    @property
    def launch_module(self):
        return "fate_flow.manager.deepspeed_worker_launcher"

    def get_cmd(
        self,
        env,
        exports,
        base64_args,
    ):
        env["PDSH_RCMD_TYPE"] = "ssh"

        exports_cmd = ""
        for key, val in exports.items():
            exports_cmd += "export {}={}; ".format(key, val)

        world_info_base64 = base64.urlsafe_b64encode(json.dumps(PDSH.get("world_info")).encode("utf-8")).decode("utf-8")
        master_addr = PDSH.get("master_address")
        master_port = PDSH.get("master_port")
        active_workers = PDSH.get("active_workers")

        return [
            PDSH.get("path"),
            "-S",
            "-f",
            "1024",
            "-w",
            active_workers,
            exports_cmd,
            sys.executable,
            "-u",
            "-m",
            self.launch_module,
            f"--world_info={world_info_base64}",
            "--node_rank=%n",
            f"--master_addr={master_addr}",
            f"--master_port={master_port}",
            f"--base64_args={base64_args}",
        ], env
