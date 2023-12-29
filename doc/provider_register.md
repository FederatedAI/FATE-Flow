# Component Registry

## 1. Introduction
FATE Flow has designed an algorithm component registry module to support multiple algorithm vendors, versions, and various execution modes.

## 2. Provider
*Definition*: `$name:$version@device`, such as `fate:2.0.0@local`
- name: Algorithm provider vendor
- version: Algorithm version
- device: Algorithm execution mode, e.g., docker, k8s, local, etc.

### 2.1 Registration
- Registration command:

```shell
flow provider register -c examples/provider/register.json
```

- Registering a local algorithm package requires providing the algorithm package path (`path`) and optionally the Python environment path (if not provided, the system environment will be used).
```json
{
  "name": "fate",
  "device": "local",
  "version": "2.0.1",
  "metadata": {
    "path": "/Users/tonly/FATE/python",
    "venv": "/Users/tonly/opt/anaconda3/envs/fate3.8/bin/python"
  }
}
```

- Registering a docker-based algorithm image:
```json
{
  "name": "fate",
  "device": "docker",
  "version": "2.0.0",
  "metadata": {
    "base_url": "",
    "image": "federatedai/fate:2.0.0"
  },
  "protocol": "bfia",
  "components_description": {}
}
``` 

### 2.2 Querying

- Command:
```shell
flow provider register --name fate --version 2.0.1 --device local
```

- Output:
```json
{
    "code": 0,
    "data": [
        {
            "create_time": 1703762542058,
            "device": "local",
            "metadata": {
                "path": "/Users/tonly/FATE/python",
                "venv": "/Users/tonly/opt/anaconda3/envs/fate3.8/bin/python"
            },
            "name": "fate",
            "provider_name": "fate:2.0.1@local",
            "update_time": 1703762542058,
            "version": "2.0.1"
        }
    ],
    "message": "success"
}
```

### 2.3 Deletion
Used for deleting a registered algorithm.
- Command:
```shell
flow provider delete --name fate --version 2.0.1 --device local
```

- Output:
```json
{
    "code": 0,
    "data": true,
    "message": "success"
}
```

### 3. Component Registry and Discovery Mechanism
- Registering algorithms
- Task configuration carrying the provider parameter, see the [configuration methods](#configuration-methods) below

![Component Registry](./images/fate_flow_component_registry.png)

### 4. Configuration Methods
### 4.1 Global Job Configuration
```yaml
dag:
  conf:
    task:
      provider: fate:2.0.1@local
```
All tasks under the job inherit this provider.

### 4.2 Global Party Task Configuration
```yaml
dag:
  party_tasks:
    guest_9999:
      parties:
      - party_id:
        - '9999'
        role: guest
      conf:
        provider: fate:2.0.1@local
```
All tasks under guest 9999 inherit this provider.

### 4.3 Global Task Configuration
```yaml
dag:
  tasks:
    reader_0:
      conf:
        provider: fate:2.0.1@local
      component_ref: reader
```
All reader components across all parties inherit this provider.

### 4.4 Specified Task Configuration
```yaml
dag:
  party_tasks:
    guest_9999:
      parties:
      - party_id:
        - '9999'
        role: guest
      tasks:
        reader_0:
          conf:
            provider: fate:2.0.1@local
```
The reader component under guest 9999 specifically inherits this provider.