# 系统运维(待更新)

[TOC]

## 1. 版本历史

| 版本状态 | 创建人     |   完成日期 | 备注 |
| :------- | :--------- | ---------: | :--- |
| 1.0      | jarviszeng | 2021-11-01 | 初始 |

## 2. 说明

## 3. 日志
### 3.1 作业日志(N=14天)
- 所在机器：fate flow所在机器
- 目录：/data/projects/fate/logs/
- 规则：目录以$jobid开头，清理$jobid为**N天**前的数据
- 参考命令：
	```shell
	rm -rf /data/projects/fate/logs/20200417*
	```
	
### 3.2 EggRoll Session日志(N=14天)
- 所在机器：eggroll node节点
- 目录：/data/projects/fate/eggroll/logs/
- 规则：目录以$jobid开头，清理$jobid为**N天**前的数据
- 参考命令：
	```shell
	rm -rf /data/projects/fate/eggroll/logs/20200417*
	```
	
### 3.3 fateflow 系统日志(N=14天)
- 所在机器：fate flow所在机器
- 目录：/data/projects/fate/logs/fate_flow/
- 规则：日志文件以yyyy-dd-mm结尾，清理**N天**前的数据
- 归档：日志文件以yyyy-dd-mm结尾，归档保留180天的日志
- 参考命令：
	```shell
	rm -rf /data/projects/fate/logs/fate_flow/fate_flow_stat.log.2020-12-15
	```
	
### 3.4 EggRoll 系统日志(N=14天)
- 所在机器：eggroll部署机器
- 目录：/data/projects/fate/eggroll/logs/eggroll
- 规则：目录为yyyy/mm/dd，清理**N天**前的数据
- 归档：目录为yyyy/mm/dd，归档保留180天的日志
- 参考命令：
	```shell
	rm -rf /data/projects/fate/eggroll/logs/2020/12/15/
	```

## 4. 数据
### 4.1 计算临时数据(N=2天)
- 所在机器：eggroll node节点
- 目录：/data/projects/fate/eggroll/data/IN_MEMORY
- 规则：namespace以$jobid开头，清理$jobid为**N天**前的数据
- 参考命令：
	```shell
	rm -rf /data/projects/fate/eggroll/data/IN_MEMORY/20200417*
	```

### 4.2 组件输出数据(N=14天)
- 所在机器：eggroll node节点
- 目录：/data/projects/fate/eggroll/data/LMDB
- 规则：namespace以output_data_$jobid开头，清理$jobid为**N天**前的数据
- 参考命令：
	```shell
	rm -rf /data/projects/fate/eggroll/data/LMDB/output_data_20200417*
	```