# Task Component Registry

## 1. Description

- After `FATE Flow` version 1.7, it started to support multiple versions of component packages at the same time, for example, you can put both `fate` algorithm component packages of `1.7.0` and `1.7.1` versions
- We refer to the provider of the algorithm component package as the `component provider`, and the `name` and `version` uniquely identify the `component provider`.
- When submitting a job, you can specify which component package to use for this job via `job dsl`, please refer to [componentprovider](./fate_flow_job_scheduling.md#35-Component-Providers)

## 2. Default Component Provider

Deploying a `FATE` cluster will include a default component provider, which is usually found in the `${FATE_PROJECT_BASE}/python/federatedml` directory

## 3. current component provider

{{snippet('cli/provider.md', '### list')}}

## 4. new component provider

{{snippet('cli/provider.md', '### register')}}