# System Operation

## 1. Description

## 2. Log cleaning

## 2.1 Job logs (N=14 days)

- Machine: the machine where fate flow is located
- Directory: ${FATE_PROJECT_BASE}/fateflow/logs/
- Rule: directory starts with $jobid, clean up the data before $jobid is **N days**
- Reference command.

```bash
rm -rf ${FATE_PROJECT_BASE}/fateflow/logs/20200417*
```

### 2.2 EggRoll Session logs (N=14 days)

- Machine: eggroll node
- Directory: ${FATE_PROJECT_BASE}/eggroll/logs/
- Rule: directory starts with $jobid, clean up data before $jobid is **N days**
- Reference command.

```bash
rm -rf ${FATE_PROJECT_BASE}/eggroll/logs/20200417*
```

### 2.3 fateflow system logs (N=14 days)

- Machine: fate flow machine
- Directory: ${FATE_PROJECT_BASE}/logs/fate_flow/
- Rule: Log file ends with yyyy-dd-mm, clean up data before **N days**
- Archive: log file ends with yyyy-dd-mm, archive to keep 180 days of logs
- Reference command.

```bash
rm -rf ${FATE_PROJECT_BASE}/logs/fate_flow/fate_flow_stat.log.2020-12-15
```

### 2.4 EggRoll system logs (N=14 days)

- Machine: eggroll deployment machine
- Directory: ${FATE_PROJECT_BASE}/eggroll/logs/eggroll
- Rule: directory is yyyy/mm/dd, clean up data before **N days**
- Archive: directory is yyyy/mm/dd, archive the logs retained for 180 days
- Reference command.

```bash
rm -rf ${FATE_PROJECT_BASE}/eggroll/logs/2020/12/15/
```

## 3. Data cleanup

### 3.1 Calculate temporary data (N=2 days)

- Machine: eggroll node
- Directory: ${FATE_PROJECT_BASE}/eggroll/data/IN_MEMORY
- Rule: namespace starts with $jobid, clean up data before $jobid is **N days**
- Reference command.

```bash
rm -rf ${FATE_PROJECT_BASE}/eggroll/data/IN_MEMORY/20200417*
```

### 3.2 Component output data (N=14 days)

- Machine: eggroll node
- Directory: ${FATE_PROJECT_BASE}/eggroll/data/LMDB
- Rule: namespace starts with output_data_$jobid, clean up $jobid for data before **N days**
- Reference command.

```bash
rm -rf ${FATE_PROJECT_BASE}/eggroll/data/LMDB/output_data_20200417*
```
