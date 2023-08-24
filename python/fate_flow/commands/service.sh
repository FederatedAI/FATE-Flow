#!/bin/bash

#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

PROJECT_BASE=$1
LOG_DIR=$PROJECT_BASE/logs


parse_yaml() {
   local prefix=$2
   local s='[[:space:]]*' w='[a-zA-Z0-9_]*' fs=$(echo @|tr @ '\034')
   sed -ne "s|^\($s\)\($w\)$s:$s\"\(.*\)\"$s\$|\1$fs\2$fs\3|p" \
        -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p"  $1 |
   awk -F$fs '{
      indent = length($1)/2;
      vname[indent] = $2;
      for (i in vname) {if (i > indent) {delete vname[i]}}
      if (length($3) > 0) {
         vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
         printf("%s%s%s=\"%s\"\n", "'$prefix'",vn, $2, $3);
      }
   }'
}

getport() {
    service_conf_path=${PROJECT_BASE}/conf/service_conf.yaml
    if test -f "${service_conf_path}"; then
      eval $(parse_yaml ${service_conf_path} "service_config_")
      echo "fate flow http port: ${service_config_fateflow_http_port}, grpc port: ${service_config_fateflow_grpc_port}"
      echo
    else
      echo "service conf not found: ${service_conf_path}"
      exit
    fi
}

getport

getpid() {
    echo "check process by http port and grpc port"
    pid1=`lsof -i:${service_config_fateflow_http_port} | grep 'LISTEN' | awk 'NR==1 {print $2}'`
    pid2=`lsof -i:${service_config_fateflow_grpc_port} | grep 'LISTEN' | awk 'NR==1 {print $2}'`
    if [[ -n ${pid1} && "x"${pid1} = "x"${pid2} ]];then
        pid=$pid1
    elif [[ -z ${pid1} && -z ${pid2} ]];then
        pid=
    fi
}

mklogsdir() {
    if [[ ! -d $LOG_DIR ]]; then
        mkdir -p $LOG_DIR
    fi
}

status() {
    getpid
    if [[ -n ${pid} ]]; then
        echo "status:`ps aux | grep ${pid} | grep -v grep`"
        lsof -i:${service_config_fateflow_http_port} | grep 'LISTEN'
        lsof -i:${service_config_fateflow_grpc_port} | grep 'LISTEN'
    else
        echo "service not running"
    fi
}

start() {
    getpid
    if [[ ${pid} == "" ]]; then
        mklogsdir
        if [[ $1x == "front"x ]];then
          exec python $PROJECT_BASE/fate_flow_server.py >> "${LOG_DIR}/console.log" 2>>"${LOG_DIR}/error.log"
        else
          nohup python $PROJECT_BASE/fate_flow_server.py  >> "${LOG_DIR}/console.log" 2>>"${LOG_DIR}/error.log" &
        fi
        for((i=1;i<=100;i++));
        do
            sleep 0.1
            getpid
            if [[ -n ${pid} ]]; then
                echo "service start sucessfully. pid: ${pid}"
                return
            fi
        done
        if [[ -n ${pid} ]]; then
           echo "service start sucessfully. pid: ${pid}"
        else
           echo "service start failed, please check ${LOG_DIR}/error.log and ${LOG_DIR}/console.log"
        fi
    else
        echo "service already started. pid: ${pid}"
    fi
}

stop() {
    getpid
    if [[ -n ${pid} ]]; then
        echo "killing: `ps aux | grep ${pid} | grep -v grep`"
        for((i=1;i<=100;i++));
        do
            sleep 0.1
            kill ${pid}
            getpid
            if [[ ! -n ${pid} ]]; then
                echo "killed by SIGTERM"
                return
            fi
        done
        kill -9 ${pid}
        if [[ $? -eq 0 ]]; then
            echo "killed by SIGKILL"
        else
            echo "kill error"
        fi
    else
        echo "service not running"
    fi
}


case "$2" in
    start)
        start
        status
        ;;

    starting)
        start front
        ;;

    stop)
        stop
        ;;

    status)
        status
        ;;

    restart)
        stop
        sleep 2
        start
        status
        ;;
    *)
        echo "usage: $0 {start|stop|status|restart}"
        exit -1
esac
