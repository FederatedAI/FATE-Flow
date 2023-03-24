import argparse
from collections import defaultdict
import os
import subprocess
import sys
import json
import base64
import logging

from fate_flow.worker.task_executor import TaskExecutor

logger = logging.getLogger(__name__)


class DeepspeedLauncher:
    def __init__(self, world_info, node_rank, master_addr, master_port, base64_args):
        self.args = json.loads(base64.urlsafe_b64decode(base64_args))
        self.current_env = os.environ.copy()
        if world_info == "None":
            raise ValueError("world_info can not be None")
        world_info = base64.urlsafe_b64decode(world_info)
        world_info = json.loads(world_info)
        node_list = list(world_info.keys())
        nnodes = len(node_list)
        local_node = node_list[node_rank]
        local_gpu_ids = world_info[local_node]
        num_local_procs = len(local_gpu_ids)

        global_rank_mapping = defaultdict(list)
        curr_global_rank = 0
        dist_world_size = 0
        for node_id in node_list:
            gids = world_info[node_id]
            dist_world_size += len(gids)
            for gid in gids:
                global_rank_mapping[node_id].append(curr_global_rank)
                curr_global_rank += 1

        self.current_env["CUDA_VISIBLE_DEVICES"] = ",".join(map(str, local_gpu_ids))
        for k in self.current_env.keys():
            if "NCCL" in k:
                logger.info(f"{node_rank} {k}={self.current_env[k]}")

        # set PyTorch distributed related environmental variables
        self.current_env["MASTER_ADDR"] = master_addr
        self.current_env["MASTER_PORT"] = str(master_port)
        self.current_env["WORLD_SIZE"] = str(dist_world_size)
        self.current_env["CROSS_RANK"] = str(node_rank)
        self.current_env["CROSS_SIZE"] = str(nnodes)
        self.current_env["LOCAL_SIZE"] = str(num_local_procs)
        self.num_local_procs = num_local_procs
        self.global_rank_mapping = global_rank_mapping
        self.local_node = local_node


    def get_cmd(self):
        return [
            sys.executable,
            "-u",
            sys.modules[TaskExecutor.__module__].__file__,
            *self.args,
        ]

    def run(self):
        processes = []
        for local_rank in range(0, self.num_local_procs):
            current_env = self.current_env.copy()
            dist_rank = self.global_rank_mapping[self.local_node][local_rank]
            current_env["RANK"] = str(dist_rank)
            current_env["LOCAL_RANK"] = str(local_rank)
            process = subprocess.Popen(self.get_cmd(), env=current_env)
            processes.append(process)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--world_info")
    parser.add_argument("--node_rank")
    parser.add_argument("--master_addr")
    parser.add_argument("--master_port")
    parser.add_argument("--base64_args")
    args = parser.parse_args()
    DeepspeedLauncher(
        world_info=args.world_info,
        node_rank=args.node_rank,
        master_addr=args.master_addr,
        master_port=args.master_port,
        base64_args=args.base64_args,
    ).run()
