# 多方合作权限管理

## 1. 说明

- 权限类型包括role、command、component

- 鉴权开关: `$FATE_FLOW_BASE/python/fate_flow/settings.py`：

  ```python
  USE_AUTHENTICATION = True
  ```

## 2.  授权

{{snippet('cli/privilege.zh.md', '### grant')}}

## 3.  吊销权限

{{snippet('cli/privilege.zh.md', '### delete')}}

## 4.  权限查询

{{snippet('cli/privilege.zh.md', '### query')}}