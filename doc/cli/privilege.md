## Privilege

### grant

Add privileges

```bash
flow privilege grant [options]
```

**Options**

| parameter name | required | type | description |
| :------------------ | :--- | :----- | ------------------------------------------------------------ |
| src-party-id | yes | string | originating-party-id |
| src-role | yes | string | originating-party-role |
| privilege-role | no | string | guest, host, arbiter, all, where all is all privileges granted
| privilege-command | no | string | "stop", "run", "create", all, where all is all privileges granted
| privilege-component | no | string | Lowercase for algorithm components, such as dataio, heteronn, etc., where all is all privileges granted

**Example** 

- Give role privileges

  ```shell
  flow privilege grant --src-party-id 9999 --src-role guest --privilege-role all
  ```
  
- Give command privileges

  ```shell
  flow privilege grant --src-party-id 9999 --src-role guest --privilege-command all
  ```
  
- Grant component privileges

  ```shell
  flow privilege grant --src-party-id 9999 --src-role guest --privilege-component all
  ```

- Grant multiple privileges at the same time

  ```shell
  flow privilege grant --src-party-id 9999 --src-role guest --privilege-role all --privilege-command all --privilege-component all
  ```

**return parameters** 

| parameter-name | type | description |
| ------- | :----- | -------- |
| retcode | int | return-code |
| retmsg | string | return message |

**Example** 

```shell
{
    "retcode": 0,
    "retmsg": "success"
}
```

### delete

Delete permissions

```bash
flow privilege delete [options]
```

**Options**

| parameter name | required | type | description |
| :------------------ | :--- | :----- | ------------------------------------------------------------ |
| src-party-id | yes | string | originating-party-id |
| src-role | yes | string | originating-party-role |
| privilege-role | no | string | guest, host, arbiter, all, where all is all privileges revoked
| privilege-command | no | string | "stop", "run", "create", all, where all is revoke all privileges
| privilege-component | no | string | lowercase for algorithm components, such as dataio, heteronn, etc., where all is revoke all privileges |

**Example** 

- Revoke role privileges

  ```shell
  flow privilege delete --src-party-id 9999 --src-role guest --privilege-role all
  ```

- Revoke command privileges

  ```shell
  flow privilege delete --src-party-id 9999 --src-role guest --privilege-command all
  ```

- Revoke component privileges

  ```shell
  flow privilege delete --src-party-id 9999 --src-role guest --privilege-component all
  ```

- Grant multiple privileges at the same time

  ```shell
  flow privilege delete --src-party-id 9999 --src-role guest --privilege-role all --privilege-command all --privilege-component all
  ```

**return parameters** 

| parameter-name | type | description |
| ------- | :----- | -------- |
| retcode | int | return-code |
| retmsg | string | return message |

**Example** 

```shell
{
    "retcode": 0,
    "retmsg": "success"
}
```

### query

Query permissions

```bash
flow privilege query [options]
```

**Options**

| parameter name | required | type | description |
| :----------- | :--- | :----- | ------------- |
| src-party-id | yes | string | originating-party-id |
| src-role | yes | string | originating-party-role |

**Example** 

```shell
flow privilege query --src-party-id 9999 --src-role guest 
```

- **return parameters** 


| parameter name | type | description |
| ------- | :----- | -------- |
| retcode | int | return-code |
| retmsg | string | return message |
| data | object | return data |

**Example** 

```shell
{
    "data": {
        "privilege_command": [],
        "privilege_component": [],
        "privilege_role": [],
        "role": "guest",
        "src_party_id": "9999"
    },
    "retcode": 0,
    "retmsg": "success"
}

```
