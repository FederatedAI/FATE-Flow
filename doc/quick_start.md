### 1. FATE Flow 2.0.0-alpha 部署

#### 1.1 源码获取
##### 1.1.1 从github拉取源码
  - [FATE](https://github.com/FederatedAI/FATE/tree/release-2.0-alpha)
  - [FATE-Flow](https://github.com/FederatedAI/FATE-Flow/tree/release-2.0-alpha)
##### 1.1.2 新建部署目录:
```shell
mkdir -p /data/projects/fate2.0
```
##### 1.1.3 将源码放到部署目录
```shell
  # fate flow
  mv ./FATE-Flow /data/projects/fate2.0/fate_flow
  # fate算法包
  mv ./FATE/python /data/projects/fate2.0/python
```
#### 1.2 依赖
##### 1.2.1 miniconda安装
```shell
wget https://webank-ai-1251170195.cos.ap-guangzhou.myqcloud.com/resources/Miniconda3-py38_4.12.0-Linux-x86_64.sh
#创建python虚拟化安装目录
mkdir -p /data/projects/fate2.0/common/python/venv

#安装miniconda3
bash Miniconda3-py38_4.12.0-Linux-x86_64.sh -b -p /data/projects/fate2.0/common/miniconda3
#创建虚拟化环境
/data/projects/fate2.0/common/miniconda3/bin/python3.8 -m venv /data/projects/fate2.0/common/python/venv
```

##### 1.2.2 依赖安装
```shell
source /data/projects/fate2.0/common/python/venv/bin/activate
cd /data/projects/fate2.0/fate_flow/python
pip install -r requirements.txt
```
详细依赖参考： [requirements.txt](../python/requirements.txt)

#### 1.3 修改配置
#### 1.3.1 配置说明
- 系统配置文件[service_conf.yaml](../conf/service_conf.yaml)说明：
```yaml
force_use_sqlite: 是否强制使用sqlite作为数据库
party_id: 站点id
fateflow:
  host: 服务ip
  http_port: http端口
  grpc_port: grpc端口
  proxy_name: 命令通道服务名，支持rollsite/nginx/osx, 需要在下面的federation中配置具体的地址
database: 数据库连接信息，若未部署mysql，可将force_use_sqlite设置为true
default_engines:
  computing: 计算引擎, 可填:standalone/eggroll/spark
  federation: 通信引擎, 可填:standalone/rollsite/pulsar/rabbitmq/osx
  storage: 存储引擎, 可填:standalone/eggroll
federation: 通信服务详细地址
```
##### 1.3.2 配置修改
- 根据实际部署情况修改系统配置service_conf.yaml
- 修改fate_flow/bin/init_env.sh, 参考如下：
```yaml
export EGGROLL_HOME=/data/projects/fate/eggroll
export PYTHONPATH=/data/projects/fate2.0/python:/data/projects/fate2.0/fate_flow/python:/data/projects/fate/eggroll/python
venv=/data/projects/fate2.0/common/python/venv
export PATH=$PATH:$JAVA_HOME/bin
source ${venv}/bin/activate
```

#### 1.4 服务启停
- init环境变量
    ```shell
    source /data/projects/fate2.0/fate_flow/bin/init_env.sh
    ```
- 启动服务
    ```shell
    sh /data/projects/fate2.0/fate_flow/bin/service.sh start
    ```
- 重启服务
    ```shell
    sh /data/projects/fate2.0/fate_flow/bin/service.sh restart
    ```
- 停止服务
    ```shell
    sh /data/projects/fate2.0/fate_flow/bin/service.sh stop
    ```
- 查询服务状态
    ```shell
    sh /data/projects/fate2.0/fate_flow/bin/service.sh status
    ```

### 2. 使用指南
#### 2.1 数据上传
- 若计算引擎使用standalone，reader组件参数支持配置文件路径，数据无需上传，使用时配置如下：
```yaml
reader_0:
  inputs:
    parameters:
      delimiter: ','
      dtype: float32
      format: csv
      id_name: id
      label_name: y
      label_type: float32
      path: file:///data/projects/fate/fateflow/examples/data/breast_hetero_guest.csv
```
- 若计算引擎使用eggroll，需要先将数据上传至eggroll中，可参考：[eggroll数据上传](../examples/test/data.py)、[上传参数](../examples/upload/upload_guest.json), 使用时配置如下：
```yaml
reader_0:
  inputs:
    parameters:
      path: eggroll:///experiment/guest
      format: raw_table
```
#### 2.2 任务操作
##### 2.2.1 提交任务
- 任务配置参考[dag配置](../examples/lr/standalone/lr_train_dag.yaml)
```python
import requests
from ruamel import yaml

base = "http://127.0.0.1:9380/v2"

def submit_job():
    uri = "/job/submit"
    dag = yaml.safe_load(open("lr_train_dag.yaml", "r"))
    response = requests.post(base+uri,  json={"dag_schema": dag})
    print(response.text)
 ```
##### 2.2.2 查询job
```python
import requests

base = "http://127.0.0.1:9380/v2"

def query_job(job_id):
    uri = "/job/query"
    response = requests.post(base+uri,  json={"job_id": job_id})
    print(response.text)
```
##### 2.2.3 查询task
```python
import requests

base = "http://127.0.0.1:9380/v2"

def query_task(job_id, role, party_id, task_name):
    uri = "/job/task/query"
    response = requests.post(base+uri,  json={"job_id": job_id, "role": role, "party_id": party_id, "task_name": task_name})
    print(response.text)
```

##### 2.2.4 停止任务
```python
import requests

base = "http://127.0.0.1:9380/v2"

def stop_job(job_id):
    uri = "/job/stop"
    response = requests.post(base+uri,  json={"job_id": job_id})
    print(response.text)
```

#### 2.3 输出查询
##### 2.3.1 metric
```python
import requests

base = "http://127.0.0.1:9380/v2"

def metric_query(job_id, role, party_id, task_name):
    uri = "/output/metric/query"
    data = {
        "job_id": job_id,
        "role": role,
        "party_id": party_id,
        "task_name": task_name
    }
    response = requests.get(base+uri,  params=data)
    print(response.text)
```
##### 2.3.2 model
```python
import requests

base = "http://127.0.0.1:9380/v2"

def model_query(job_id, role, party_id, task_name):
    uri = "/output/model/query"
    data = {
        "job_id": job_id,
        "role": role,
        "party_id": party_id,
        "task_name": task_name
    }
    response = requests.get(base+uri,  params=data)
    print(response.text)
```

#### 2.4 算法容器
##### 2.4.1 方案
算法容器化方案参考：[算法容器注册与加载方案](./container.md)

##### 2.4.2 配置
service_conf.yaml中默认配置如下：
```yaml
worker:
  type: native
  docker:
    config:
      base_url: unix:///var/run/docker.sock
    image: ccr.ccs.tencentyun.com/federatedai/fate_algorithm:2.0.0-alpha
    # 容器内路径，一般不需要更改
    fate_root_dir: /data/projects/fate
    # 宿主机路径，根据实际情况填写
    eggroll_conf_dir:
  k8s:
    image: ccr.ccs.tencentyun.com/federatedai/fate_algorithm:2.0.0-alpha
    namespace: fate-10000
```
- 在 2.0.0-alpha 版本中暂不支持算法容器注册功能，只支持固定模式的算法运行方案：`local`、`docker` 或 `k8s`, 由配置 `type` 决定运行模式。
- `worker.type` 支持：`docker`、`k8s`，默认使用非容器模式，即 `native`。
- 容器模式不支持通信组件使用 `standalone`，需更改 `default_engines.federation` 为其他组件。
