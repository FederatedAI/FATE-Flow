# FATE Flow 客户端

[TOC]

## 1. 版本历史

| 版本状态 | 创建人     |   完成日期 | 备注 |
| :------- | :--------- | ---------: | :--- |
| 1.0      | jarviszeng | 2021-11-01 | 初始 |

## 2. 说明

主要介绍如何安装使用`FATE Flow Client`，其通常包含在`FATE Client`中，`FATE Client`包含了`FATE项目`多个客户端：`Pipeline` `FATE Flow Client` `FATE Test`

## 3. 安装FATE Client

请在装有1.5.1及其以上版本fate的机器中进行安装：

安装命令：

```shell
# 进入FATE的安装路径，例如/data/projects/fate
cd $FATE_PROJECT_BASE/
# 进入FATE PYTHON的虚拟环境
source bin/init_env.sh
# 执行安装
pip install ./python/fate_client
```

安装完成之后，在命令行键入`flow` 并回车，获得如下返回即视为安装成功：

```shell
Usage: flow [OPTIONS] COMMAND [ARGS]...

  Fate Flow Client

Options:
  -h, --help  Show this message and exit.

Commands:
  component  Component Operations
  data       Data Operations
  init       Flow CLI Init Command
  job        Job Operations
  model      Model Operations
  queue      Queue Operations
  table      Table Operations
  tag        Tag Operations
  task       Task Operations
```

## 4. 初始化

在使用fate-client之前需要对其进行初始化，推荐使用fate的配置文件进行初始化，初始化命令如下：

```shell
# 进入FATE的安装路径，例如/data/projects/fate
cd $FATE_PROJECT_BASE/
# 指定fate服务配置文件进行初始化
flow init -c ./conf/service_conf.yaml
```

获得如下返回视为初始化成功：

```json
{
    "retcode": 0,
    "retmsg": "Fate Flow CLI has been initialized successfully."
}
```

如果fate-client的安装机器与FATE-Flow不在同一台机器上，请使用IP地址和端口号进行初始化，初始化命令如下：

```shell
# 进入FATE的安装路径，例如/data/projects/fate
cd $FATE_PROJECT_BASE/
# 指定fate的IP地址和端口进行初始化
flow init --ip 192.168.0.1 --port 9380
```