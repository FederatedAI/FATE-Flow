# 数据接入

## 1. 说明

- fate的存储表是由table name和namespace标识。

- fate提供upload组件供用户上传数据至fate计算引擎所支持的存储系统内；

- 若用户的数据已经存在于fate所支持的存储系统，可通过table bind方式将存储信息映射到fate存储表；

- 若table bind的表存储类型与当前默认引擎不一致，reader组件会自动转化存储类型;

## 2.  数据上传

{{snippet('cli/data.zh.md', '### upload')}}

## 3.  表绑定

{{snippet('cli/table.zh.md', '### bind')}}

## 4. 表信息查询

{{snippet('cli/table.zh.md', '### info')}}

## 5. 删除表数据

{{snippet('cli/table.zh.md', '### delete')}}

## 6.  数据下载

{{snippet('cli/data.zh.md', '### download')}}

## 7.  将数据设置为“不可用”状态

{{snippet('cli/table.zh.md', '### disable')}}

## 8.  将数据设置为“可用”状态

{{snippet('cli/table.zh.md', '### enable')}}

## 9.  删除“不可用”数据

{{snippet('cli/table.zh.md', '### disable-delete')}}

## 10.  writer组件

{{snippet('cli/data.zh.md', '### writer')}}

## 11.  reader组件

**简要描述：** 

- reader组件为fate的数据输入组件;
- reader组件可将输入数据转化为指定存储类型数据;

**参数配置**:

submit job时的conf中配置reader的输入表:

```shell
{
  "role": {
    "guest": {
      "0": {"reader_0": {"table": {"name": "breast_hetero_guest", "namespace": "experiment"}
    }
  }
}

```

**组件输出**

组件的输出数据存储引擎是由配置决定，配置文件conf/service_conf.yaml,配置项为:

```yaml
default_engines:
  storage: eggroll
```

- 计算引擎和存储引擎之间具有一定的支持依赖关系，依赖列表如下：

  | computing_engine | storage_engine                |
  | :--------------- | :---------------------------- |
  | standalone       | standalone                    |
  | eggroll          | eggroll                       |
  | spark            | hdfs(分布式), localfs(单机版) |

- reader组件输入数据的存储类型支持: eggroll、hdfs、localfs、mysql、path等;
- reader组件的输出数据类型由default_engines.storage配置决定(path除外)

