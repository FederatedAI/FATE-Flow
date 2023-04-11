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

        world_info_base64 = base64.urlsafe_b64encode(json.dumps(PDSH.get("world_info")).encode("utf-8")).decode("utf-8")
        master_addr = PDSH.get("master_address")
        master_port = self.generate_master_port(master_addr)
        active_workers = PDSH.get("active_workers")

        pdsh_cmd_args =[
            PDSH.get("path"),
            "-S",
            "-f",
            "1024",
            "-w",
            active_workers
        ]

        exports_cmd = ""
        for key, val in exports.items():
            exports_cmd += "export {}={}; ".format(key, val)
        exports_cmd += "export {}={}; ".format("MASTER_ADDR", master_addr)
        exports_cmd += "export {}={}; ".format("MASTER_PORT", master_port)

        deepspeed_launch = [
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
        ]

        return pdsh_cmd_args + deepspeed_launch, env

    @staticmethod
    def get_kill_cmd(active_workers, worker_id):
        active_workers = PDSH.get("active_workers")
        pdsh_cmd_args =[
            PDSH.get("path"),
            "-S",
            "-f",
            "1024",
            "-w",
            active_workers
        ]
        kill_command = pdsh_cmd_args + [f"pkill -f {worker_id}"]
        return kill_command

    def generate_master_port(self, master_addr):
        import random
        port = random.randint(30000, 60000)
        while True:
            if not self.telnet(master_addr, port):
                return port

    @staticmethod
    def telnet(ip, port):
        import telnetlib
        try:
            telnetlib.Telnet(ip, port, timeout=3)
            return True
        except Exception as e:
            return False
