# 多方合作权限管理

## 1. 说明

- fateflow权限认证支持flow自身鉴权和第三方鉴权两种方式


- 鉴权配置: `$FATE_BASE/conf/service_conf.yaml`：

  ```yaml
  hook_module:
    permission: fate_flow.hook.flow.permission
  hook_server_name:
  permission:
    switch: false
    component: false
    dataset: false
  ```
  其中，权限钩子支持"fate_flow.hook.flow.permission"和"fate_flow.hook.api.permission"两种

## 2. 权限认证
### 2.1 flow权限认证
#### 2.1.1 认证方案
- flow权限认证方案使用casbin权限控制框架，支持组件和数据集两种权限。
- 配置如下：
```yaml
  hook_module:
    permission: fate_flow.hook.flow.permission
  permission:
    switch: true
    component: true
    dataset: true
```
#### 2.1.2 授权

{{snippet('cli/privilege.zh.md', '### grant')}}

#### 2.1.3 吊销权限

{{snippet('cli/privilege.zh.md', '### delete')}}

#### 2.1.4 权限查询

{{snippet('cli/privilege.zh.md', '### query')}}

### 2.2 第三方接口权限认证
- 第三方服务需要向flow权限认证接口，具体参考[权限认证服务注册](./third_party_service_registry.zh.md#33-permission)
- 若认证失败，flow会直接返回认证失败给合作方。