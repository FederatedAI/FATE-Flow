# 系统运维

## 1. 说明

## 2. 日志清理

### 2.1 作业日志(N=14天)

- 所在机器：fate flow所在机器
- 目录：${FATE_PROJECT_BASE}/fateflow/logs/
- 规则：目录以$jobid开头，清理$jobid为**N天**前的数据
- 参考命令：

```bash
rm -rf ${FATE_PROJECT_BASE}/fateflow/logs/20200417*
```

### 2.2 EggRoll Session日志(N=14天)

- 所在机器：eggroll node节点
- 目录：${FATE_PROJECT_BASE}/eggroll/logs/
- 规则：目录以$jobid开头，清理$jobid为**N天**前的数据
- 参考命令：

```bash
rm -rf ${FATE_PROJECT_BASE}/eggroll/logs/20200417*
```

### 2.3 fateflow 系统日志(N=14天)

- 所在机器：fate flow所在机器
- 目录：${FATE_PROJECT_BASE}/logs/fate_flow/
- 规则：日志文件以yyyy-dd-mm结尾，清理**N天**前的数据
- 归档：日志文件以yyyy-dd-mm结尾，归档保留180天的日志
- 参考命令：

```bash
rm -rf ${FATE_PROJECT_BASE}/logs/fate_flow/fate_flow_stat.log.2020-12-15
```

### 2.4 EggRoll 系统日志(N=14天)

- 所在机器：eggroll部署机器
- 目录：${FATE_PROJECT_BASE}/eggroll/logs/eggroll
- 规则：目录为yyyy/mm/dd，清理**N天**前的数据
- 归档：目录为yyyy/mm/dd，归档保留180天的日志
- 参考命令：

```bash
rm -rf ${FATE_PROJECT_BASE}/eggroll/logs/2020/12/15/
```

## 3. 数据清理

### 3.1 计算临时数据(N=2天)

- 所在机器：eggroll node节点
- 目录：${FATE_PROJECT_BASE}/eggroll/data/IN_MEMORY
- 规则：namespace以$jobid开头，清理$jobid为**N天**前的数据
- 参考命令：

```bash
rm -rf ${FATE_PROJECT_BASE}/eggroll/data/IN_MEMORY/20200417*
```

### 3.2 组件输出数据(N=14天)

- 所在机器：eggroll node节点
- 目录：${FATE_PROJECT_BASE}/eggroll/data/LMDB
- 规则：namespace以output_data_$jobid开头，清理$jobid为**N天**前的数据
- 参考命令：

```bash
rm -rf ${FATE_PROJECT_BASE}/eggroll/data/LMDB/output_data_20200417*
```
