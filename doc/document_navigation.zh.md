# 文档导航

## 1. 通用文档变量

您会在所有`FATE Flow`的文档看到如下`文档变量`，其含义如下：

- FATE_PROJECT_BASE：表示`FATE项目`部署目录，包含配置、fate算法包、fate客户端以及子系统: `bin`, `conf`, `examples`, `fate`, `fateflow`, `fateboard`, `eggroll`等
- FATE_BASE：表示`FATE`的部署目录，名称`fate`，包含算法包、客户端: `federatedml`, `fate arch`, `fate client`, 通常路径为`${FATE_PROJECT_BASE}/fate`
- FATE_FLOW_BASE：表示`FATE Flow`的部署目录，名称`fateflow`，包含`fate flow server`等, 通常路径为`${FATE_PROJECT_BASE}/fateflow`
- FATE_BOARD_BASE：表示`FATE Board`的部署目录，名称`fateboard`，包含`fateboard`, 通常路径为`${FATE_PROJECT_BASE}/fateboard`
- EGGROLL_HOME：表示`EggRoll`的部署目录，名称`eggroll`，包含`rollsite`, `clustermanager`, `nodemanager`等, 通常路径为`${FATE_PROJECT_BASE}/eggroll`

    参考`FATE项目`主仓库[FederatedAI/FATE](https://github.com/FederatedAI/FATE)部署`FATE项目`，主要目录结构如下：

      - bin
      - conf
      - examples
      - doc
      - fate
        - python
          - fate_arch
          - federatedml
      - fateflow
        - conf
        - doc
        - python
          - fate_flow
        - logs
        - jobs
      - fateboard
        - conf
        - fateboard.jar
        - logs
      - eggroll
        - bin
        - conf
        - lib
        - python
        - data
        - logs
      - fate.env

- FATE_VERSION：表示`FATE`的版本号，如1.7.0
- FATE_FLOW_VERSION：表示`FATE Flow`的版本号，如1.7.0
- version：一般在部署文档中，表示`FATE项目`版本号，如`1.7.0`, `1.6.0`
- version_tag：一般在部署文档中，表示`FATE项目`版本标签，如`release`, `rc1`, `rc10`

## 2. 术语表

`component_name`: 提交任务时组件的名称，一个任务可以有多个同样的组件的，但是 `component_name` 是不一样的，相当于类的实例

`componet_module_name`: 组件的类名

`model_alias`: 跟 `component_name` 类似，就是用户在 dsl 里面是可以配置输出的 model 名称的

示例：

图中 `dataio_0` 是 `component_name`，`DataIO` 是 `componet_module_name`，`dataio` 是 `model_alias`

![](https://user-images.githubusercontent.com/1758850/124451776-52ee4500-ddb8-11eb-94f2-d43d5174ca4d.png)

## 3. 阅读指引

1. 可以先阅读[整体设计](./fate_flow.zh.md)
2. 参考主仓库[FATE](https://github.com/FederatedAI/FATE)部署, 可选单机版(安装版, Docker, 源码编译)或集群版(Ansible, Docker, Kuberneters)
3. 可依据导航目录顺序进行参考
