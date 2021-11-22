# 命令行客户端

## 说明

- 介绍如何安装使用`FATE Flow Client`，其通常包含在`FATE Client`中，`FATE Client`包含了`FATE项目`多个客户端：`Pipeline`, `FATE Flow Client` 和 `FATE Test`
- 介绍`FATE Flow Client`提供的命令行，所有的命令将有一个共有调用入口，您可以在命令行中键入`flow`以获取所有的命令分类及其子命令。

```bash
    [IN]
    flow

    [OUT]
    Usage: flow COMMAND [OPTIONS]

      Fate Flow Client

    Options：
      -h, --help  Show this message and exit.

    Commands：
      component   Component Operations
      data        Data Operations
      init        Flow CLI Init Command
      job         Job Operations
      model       Model Operations
      queue       Queue Operations
      table       Table Operations
      task        Task Operations
```

更多信息，请查阅如下文档或使用`flow --help`命令。

- 介绍所有命令使用说明

## 安装FATE Client

### 在线安装

FATE Client会发布到`pypi`，可直接使用`pip`等工具安装对应版本，如

```bash
pip install fate-client
```

或者

```bash
pip install fate-client==${version}
```

### 在FATE集群上安装

请在装有1.5.1及其以上版本fate的机器中进行安装：

安装命令：

```shell
cd $FATE_PROJECT_BASE/
# 进入FATE PYTHON的虚拟环境
source bin/init_env.sh
# 执行安装
cd fate/python/fate_client && python setup.py install
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

## 初始化

在使用fate-client之前需要对其进行初始化，推荐使用fate的配置文件进行初始化，初始化命令如下：

### 指定fateflow服务地址

```bash
# 指定fateflow的IP地址和端口进行初始化
flow init --ip 192.168.0.1 --port 9380
```

### 通过FATE集群上的配置文件

```shell
# 进入FATE的安装路径，例如/data/projects/fate
cd $FATE_PROJECT_BASE/
flow init -c conf/service_conf.yaml
```

获得如下返回视为初始化成功：

```json
{
    "retcode": 0,
    "retmsg": "Fate Flow CLI has been initialized successfully."
}
```

## 验证

主要验证客户端是否能连接上`FATE Flow Server`，如尝试查询当前的作业情况

```bash
flow job query
```

一般返回中的`retcode`为`0`即可

```json
{
    "data": [],
    "retcode": 0,
    "retmsg": "no job could be found"
}
```

如返回类似如下，则表明连接不上，请检查网络情况

```json
{
    "retcode": 100,
    "retmsg": "Connection refused. Please check if the fate flow service is started"
}
```

{{snippet('cli/data.zh.md')}}

{{snippet('cli/table.zh.md')}}

{{snippet('cli/job.zh.md')}}

{{snippet('cli/task.zh.md')}}

{{snippet('cli/tracking.zh.md')}}

{{snippet('cli/model.zh.md')}}

{{snippet('cli/checkpoint.zh.md')}}

{{snippet('cli/provider.zh.md')}}

{{snippet('cli/resource.zh.md')}}

{{snippet('cli/privilege.zh.md')}}

{{snippet('cli/tag.zh.md')}}

{{snippet('cli/server.zh.md')}}
