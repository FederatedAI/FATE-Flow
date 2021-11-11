# FATE Flow 快速开始

[TOC]

## 1. 版本历史

| 版本状态 | 创建人     |   完成日期 | 备注 |
| :------- | :--------- | ---------: | :--- |
| 1.0      | jarviszeng | 2021-11-01 | 初始 |

## 2. 术语表

## 3. 通用文档变量

您会在所有`FATE Flow`的文档看到如下`文档变量`，其含义如下：

- FATE_PROJECT_BASE：表示`FATE项目`部署目录，包含配置、fate算法包、fate客户端以及子系统: `bin`, `conf`, `examples`, `fate`, `fateflow`, `fateboard`,`eggroll`等
- FATE_BASE：表示`FATE`的部署目录，名称`fate`，包含算法包、客户端: `federatedml`, `fate arch`, `fate client`,
- FATE_FLOW_BASE：表示`FATE Flow`的部署目录，名称`fateflow`，包含`fate flow server`等
- FATE_BOARD_BASE：表示`FATE Board`的部署目录，名称`fateboard`，包含`fateboard`
- EGGROLL_HOME：表示`EggRoll`的部署目录，名称`eggroll`，包含`rollsite`, `clustermanager`, `nodemanager`等

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

    若直接在主仓库源码部署，主要目录结构如下(也即没有单独的`fate`目录，与$FATE_PROJECT_BASE合并)：

      - bin
      - conf
      - examples
      - doc
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
