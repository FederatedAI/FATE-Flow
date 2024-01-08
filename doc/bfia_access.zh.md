# BFIA接入指南
[BFIA协议](https://github.com/FederatedAI/InterOp)由北京金融科技产业联盟组织，中国银联牵头，联合主要金融机构、电信运营商、互联网公司、科技公司、检测机构、科研院所等60余家单位共同制定的互联互通API接口规范。FATE 2.0版本从Pipeline、调度、通信等几个层面适配此协议，本文将介绍如何以BFIA协议与FATE框架进行联邦学习。

## 1. Pipeline

![pipeline](./images/open_flow/pipeline.png)
pipeline构建FATE的互联互通统一客户端，产生基于FATE 2.0协议的DAG配置。pipeline并不直接调用BFIA协议API，而是调用FATE协议API，在FATE Flow内通过适配器模式转化为BFIA协议运行。


### 1.1 FATE算法
```python
from fate_client.pipeline import FateFlowPipeline
from fate_client.pipeline.components.fate import CoordinatedLR, PSI
from fate_client.pipeline.interface.channel import DataWarehouseChannel


guest = "JG0100001100000010"
host = "JG0100001100000010"
arbiter = "JG0100001100000010"
pipeline = FateFlowPipeline().set_parties(guest=guest, host=host, arbiter=arbiter)
pipeline.set_site_role("guest")
pipeline.set_site_party_id(guest)

psi_0 = PSI("psi_0",
        input_data=[DataWarehouseChannel(dataset_id="experiment#breast_hetero_guest", parties=dict(guest=guest)),
                    DataWarehouseChannel(dataset_id="experiment#breast_hetero_host", parties=dict(host=host))])
lr_0 = CoordinatedLR("lr_0",
                 epochs=10,
                 batch_size=300,
                 optimizer={"method": "SGD", "optimizer_params": {"lr": 0.1}, "penalty": "l2", "alpha": 0.001},
                 init_param={"fit_intercept": True, "method": "zeros"},
                 train_data=psi_0.outputs["output_data"],
                 learning_rate_scheduler={"method": "linear", "scheduler_params": {"start_factor": 0.7,
                                                                                   "total_iters": 100}})

pipeline.add_tasks([psi_0, lr_0])

pipeline.protocol_kind = "bfia"
pipeline.conf.set(
"extra",
dict(initiator={'party_id': guest, 'role': 'guest'})
)
pipeline.guest.conf.set("resources", dict(cpu=-1, disk=-1, memory=-1))
pipeline.hosts[0].conf.set("resources", dict(cpu=-1, disk=-1, memory=-1))
pipeline.compile()
pipeline.fit()

```

### 1.2 银联算法
```python
from fate_client.pipeline import FateFlowPipeline
from fate_client.pipeline.adapters.bfia.components.unionpay.intersection import Intersection
from fate_client.pipeline.adapters.bfia.components.unionpay.hetero_lr import HeteroLR
from fate_client.pipeline.interface import DataWarehouseChannel


pipeline = FateFlowPipeline().set_parties(
    guest="JG0100001100000010",
    host="JG0100001100000010",
    arbiter="JG0100001100000010"
)
pipeline.set_site_role("guest")
pipeline.set_site_party_id("JG0100001100000010")

intersection_0 = Intersection(
    "intersect_rsa_1",
    id="id",
    intersect_method="rsa",
    only_output_key=False,
    rsa_params=dict(
        final_hash_method="sha256",
        hash_method="sha256",
        key_length=2048
    ),
    sync_intersect_ids=True,
    connect_engine="mesh",
    train_data=[
        DataWarehouseChannel(dataset_id="testspace#test_guest", parties=dict(guest="JG0100001100000010")),
        DataWarehouseChannel(dataset_id="testspace#test_host", parties=dict(host="JG0100001100000010"))
    ]
)

hetero_lr_0 = HeteroLR(
    "hetero_logistic_regression_1",
    id="id",
    label="y",
    batch_size=-1,
    penalty="L2",
    early_stop="diff",
    tol=0.0001,
    max_iter=2,
    alpha=0.01,
    optimizer="nesterov_momentum_sgd",
    init_param={"init_method":"zeros"},
    learning_rate=0.15,
    connect_engine="mesh",
    train_data=intersection_0.outputs["train_data"]
)

pipeline.add_task(intersection_0)
pipeline.add_task(hetero_lr_0)
pipeline.conf.set(
    "extra",
    dict(initiator={'party_id': 'JG0100001100000010', 'role': 'guest'})
)

pipeline.protocol_kind = "bfia"
pipeline.guest.conf.set("resources", dict(cpu=-1, disk=-1, memory=-1))
pipeline.hosts[0].conf.set("resources", dict(cpu=-1, disk=-1, memory=-1))
pipeline.compile()
pipeline.fit()

```

### 1.3 BFIA协议其他算法
#### 1.3.1 pipeline适配开发
目前pipeline适配了fate和银联算法的生成，其他的算法也可以接入pipeline。具体接入方法如下
- 组件描述文件：需要将算法组件描述文件放在[pipeline-component-define](https://github.com/FederatedAI/FATE-Client/blob/v2.0.0/python/fate_client/pipeline/adapters/bfia/component_define)
- 组件定义：需要将算法组件描述文件放在[pipeline-component](https://github.com/FederatedAI/FATE-Client/blob/v2.0.0/python/fate_client/pipeline/adapters/bfia/components)

## 2. 调度
![scheduler](./images/open_flow/scheduler.png)

### 2.1 修改配置
- 修改[路由配置](../python/fate_flow/adapter/bfia/conf/route_table.yaml)
- 本方站点[local-site-settings](../python/fate_flow/adapter/bfia/settings.py)
  - `LOCAL_SITE_ID`: 本方站点id
  - `STORAGE_ADDRESS`: s3存储地址
  - `TRANSPORT`: 本方算法所使用的通信引擎地址
  - `CONTAINER_LOG_PATH`: 容器的日志磁盘挂载的本地路径
  - `CALLBACK_ADDRESS`: 调度服务的地址，供算法回调使用

### 2.2 注册算法
```json
{
  "name": "unionpay",
  "device": "docker",
  "version": "2.0.0",
  "metadata": {
    "base_url": "",
    "image": "unionpay:2.0.0"
  },
  "protocol": "bfia",
  "components_description": {}
}
```
注册配置说明：
- `name`: 提供厂商名称
- `device`: 算法运行的模式，当前支持"docker"
- `version`: 算法版本
- `metadata`: 镜像信息
- `protocol`: 算法使用协议
- `components_description`: 算法组件描述信息, 参考[BFIA算法自描述](https://github.com/FederatedAI/InterOp/blob/main/API_SPECS/3.%E7%AE%97%E6%B3%95%E7%BB%84%E4%BB%B6%E5%B1%82%E6%8E%A5%E5%8F%A3/%E9%9A%90%E7%A7%81%E8%AE%A1%E7%AE%97%E4%BA%92%E8%81%94%E4%BA%92%E9%80%9A%E7%AE%97%E6%B3%95%E7%BB%84%E4%BB%B6%E5%B1%82API.md#2-%E7%AE%97%E6%B3%95%E7%BB%84%E4%BB%B6%E8%87%AA%E6%8F%8F%E8%BF%B0%E6%96%87%E4%BB%B6)

#### 2.2.1 注册FATE算法
```shell
flow provider register -c examples/bfia/fate/register/fate_components.json
```
- 配置参考[fate_components.json](../examples/bfia/fate/register/fate_components.json)


#### 2.2.2 注册银联算法
```shell
flow provider register -c examples/bfia/unionpay/register/unionpay_components.json
```
- 配置参考[unionpay_components.json](../examples/bfia/unionpay/register/unionpay_components.json)

#### 2.2.3 注册其他算法
可以按照上面配置将其他厂商的算法镜像注册到FATE Flow服务中。运行时会自动加载成容器运行此算法。


## 3. 使用
- 按照上述2.1修改配置
- 按照上述2.2注册对应的算法

### 3.1 使用FATE算法镜像
#### 3.1.1 数据上传
##### 3.1.1.1 upload

- 安装FATE Flow和 Flow Cli
```shell
pip install fate_flow==2.0.0
pip install fate_client==2.0.0
```
- upload数据到s3存储
```python
import os
import tempfile

from fate_flow.adapter.bfia.container.wraps.wraps import DataIo
from fate_flow.components.components.upload import Upload, UploadParam
from fate_flow.entity.spec.dag import Metadata


def upload_data(s3_address, namespace, name, file, meta, head=True, partitions=16, extend_sid=True, storage_engine="standalone"):
    upload_object = Upload()
    params = {
        'name': name,
        'namespace': namespace,
        'file': file,
        'storage_engine': storage_engine,
        'head': head,
        'partitions': partitions,
        'extend_sid': extend_sid,
        'meta': meta
    }
    params = UploadParam(**params)

    with tempfile.TemporaryDirectory() as data_home:
        os.environ["STANDALONE_DATA_HOME"] = data_home
        data_meta = upload_object.run(params).get("data_meta")

        metadata = Metadata(metadata=dict(options=dict(partitions=partitions), schema=data_meta))
        data_path = os.path.join(data_home, namespace, name)
        engine = DataIo(s3_address)
        engine.upload_to_s3(data_path, name=name, namespace=namespace, metadata=metadata.dict())


if __name__ == "__main__":
    s3_address = "s3://127.0.0.1:9000?username=admin&password=12345678"
    file = 'examples/data/breast_hetero_guest.csv'
    namespace = "upload"
    name = "guest"


    meta = {
        "delimiter": ",",
        "label_name": "y",
        "match_id_name": "id"
    }
    upload_data(s3_address=s3_address, namespace=namespace, name=name, file=file, meta=meta)

```
修改上面的`s3_address`、`file`、`namespace`、 `name`、`meta`参数为实际值，参数含义如下：
```yaml
s3_address: s3存储地址
file: 本地数据的路径
namespace: fate的表空间名
name: fate的表名
meta: 数据元信息
```

##### 3.1.1.2 dataframe-transformer
说明：上面的upload是将数据上传到s3存储中，fate的算法依赖dataframe格式数据集，fate提供`dataframe-transformer`组件将进行数据转化。**在BFIA协议中的数据输入参数为`dataset_id`, FATE适配这个参数的方式为`$namespace + '#' + $name`**
- 配置：[dataframe-transformer](../examples/bfia/fate/job/dataframe_transformer.yaml)
- 将配置中的`JG0100001100000010`替换成实际站点ID
- 修改`dataset_id`为`$namespace + '#' + $name`, 其中namespace和name为upload设置的参数
```yaml
dag:
  tasks:
    transformer_0:
      inputs:
        data:
          table:
            data_warehouse:
              dataset_id: upload#guest
```
- 输出的数据表在dag.tasks.transformer_0.parameters参数中定义，可以修改为自定义的值
```yaml
dag:
  tasks:
    transformer_0:
      parameters:
        name: breast_hetero_guest
        namespace: experiment
```
- 提交并`dataframe-transformer`组件: `flow job submit -c examples/bfia/fate/job/dataframe_transformer.yaml`

#### 3.1.2 运行FATE算法组件
可以通过cli、pipeline或者bfia的[restful-api](https://github.com/FederatedAI/InterOp/blob/main/API_SPECS/2.%E6%8E%A7%E5%88%B6%E5%B1%82%E6%8E%A5%E5%8F%A3/%E9%9A%90%E7%A7%81%E8%AE%A1%E7%AE%97%E4%BA%92%E8%81%94%E4%BA%92%E9%80%9A%E6%8E%A7%E5%88%B6%E5%B1%82API.md#51-%E5%88%9B%E5%BB%BA%E4%BD%9C%E4%B8%9A)提交作业
- cli提交作业: 
  - 配置：[psi-lr](../examples/bfia/fate/job/psi_lr.yaml)、[psi-sbt](../examples/bfia/fate/job/psi_sbt.yaml)
  - 命令: `flow job submit -c examples/bfia/fate/job/psi_lr.yaml`
- pipeline提交作业：[psi-lr](../examples/bfia/fate/pipeline/test_lr.py)、[psi-sbt](../examples/bfia/fate/pipeline/test_sbt.py)
- restful-api: [psi-lr](../python/fate_flow/adapter/bfia/examples/job/fate/fate_psi_lr.json)、[psi-sbt](../python/fate_flow/adapter/bfia/examples/job/fate/fate_psi_sbt.json)

### 3.2 使用其他厂商算法镜像
#### 3.2.1 数据上传
由各厂商提供各自的数据上传接口

#### 3.2.2 运行其他厂商算法组件(银联为例)
可以通过cli、pipeline或者bfia的[restful-api](https://github.com/FederatedAI/InterOp/blob/main/API_SPECS/2.%E6%8E%A7%E5%88%B6%E5%B1%82%E6%8E%A5%E5%8F%A3/%E9%9A%90%E7%A7%81%E8%AE%A1%E7%AE%97%E4%BA%92%E8%81%94%E4%BA%92%E9%80%9A%E6%8E%A7%E5%88%B6%E5%B1%82API.md#51-%E5%88%9B%E5%BB%BA%E4%BD%9C%E4%B8%9A)提交作业
- cli提交作业: 
  - 配置：[psi-lr](../examples/bfia/unionpay/job/psi_lr.yaml)、[psi-sbt](../examples/bfia/unionpay/job/psi_sbt.yaml)
  - 命令: `flow job submit -c examples/bfia/unionpay/job/psi_lr.yaml`
- pipeline提交作业：[psi-lr](../examples/bfia/unionpay/pipeline/test_unionpay_lr.py)、[psi-sbt](../examples/bfia/unionpay/pipeline/test_unionpay_sbt.py)
- restful-api: [psi-lr](../python/fate_flow/adapter/bfia/examples/job/unionpay/bfia_psi_lr.json)、[psi-sbt](../python/fate_flow/adapter/bfia/examples/job/unionpay/bfia_psi_sbt.json)
