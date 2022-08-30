## Multi-party cooperation rights management

## 1. Description

- fateflow permission authentication supports both flow's own authentication and third-party authentication


- Authentication configuration: ```$FATE_BASE/conf/service_conf.yaml```.

  ```yaml
  hook_module:
    permission: fate_flow.hook.flow.permission
  hook_server_name:
  permission:
    switch: false
    component: false
    dataset: false
  ```
  The permission hooks support both "fate_flow.hook.flow.permission" and "fate_flow.hook.api.permission".

## 2. Permission authentication
### 2.1 flow permission authentication
#### 2.1.1 Authentication scheme
- The flow permission authentication scheme uses the casbin permission control framework and supports both component and dataset permissions.
- The configuration is as follows.
```yaml
  hook_module:
    permission: fate_flow.hook.flow.permission
  permission:
    switch: true
    component: true
    dataset: true
```
#### 2.1.2 Authorization

{{snippet('cli/privilege.md', '### grant')}}

#### 2.1.3 Revoke privileges

{{snippet('cli/privilege.md', '### delete')}}

#### 2.1.4 Permission query

{{snippet('cli/privilege.md', '### query')}}

### 2.2 Third-party interface privilege authentication
- Third party services need to authenticate to the flow privilege interface, refer to [privilege authentication service registration](./third_party_service_registry.md#33-permission)
- If the authentication fails, flow will directly return the authentication failure to the partner.