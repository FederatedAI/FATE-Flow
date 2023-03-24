import base64
import os
import subprocess
import sys


class PDSHRunner:
    def __init__(self) -> None:
        ...

    @property
    def launch_module(self):
        return "fate_flow.manager.deepspeed_worker_launcher"

    def get_cmd(
        self,
        env,
        active_workers,
        exports,
        world_info_base64,
        master_addr,
        master_port,
        base64_args,
    ):
        env["PDSH_RCMD_TYPE"] = "ssh"

        exports_cmd = ""
        for key, val in exports.items():
            if key == "PYTHONPATH":
                val = f"{val}:/Users/sage/FATE/python"
            exports_cmd += "export {}={}; ".format(key, val)
        exports_cmd += "export FATE_PROJECT_BASE=/Users/sage/FATE;"


        return [
            "/usr/local/bin/pdsh",
            "-S",
            "-f",
            "1024",
            "-w",
            active_workers,
            # cmd
            exports_cmd,
            f"cd {os.path.abspath('.')};",
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
