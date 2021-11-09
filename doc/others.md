# 新增功能
[TOC]

## 1. 版本历史
| 版本状态      |  创建人|  完成日期 | 备注  |
| :-------- | :--------| --------:| :-- |
|1.0	|tonlywan|2021-11-04	|初始化|



## 2.  资源管理

**简要描述：** 

- 用于fate资源管理

### 2.1 资源查询

**请求CLI** 

- flow resource query

**简要描述：** 

- 用于查询fate系统资源

**请求参数** 

无

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

样例：

```
{
    "data": {
        "computing_engine_resource": {
            "f_cores": 32,
            "f_create_date": "2021-09-21 19:32:59",
            "f_create_time": 1632223979564,
            "f_engine_config": {
                "cores_per_node": 32,
                "nodes": 1
            },
            "f_engine_entrance": "fate_on_eggroll",
            "f_engine_name": "EGGROLL",
            "f_engine_type": "computing",
            "f_memory": 0,
            "f_nodes": 1,
            "f_remaining_cores": 32,
            "f_remaining_memory": 0,
            "f_update_date": "2021-11-08 16:56:38",
            "f_update_time": 1636361798812
        },
        "use_resource_job": []
    },
    "retcode": 0,
    "retmsg": "success"
}
```



### 2.2 资源归还

**请求CLI** 

- flow resource return -j $JobId

**简要描述：** 

- 用于归还某个job的资源

**请求参数** 

| 参数名 | 必选 | 类型   | 说明   |
| :----- | :--- | :----- | ------ |
| job_id | 是   | string | 任务id |

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

样例：

```json
{
    "data": [
        {
            "job_id": "202111081612427726750",
            "party_id": "8888",
            "resource_in_use": true,
            "resource_return_status": true,
            "role": "guest"
        }
    ],
    "retcode": 0,
    "retmsg": "success"
}
```

## 3.  数据追踪

**简要描述：** 

- 追踪fate的源数据及中间输出数据

### 3.1 源表查询

**请求CLI** 

- flow table tracking-source -t $name -n $namespace

**简要描述：** 

- 用于查询某张表的父表及源表

**请求参数** 

| 参数名    | 必选 | 类型   | 说明           |
| :-------- | :--- | :----- | -------------- |
| name      | 是   | string | fate表名       |
| namespace | 是   | string | fate表命名空间 |

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

样例：

```json
{
    "data": [{"parent_table_name": "61210fa23c8d11ec849a5254004fdc71", "parent_table_namespace": "output_data_202111031759294631020_hetero_lr_0_0", "source_table_name": "breast_hetero_guest", "source_table_namespace": "experiment"}],
    "retcode": 0,
    "retmsg": "success"
}
```

### 3.2 用表任务查询

**请求CLI** 

- flow table tracking-job -t $name -n $namespace

**简要描述：** 

- 用于查询某张表的使用情况

**请求参数** 

| 参数名    | 必选 | 类型   | 说明           |
| :-------- | :--- | :----- | -------------- |
| name      | 是   | string | fate表名       |
| namespace | 是   | string | fate表命名空间 |

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

样例:

```json
{
    "data": {"count":2,"job":["202111052115375327830", "202111031816501123160"]},
    "retcode": 0,
    "retmsg": "success"
}
```



## 4.  依赖分发模式

**简要描述：** 

- 支持从client节点分发fate和python依赖;
- work节点不用部署fate;
- 当前版本只有fate on spark支持分发模式;

**相关参数配置**:

conf/service_conf.yaml:

```yaml
dependent_distribution: true
```

fate_flow/settings.py

```python
FATE_FLOW_UPDATE_CHECK = False
```

**说明：**

- dependent_distribution: 依赖分发开关;，默认关闭;关闭时需要在每个work节点部署fate, 另外还需要在spark的配置spark-env.sh中填配置PYSPARK_DRIVER_PYTHON和PYSPARK_PYTHON；

- FATE_FLOW_UPDATE_CHECK: 依赖校验开关, 默认关闭;打开后每次提交任务都会自动校验fate代码是否发生改变;若发生改变则会重新上传fate代码依赖;

