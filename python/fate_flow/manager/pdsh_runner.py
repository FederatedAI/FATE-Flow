import base64
import json
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
            node_info
    ):
        env["PDSH_RCMD_TYPE"] = "ssh"
        master_addr, active_workers, world_info = self.node_voting(node_info)
        world_info_base64 = base64.urlsafe_b64encode(json.dumps(world_info).encode("utf-8")).decode("utf-8")
        master_port = self.generate_master_port(master_addr)

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
        return pdsh_cmd_args + deepspeed_launch, env, master_addr, world_info

    @staticmethod
    def node_voting(node_info):
        world_info = {}
        master_addr = node_info[0][0]
        for node in node_info:
            if node[0] not in world_info:
                world_info[node[0]] = [node[1]]
            else:
                world_info[node[0]].append(node[1])
        return master_addr, ",".join(world_info.keys()), world_info

    @staticmethod
    def get_kill_cmd(active_workers, worker_id):
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

    @staticmethod
    def get_model_sync_cmd(active_workers, path):
        import os
        os.makedirs(os.path.dirname(path))
        pdcp_cmd_args =[
            PDSH.get("pdcp"),
            "-w",
            active_workers,
            "-r",
            path,
            path
        ]
        return pdcp_cmd_args

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
