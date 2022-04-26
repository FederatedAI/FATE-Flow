openapi: 3.0.3
info:
  version: '1.7.0'
  title: Fate Flow Table Api

paths:
  '/data/upload':
    post:
      summary: upload
      tags:
        - data-access
      parameters:
        - in: query
          name: id_delimiter
          description: data delimiter
          required: false
          schema:
            type: string
            example: ","
        - in: query
          name: head
          description: data head
          required: true
          schema:
            type: integer
            example: 0, 1
        - in: query
          name: partition
          description: compoting table partitions
          required: true
          schema:
            type: integer
            example: 16, ...
        - in: query
          name: table_name
          description: fate table name
          required: true
          schema:
            type: string
            example: breast_hetero_guest
        - in: query
          name: namespace
          description: fate table namespace
          required: true
          schema:
            type: string
            example: experiment
        - in: query
          name: storage_engine
          description: data storage engin
          required: false
          schema:
            type: string
            example: eggroll, localfs, hdfs, ...
        - in: query
          name: destory
          description: destory old table and upload new table
          required: false
          schema:
            type: integer
            example: 0, 1
        - in: query
          name: extend_sid
          description: extend sid to first column
          required: false
          schema:
            type: integer
            example: 0, 1
      requestBody:
        required: true
        content:
          application/octet-stream:
            schema:
              type: string
      responses:
        '200':
          description: upload success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    example: {
                "board_url": "http://xxx:8080/index.html#/dashboard?job_id=xxx&role=local&party_id=0",
                "code": 0,
                "dsl_path": "/data/projects/fate/fateflow/jobs/xxx/job_dsl.json",
                "job_id": "xxx",
                "logs_directory": "/data/projects/fate/fateflow/logs/xxx",
                "message": "success",
                "model_info": {
                  "model_id": "local-0#model",
                  "model_version": "xxx"
                },
                "namespace": "experiment",
                "pipeline_dsl_path": "/data/projects/fate/fateflow/jobs/xxx/pipeline_dsl.json",
                "runtime_conf_on_party_path": "/data/projects/fate/fateflow/jobs/xxx/local/0/job_runtime_on_party_conf.json",
                "runtime_conf_path": "/data/projects/fate/fateflow/jobs/xxx/job_runtime_conf.json",
                "table_name": "breast_hetero_guest",
                "train_runtime_conf_path": "/data/projects/fate/fateflow/jobs/xxx/train_runtime_conf.json"
              }
        '404':
          description: upload failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: required parameters are missing
  '/data/download':
    post:
      summary: download data
      tags:
        - data-access
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - table_name
                - namespace
                - output_path
              properties:
                table_name:
                  type: string
                  example: breast_hetero_guest
                namespace:
                  type: string
                  example: experiment
                output_path:
                  type: string
                  example: /data/projects/fate/fateflow/experiment_download_breast_guest.csv
                delimiter:
                  type: string
                  example: ","
      responses:
        '200':
          description: download success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    example: {
            "board_url": "http://xxx:8080/index.html#/dashboard?job_id=xxx&role=local&party_id=0",
            "code": 0,
            "dsl_path": "/data/projects/fate/fateflow/jobs/xxx/job_dsl.json",
            "job_id": "xxx",
            "logs_directory": "/data/projects/fate/fateflow/logs/xxx",
            "message": "success",
            "model_info": {
              "model_id": "local-0#model",
              "model_version": "xxx"
            },
            "namespace": "experiment",
            "pipeline_dsl_path": "/data/projects/fate/fateflow/jobs/xxx/pipeline_dsl.json",
            "runtime_conf_on_party_path": "/data/projects/fate/fateflow/jobs/xxx/local/0/job_runtime_on_party_conf.json",
            "runtime_conf_path": "/data/projects/fate/fateflow/jobs/xxx/job_runtime_conf.json",
            "table_name": "breast_hetero_guest",
            "train_runtime_conf_path": "/data/projects/fate/fateflow/jobs/xxx/train_runtime_conf.json"
          }
        '404':
          description: download failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: required parameters are missing
  '/data/upload/history':
    post:
      summary: history of upload job info
      tags:
        - data-access
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                job_id:
                  type: string
                  example: 202103241706521313480
                limit:
                  type: integer
                  description: limit output
                  example: 1
      responses:
        '200':
          description: get success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    example: [{
                              "202103241706521313480": {
                                  "notes": "",
                                  "schema": {
                                      "header": "y,x0,x1,x2,x3,x4,x5,x6,x7,x8,x9",
                                      "sid": "id"
                                  },
                                  "upload_info": {
                                      "namespace": "experiment",
                                      "partition": 4,
                                      "table_name": "breast_hetero_guest",
                                      "upload_count": 569
                                  }
                              }
                          }
                      ]

        '404':
          description: get failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 100
                  retmsg:
                    type: string
                    example: server error


  '/table/bind':
    post:
      summary: bind a storage address to fate table
      tags:
        - table
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - engine
                - address
                - namespace
                - name
                - head
                - id_delimiter
                - partitions
              properties:
                engine:
                  type: string
                  example: mysql
                name:
                  type: string
                  example: breast_hetero_guest
                namespace:
                  type: string
                  example: experiment
                address:
                  type: object
                  description: storage address
                  example:
                    user: fate
                    passwd: fate
                    host: 127.0.0.1
                    port: 3306
                    db: xxx
                    name: xxx
                partitions:
                  type: integer
                  description: fate computing table partitions
                  example: 16
                head:
                  type: integer
                  description: 1 means data have head
                  example: 0,1
                id_delimiter:
                  type: string
                  description: data table or intermediate storage table delimiter
                  example: ","
                in_serialized:
                  type: integer
                  description: data serialized, standlone/eggroll/mysql/path storage default 1, others default 0
                  example: 0, 1
                drop:
                  type: integer
                  description: if table is exist, will delete it
                  example: 0,1
                id_column:
                  type: string
                  example: "id"
                feature_column:
                  type: string
                  description: delimited by ","
                  example: x1,x2,x3

      responses:
        '200':
          description: bind table success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    properties:
                      table_name:
                        type: string
                        example: breast_hetero_guest
                      namespace:
                        type: string
                        example: experiment
        '404':
          description: bind table failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 100
                  retmsg:
                    type: string
                    example: engine xxx address xxx check failed
  '/table/delete':
    post:
      summary: delete fate table
      tags:
        - table
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - table_name
                - namespace
              properties:
                table_name:
                  type: string
                  example: breast_hetero_guest
                namespace:
                  type: string
                  example: experiment
      responses:
        '200':
          description: delete table success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    properties:
                      table_name:
                        type: string
                        example: breast_hetero_guest
                      namespace:
                        type: string
                        example: experiment
        '404':
          description: delete table failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: no find table
  '/table/list':
    post:
      summary: get job all tables
      tags:
        - table
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - job_id
                - role
                - party_id
              properties:
                job_id:
                  type: string
                  example: 202101251515021092240
                role:
                  type: string
                  example: guest
                party_id:
                  type: string
                  example: 10000
      responses:
        '200':
          description: get tables success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    example: {"Reader_0":{"input":{"table":{"name":"xxx","namespace":"xxxx"}},"output":{"data_0":{"name":"xxx","namespace":"xxx"}}},"DataIO_0":{"input":{"Reader_0.data_0":{"name":"xxx","namespace":"xxx"}},"output":{"data_0":{"name":"xxx","namespace":"xxx"}}},"Intersection_0":{"input":{"DataIO_0.data_0":{"name":"xxx","namespace":"xxx"}},"output":{"data_0":{"name":"xxx","namespace":"xxx"}}}}

        '404':
          description: delete table failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: no find table
  '/table/table_info':
    post:
      summary: query table info
      tags:
        - table
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - table_name
                - namespace
              properties:
                table_name:
                  type: string
                  example: breast_hetero_guest
                namespace:
                  type: string
                  example: experiment

      responses:
        '200':
          description: get tables success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    example: {
        "address": {xxx},
        "count": 569,
        "exist": 1,
        "table_name": "breast_hetero_guest",
        "namespace": "experiment",
        "partition": 16,
        "schema": {"sid": "id", "header": "id, y,x0,x1,x2,x3,x4,x5,x6,x7,x8,x9"}
    }

        '404':
          description: query table failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: no find table
  '/table/tracking/source':
    post:
      summary: tracking table source
      tags:
        - table
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - table_name
                - namespace
              properties:
                table_name:
                  type: string
                  example: breast_hetero_guest
                namespace:
                  type: string
                  example: experiment

      responses:
        '200':
          description: tracking success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    example: [{"parent_table_name":"xxx","parent_table_namespace":"xxx","source_table_name":"xxx","source_table_namespace":"xxx"}]
        '404':
          description: tracking failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: no find table
  '/table/tracking/job':
    post:
      summary: tracking using table job
      tags:
        - table
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - table_name
                - namespace
              properties:
                table_name:
                  type: string
                  example: breast_hetero_guest
                namespace:
                  type: string
                  example: experiment

      responses:
        '200':
          description: tracking success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    example: {"count":5,"job":["202104212104472450460","202104212127150470680","202104220937051579910","202104212038599210200","202104212131462630720"]}
        '404':
          description: tracking failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: no find table

  '/job/submit':
    post:
      summary: submit job
      tags:
        - job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - dsl
                - runtime_conf
              properties:
                dsl:
                  type: object
                  example: {
                    "components": {
                      "reader_0": {
                        "module": "Reader",
                        "output": {
                          "data": [
                            "table"
                          ]
                        }
                      },
                      "dataio_0": {
                        "module": "DataIO",
                        "input": {
                          "data": {
                            "data": [
                              "reader_0.table"
                            ]
                          }
                        },
                        "output": {
                          "data": [
                            "train"
                          ],
                          "model": [
                            "dataio"
                          ]
                        },
                        "need_deploy": true
                      },
                      "intersection_0": {
                        "module": "Intersection",
                        "input": {
                          "data": {
                            "data": [
                              "dataio_0.train"
                            ]
                          }
                        },
                        "output": {
                          "data": [
                            "train"
                          ]
                        }
                      },
                      "hetero_feature_binning_0": {
                        "module": "HeteroFeatureBinning",
                        "input": {
                          "data": {
                            "data": [
                              "intersection_0.train"
                            ]
                          }
                        },
                        "output": {
                          "data": [
                            "train"
                          ],
                          "model": [
                            "hetero_feature_binning"
                          ]
                        }
                      },
                      "hetero_feature_selection_0": {
                        "module": "HeteroFeatureSelection",
                        "input": {
                          "data": {
                            "data": [
                              "hetero_feature_binning_0.train"
                            ]
                          },
                          "isometric_model": [
                            "hetero_feature_binning_0.hetero_feature_binning"
                          ]
                        },
                        "output": {
                          "data": [
                            "train"
                          ],
                          "model": [
                            "selected"
                          ]
                        }
                      },
                      "hetero_lr_0": {
                        "module": "HeteroLR",
                        "input": {
                          "data": {
                            "train_data": [
                              "hetero_feature_selection_0.train"
                            ]
                          }
                        },
                        "output": {
                          "data": [
                            "train"
                          ],
                          "model": [
                            "hetero_lr"
                          ]
                        }
                      },
                      "evaluation_0": {
                        "module": "Evaluation",
                        "input": {
                          "data": {
                            "data": [
                              "hetero_lr_0.train"
                            ]
                          }
                        },
                        "output": {
                          "data": [
                            "evaluate"
                          ]
                        }
                      }
                    }
                  }

                runtime_conf:
                  type: object
                  example: {
                    "dsl_version": "2",
                    "initiator": {
                      "role": "guest",
                      "party_id": 9999
                    },
                    "role": {
                      "guest": [9999],
                      "host": [10000],
                      "arbiter": [10000]
                    },
                    "job_parameters": {
                      "common": {
                        "task_parallelism": 2,
                        "computing_partitions": 8,
                        "task_cores": 4,
                        "auto_retries": 1
                      }
                    },
                    "component_parameters": {
                      "common": {
                        "intersection_0": {
                          "intersect_method": "raw",
                          "sync_intersect_ids": true,
                          "only_output_key": false
                        },
                        "hetero_lr_0": {
                          "penalty": "L2",
                          "optimizer": "rmsprop",
                          "alpha": 0.01,
                          "max_iter": 3,
                          "batch_size": 320,
                          "learning_rate": 0.15,
                          "init_param": {
                            "init_method": "random_uniform"
                          }
                        }
                      },
                      "role": {
                        "guest": {
                          "0": {
                            "reader_0": {
                              "table": {
                                "name": "breast_hetero_guest",
                                "namespace": "experiment"
                              }
                            },
                            "dataio_0": {
                              "with_label": true,
                              "label_name": "y",
                              "label_type": "int",
                              "output_format": "dense"
                            }
                          }
                        },
                        "host": {
                          "0": {
                            "reader_0": {
                              "table": {
                                "name": "breast_hetero_host",
                                "namespace": "experiment"
                              }
                            },
                            "dataio_0": {
                              "with_label": false,
                              "output_format": "dense"
                            },
                            "evaluation_0": {"need_run": false}
                          }
                        }
                      }
                    }
                  }
      responses:
        '200':
          description: submit job success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    example: {"board_url":"xxx","code":0,"dsl_path":"xxx","job_id":"xxx","logs_directory":"xxx","message":"success","model_info":{"model_id":"xxx","model_version":"xxx"},"pipeline_dsl_path":"xxx","runtime_conf_on_party_path":"xxx","runtime_conf_path":"xxx","train_runtime_conf_path":"xxx"}
        '404':
          description: submit job failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: "config error"
  '/job/stop':
    post:
      summary: stop job
      tags:
        - job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - job_id
              properties:
                job_id:
                  type: string
                  example: 202103231958539401540
                stop_status:
                  type: string
                  default: cancel
                  example: "failed"
                  description: "failed or cancel"

      responses:
        '200':
          description: stop job success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
        '404':
          description: stop job failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: no find job
  '/job/rerun':
    post:
      summary: rerun job
      tags:
        - job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - job_id
              properties:
                job_id:
                  type: string
                  example: 202103231958539401540

      responses:
        '200':
          description: rerun job success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
        '404':
          description: rerun job failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: no find job
  '/job/query':
    post:
      summary: query job
      tags:
        - job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - job_id
              properties:
                job_id:
                  type: string
                  example: xxx

      responses:
        '200':
          description: query job success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    example: [
                      {
                        "f_apply_resource_time": xxx,
                        "f_cancel_signal": false,
                        "f_cancel_time": xxx,
                        "f_cores": 8,
                        "f_create_date": "xxx",
                        "f_create_time": xxx,
                        "f_description": "",
                        "f_dsl": {},
                        "f_elapsed": 14380,
                        "f_end_date": "xxx",
                        "f_end_scheduling_updates": 1,
                        "f_end_time": xxx,
                        "f_engine_name": "EGGROLL",
                        "f_engine_type": "computing",
                        "f_initiator_party_id": "20001",
                        "f_initiator_role": "guest",
                        "f_is_initiator": true,
                        "f_job_id": "xxx",
                        "f_memory": 0,
                        "f_name": "",
                        "f_party_id": "20001",
                        "f_progress": 14,
                        "f_ready_signal": false,
                        "f_ready_time": null,
                        "f_remaining_cores": 8,
                        "f_remaining_memory": 0,
                        "f_rerun_signal": false,
                        "f_resource_in_use": false,
                        "f_return_resource_time": xxx,
                        "f_role": "guest",
                        "f_roles": {},
                        "f_runtime_conf": {},
                        "f_runtime_conf_on_party": {},
                        "f_start_date": "xxx",
                        "f_start_time": xxx,
                        "f_status": "failed",
                        "f_status_code": null,
                        "f_tag": "job_end",
                        "f_train_runtime_conf": {},
                        "f_update_date": "xxx",
                        "f_update_time": xxx,
                        "f_user": {},
                        "f_user_id": ""
                      }
                    ]
        '404':
          description: query job failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: no find job
  '/job/list/job':
    post:
      summary: get job list
      tags:
        - job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                limit:
                  type: string
                  example: 10

      responses:
        '200':
          description: get job list success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
        '404':
          description: get job list failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: no find job
  '/job/update':
    post:
      summary: job notes
      tags:
        - job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - job_id
                - role
                - party_id
                - notes
              properties:
                job_id:
                  type: string
                  example: "2022xxx"
                role:
                  type: string
                  example: guest
                party_id:
                  type: integer
                  example: 10000
                notes:
                  type: string
                  example: this is a test


      responses:
        '200':
          description: success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
        '404':
          description: failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: no find job
  '/job/parameter/update':
    post:
      summary: update job parameter
      tags:
        - job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - job_id
              properties:
                job_id:
                  type: string
                  example: "2022xxx"
                component_parameters:
                  type: object
                  example: {"common": {"hetero_lr_0": {"max_iter": 10}}}
                job_parameters:
                  type: object
                  example: {"common": {"auto_retries": 2}}

      responses:
        '200':
          description: success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    example: {
                      "component_parameters":{"common":{"hetero_lr_0":{"alpha":0.01,"batch_size":320,"init_param":{"init_method":"random_uniform"},"learning_rate":0.15,"max_iter":10,"optimizer":"rmsprop","penalty":"L2"},"intersection_0":{"intersect_method":"raw","only_output_key":false,"sync_intersect_ids":true}},"role":{"guest":{"0":{"dataio_0":{"label_name":"y","label_type":"int","output_format":"dense","with_label":true},"reader_0":{"table":{"name":"breast_hetero_guest","namespace":"experiment"}}}},"host":{"0":{"dataio_0":{"output_format":"dense","with_label":false},"evaluation_0":{"need_run":false},"reader_0":{"table":{"name":"breast_hetero_host","namespace":"experiment"}}}}}},"components":[],"job_parameters":{"common":{"adaptation_parameters":{"if_initiator_baseline":true,"request_task_cores":4,"task_cores_per_node":4,"task_memory_per_node":0,"task_nodes":1},"auto_retries":2,"auto_retry_delay":1,"computing_engine":"EGGROLL","computing_partitions":4,"eggroll_run":{},"engines_address":{},"federated_mode":"MULTIPLE","federated_status_collect_type":"PUSH","inheritance_info":{},"job_type":"train","model_id":"arbiter-10001#guest-20001#host-10001#model","model_version":"202204251958539401540","pulsar_run":{},"rabbitmq_run":{},"spark_run":{},"task_parallelism":1}},"src_party_id":"20001","src_role":"guest"}
        '404':
          description: failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: no find job
  '/job/config':
    post:
      summary: job config
      tags:
        - job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - job_id
              properties:
                job_id:
                  type: string
                  example: "2022xxx"
                role:
                  type: string
                  example: guest
                party_id:
                  type: integer
                  example: 10000

      responses:
        '200':
          description: success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    example: {"job_id": "xxx", "dsl": {}, "runtime_conf": {}, "train_runtime_conf": {}, "model_info": {}}
        '404':
          description: failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: no find job
  '/job/log/download':
    post:
      summary: download job log (tar.gz)
      tags:
        - job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - job_id
              properties:
                job_id:
                  type: string
                  example: "xxx"
      responses:
        '200':
          description: get job log success
          content:
            application/octet-stream:
              schema:
                type: string
                example: ""
                description: file xxx_log.tar.gz

        '404':
          description: get job list failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 404
                  retmsg:
                    type: string
                    example: Log file path xxx not found. Please check if the job id is valid.
  '/job/log/path':
    post:
      summary: job log path
      tags:
        - job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - job_id
              properties:
                job_id:
                  type: string
                  example: "xxx"

      responses:
        '200':
          description: success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    example: {"logs_directory":"/data/projects/fate/fateflow/logs/xxx"}
        '404':
          description: failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: no find job
  '/job/task/query':
    post:
      summary: query task
      tags:
        - job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - job_id
              properties:
                job_id:
                  type: string
                  example: "xxx"
                role:
                  type: string
                  example: guest
                party_id:
                  type: integer
                  example: 10000
                component_name:
                  type: string
                  example: reader_0
      responses:
        '200':
          description: success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    example: [{}]
                    description: "[{task_info}]"
        '404':
          description: failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: no find task
  '/job/list/task':
    post:
      summary: get task list
      tags:
        - job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                limit:
                  type: integer
                  example: 5
      responses:
        '200':
          description: success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    example: {"count": 5, "tasks": [{},{},{},{},{}]}
                    description: "[{task_info}]"
        '404':
          description: failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: no find task
  '/job/clean':
    post:
      summary: clean job
      tags:
        - job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              required:
                - job_id
              type: object
              properties:
                job_id:
                  type: string
                  example: xxx
                role:
                  type: string
                  example: guest
                party_id:
                  type: integer
                  example: 10000
                component_name:
                  type: string
                  example: reader_0
      responses:
        '200':
          description: success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
        '404':
          description: failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: no find task
  '/job/clean/queue':
    post:
      summary: cancel waiting job
      tags:
        - job
      responses:
        '200':
          description: success
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 0
                  retmsg:
                    type: string
                    example: success
                  data:
                    type: object
                    example: {"202204261616186991350":0,"202204261616198643190":0,"202204261616210073410":0}
        '404':
          description: failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  retcode:
                    type: integer
                    example: 101
                  retmsg:
                    type: string
                    example: server error



tags:
  - name: data-access
  - name: table
  - name: job


servers:
  - description: Default Server URL
    url: http://localhost:9380/v1