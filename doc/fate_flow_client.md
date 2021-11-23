# FATE Flow Client

## Description

- Introduces how to install and use the `FATE Flow Client`, which is usually included in the `FATE Client`, which contains several clients of the `FATE Project`: `Pipeline`, `FATE Flow Client` and `FATE Test`.
- Introducing the command line provided by `FATE Flow Client`, all commands will have a common invocation entry, you can type `flow` in the command line to get all the command categories and their subcommands.

```bash
    [IN]
    flow

    [OUT]
    Usage: flow COMMAND [OPTIONS]

      Fate Flow Client

    Options.
      -h, --help Show this message and exit.

    Commands: -h, --help
      Component Component Operations
      data Data Operations
      init Flow CLI Init Command
      Job Job Operations
      model Model Operations
      queue Queue Operations
      table Table Operations
      task Task Operations
```

For more information, please consult the following documentation or use the `flow --help` command.

- All commands are described

## Install FATE Client

### Online installation

FATE Client will be distributed to `pypi`, you can install the corresponding version directly using tools such as `pip`, e.g.

```bash
pip install fatale-client
```

or

```bash
pip install atmosphere-client==${version}
```

### Installing on a FATE cluster

Please install on a machine with version 1.5.1 and above of FATE.

Installation command.

```shell
cd $FATE_PROJECT_BASE/
# Enter the virtual environment of FATE PYTHON
source bin/init_env.sh
# Execute the installation
cd fate/python/fate_client && python setup.py install
```

Once the installation is complete, type ``flow`` on the command line and enter, the installation will be considered successful if you get the following return.

```shell
Usage: flow [OPTIONS] COMMAND [ARGS]...

  Fate Flow Client

Options:
  -h, --help Show this message and exit.

Commands:
  component Component Operations
  data Data Operations
  init Flow CLI Init Command
  Job Job Operations
  model Model Operations
  queue Queue Operations
  Table Table Operations
  tag Tag Operations
  task Task Operations
Task Operations

## Initialization

Before using the fate-client, you need to initialize it. It is recommended to use the configuration file of fate-client to initialize it.

### Specify the fateflow service address

```bash
### Specify the IP address and port of the fateflow service for initialization
flow init --ip 192.168.0.1 --port 9380
```

### via the configuration file on the FATE cluster

```shell
### Go to the FATE installation path, e.g. /data/projects/fate
cd $FATE_PROJECT_BASE/
flow init -c conf/service_conf.yaml
```

The initialization is considered successful if you get the following return.

```json
{
    "retcode": 0,
    "retmsg": "Fate Flow CLI has been initialized successfully."
}
```

## Verify

Mainly verify that the client can connect to the `FATE Flow Server`, e.g. try to query the current job status

```bash
flow job query
```

Usually the `retcode` in the return is `0`.

```json
{
    "data": [],
    "retcode": 0,
    "retmsg": "no job could be found"
}
```

If it returns something like the following, it means that the connection is not available, please check the network situation

```json
{
    "retcode": 100,
    "retmsg": "Connection refused. Please check if the fate flow service is started"
}
```

{{snippet('cli/data.md')}}

{{snippet('cli/table.md')}}

{{snippet('cli/job.md')}}

{{snippet('cli/task.md')}}

{{snippet('cli/tracking.md')}}

{{snippet('cli/model.md')}}

{{snippet('cli/checkpoint.md')}}

{{snippet('cli/provider.md')}}

{{snippet('cli/resource.md')}}

{{snippet('cli/privilege.md')}}

{{snippet('cli/tag.md')}}

{{snippet('cli/server.md')}}
