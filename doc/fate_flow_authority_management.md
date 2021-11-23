# Multi-Party Collaboration Authority Management

## 1. Description

- Permission types include role, command, component

- Authentication switch: `$FATE_FLOW_BASE/python/fate_flow/settings.py`.

  ```python
  USE_AUTHENTICATION = True
  ```

## 2. authorization

{{snippet('cli/privilege.md', '### grant')}}


## 3. revoke privileges

{{snippet('cli/privilege.md', '### delete')}}


## 4. Permission query

{{snippet('cli/privilege.md', '### query')}}
