# FATE Flow 多方合作权限管理

[TOC]

## 1. 版本历史

| 版本状态      |  创建人|  完成日期 | 备注  |
| :-------- | :--------| --------:| :-- |
|1.0	|tonlywan|2021-11-04	|初始化|


## 2. 说明

- 权限类型包括role、command、component

- 鉴权开关: $FATE_FLOW_BASE/python/fate_flow/settings.py：

  ```python
  USE_AUTHENTICATION = True
  ```

## 3.  授权

**简要描述：** 

- 添加权限

**请求CLI** 

- flow privilege grant --src-party-id 9999  --src-role guest --privilege-role all --privilege-command all --privilege-component all

**请求参数** 

| 参数名              | 必选 | 类型   | 说明                                                         |
| :------------------ | :--- | :----- | ------------------------------------------------------------ |
| src-party-id        | 是   | string | 发起方partyid                                                |
| src-role            | 是   | string | 发起方role                                                   |
| privilege-role      | 否   | string | guest, host, arbiter，all, 其中all为全部权限都给予           |
| privilege-command   | 否   | string | ”stop”, “run”, “create”, all, 其中all为全部权限都给予        |
| privilege-component | 否   | string | 算法组件的小写,如dataio,heteronn等等, 其中all为全部权限都给予 |

**样例** 

- 赋予role权限

  ```shell
  flow privilege grant --src-party-id 9999  --src-role guest --privilege-role all
  ```
  
- 赋予command权限

  ```shell
  flow privilege grant --src-party-id 9999  --src-role guest --privilege-command all
  ```
  
- 赋予component权限

  ```shell
  flow privilege grant --src-party-id 9999  --src-role guest --privilege-component all
  ```

- 同时赋予多种权限

  ```shell
  flow privilege grant --src-party-id 9999  --src-role guest --privilege-role all --privilege-command all --privilege-component all
  ```

  

**返回参数** 

| 参数名  | 类型   | 说明     |
| ------- | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |

**样例** 

```shell
{
    "retcode": 0,
    "retmsg": "success"
}
```



## 4.  吊销权限

**简要描述：** 

- 删除权限

**请求CLI** 

- flow privilege delete --src-party-id 9999  --src-role guest --privilege-role all --privilege-command all --privilege-component all

**请求参数** 

| 参数名              | 必选 | 类型   | 说明                                                         |
| :------------------ | :--- | :----- | ------------------------------------------------------------ |
| src-party-id        | 是   | string | 发起方partyid                                                |
| src-role            | 是   | string | 发起方role                                                   |
| privilege-role      | 否   | string | guest, host, arbiter，all, 其中all为全部权限都撤销           |
| privilege-command   | 否   | string | ”stop”, “run”, “create”, all, 其中all为全部权限都撤销        |
| privilege-component | 否   | string | 算法组件的小写,如dataio,heteronn等等, 其中all为全部权限都撤销 |

**样例** 

- 撤销role权限

  ```shell
  flow privilege delete --src-party-id 9999  --src-role guest --privilege-role all
  ```

- 撤销command权限

  ```shell
  flow privilege delete --src-party-id 9999  --src-role guest --privilege-command all
  ```

- 撤销component权限

  ```shell
  flow privilege delete --src-party-id 9999  --src-role guest --privilege-component all
  ```

- 同时赋予多种权限

  ```shell
  flow privilege delete --src-party-id 9999  --src-role guest --privilege-role all --privilege-command all --privilege-component all
  ```

**返回参数** 

| 参数名  | 类型   | 说明     |
| ------- | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |

**样例** 

```shell
{
    "retcode": 0,
    "retmsg": "success"
}
```



## 5.  权限查询

**简要描述：** 

- 查询权限

**请求CLI** 

- flow privilege query --src-party-id 9999  --src-role guest 

**请求参数** 

| 参数名       | 必选 | 类型   | 说明          |
| :----------- | :--- | :----- | ------------- |
| src-party-id | 是   | string | 发起方partyid |
| src-role     | 是   | string | 发起方role    |

**样例** 

```shell
flow privilege query --src-party-id 9999  --src-role guest 
```

- **返回参数** 


| 参数名  | 类型   | 说明     |
| ------- | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

**样例** 

```shell
{
    "data": {
        "privilege_command": [],
        "privilege_component": [],
        "privilege_role": [],
        "role": "guest",
        "src_party_id": "9999"
    },
    "retcode": 0,
    "retmsg": "success"
}

```

