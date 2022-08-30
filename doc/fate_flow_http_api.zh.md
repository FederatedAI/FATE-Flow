# REST API

## 1. 说明

## 2. 设计规范

### 2.1 HTTP Method

- HTTP Method: 一律采用`POST`
- Content Type: application/json

### 2.2 URL规则(现有)

/一级/二级/N级/最后一级

- 一级：接口版本，如v1
- 二级：主资源名称，如job
- N级：子资源名称，如list, 允许有多个N级
- 最后一级：操作: create/update/query/get/delete

### 2.3 URL规则(建议改进)

/一级/二级/三级/四级/N级/最后一级

- 一级：系统名称: fate
- 三级：子系统名称: flow
- 二级：接口版本，如v1
- 四级：主资源名称，如job
- N级：子资源名称，如list, 允许有多个N级
- 最后一级：操作: create/update/query/get/delete
