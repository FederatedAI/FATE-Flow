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
# -----------------------------------------------------------------------------
# Service Control Script for a FATE Flow Server Application
# -----------------------------------------------------------------------------
#
# This script is used to manage the lifecycle (start, stop, restart, and check status) of a server application.
# The server application listens on two ports: an HTTP port and a gRPC port.
# The settings for these ports, as well as other configurations, are read from a YAML file.
#
# Dependencies:
#   - lsof: To check which processes are listening on which ports.
#   - sed, awk: For text processing, mainly for parsing the YAML configuration.
#
# Usage:
#   ./service.sh {start|stop|status|restart [sleep_time]}
#   sleep_time: Optional. Number of seconds to wait between stop and start during restart. Default is 10 seconds.
#
# Assumptions:
#   - The script assumes the presence of a configuration file named 'service_conf.yaml' in a relative directory.
#   - The configuration file is structured in a specific way that the parsing logic expects.
#
# -----------------------------------------------------------------------------
FATE_FLOW_BASE=$1
LOG_DIR=$FATE_FLOW_BASE/logs


# --------------- Color Definitions ---------------
esc_c="\e[0m"
error_c="\e[31m"
ok_c="\e[32m"
highlight_c="\e[43m"

# --------------- Logging Functions ---------------
print_info() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local overwrite=$2

    # Check if we need to overwrite the current line
    if [ "$overwrite" == "overwrite" ]; then
        echo -ne "\r${ok_c}[${timestamp}][MS]${esc_c} $1"
    else
        echo -e "${ok_c}[${timestamp}][MS]${esc_c} $1"
    fi
}
print_ok() {
    local overwrite=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    if [ "$overwrite" == "overwrite" ]; then
        echo -ne "\r${ok_c}[${timestamp}][OK]${esc_c} $1"
    else
        echo -e "${ok_c}[${timestamp}][OK]${esc_c} $1"
    fi
}

print_error() {
    local overwrite=$3
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    if [ "$overwrite" == "overwrite" ]; then
        echo -ne "\r${error_c}[${timestamp}][ER]${esc_c} $1: $2"
    else
        echo -e "${error_c}[${timestamp}][ER]${esc_c} $1: $2"
    fi
}

# --------------- Util Functions ---------------
# Check if the dependencies are installed on the system
check_dependencies() {
    local missing_deps=0

    for dep in lsof sed awk; do
        if ! command -v "$dep" &>/dev/null; then
            print_error "Missing dependency" "$dep"
            missing_deps=1
        fi
    done

    if [ "$missing_deps" -eq 1 ]; then
        print_error "Please install the missing dependencies and try again."
        exit 1
    fi
}

# Get the PID of the process using a specific port
get_pid() {
    local port=$1
    lsof -i:${port} | grep 'LISTEN' | awk 'NR==1 {print $2}'
}

# Extract the specified port from a specified section of the YAML file
get_port_from_yaml() {
    local yaml_file=$1
    local section=$2
    local port_key=$3
    local s='[[:space:]]*'
    local w='[a-zA-Z0-9_]*'
    local fs=$(echo @ | tr @ '\034') # Set fs back to the ASCII "file separator"

    sed -ne "s|^\($s\)\($w\)$s:$s\"\(.*\)\"$s\$|\1$fs\2$fs\3|p" \
        -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p" $yaml_file |
        awk -F$fs -v section="$section" -v port_key="$port_key" '
    {
        indent = length($1)/2;
        vname[indent] = $2;
        for (i in vname) {if (i > indent) {delete vname[i]}}
        if (length($3) > 0) {
            vn="";
            for (i=0; i<indent; i++) {
                vn=(vn ? vn "." : "") vname[i];  # Concatenate using a dot
            }
            if (vn == section && $2 == port_key) print $3;
        }
    }'
}

# Function to load configuration details from the YAML file
load_config() {
    print_info "-------------------------------load config-------------------------------"
    check_dependencies
    ENTRYPOINT=${FATE_FLOW_BASE}/fate_flow_server.py
    if [ ! -f "${ENTRYPOINT}" ]; then
        print_error "Service entrypoint not found." ${ENTRYPOINT}
        exit 1
    fi

    # Logs

    [ ! -d "${LOG_DIR}" ] && mkdir -p "${LOG_DIR}"
    LOG_STDERR="${LOG_DIR}/error.log"
    LOG_STDOUT="${LOG_DIR}/console.log"

    print_info "Checking service configuration..."
    CONF_PATH="${FATE_FLOW_BASE}/conf/service_conf.yaml"
    if [ -f "${CONF_PATH}" ]; then
        print_ok "Service configuration file found." ${CONF_PATH}
    else
        print_error "Service configuration not found." ${CONF_PATH}
        exit 1
    fi

    # load ports
    print_info "Retrieving http port..."
    local section="fateflow"
    http_port=$(get_port_from_yaml $CONF_PATH $section "http_port")
    if [ -z "$http_port" ]; then
        print_error "Retrieve http port failed" "please check ${CONF_PATH}"
        exit 1
    else
        print_ok "HTTP port set to ${highlight_c}${http_port}${esc_c}"
    fi
    print_info "Retrieving gPRC port..."
    grpc_port=$(get_port_from_yaml $CONF_PATH $section "grpc_port")
    if [ -z "$grpc_port" ]; then
        print_error "Retrieve gRPC port failed" "please check ${CONF_PATH}"
        exit 1
    else
        print_ok "gRPC port set to ${highlight_c}${grpc_port}${esc_c}"
    fi

}

# --------------- Functions for start---------------
# Check if the service is up and running
check_service_up() {
    local pid=$1
    local timeout_ms=$2
    local interval_ms=$3
    local http_port=$4
    local grpc_port=$5
    local elapsed_ms=0
    local spin_state=0

    while ((elapsed_ms < timeout_ms)); do
        if ! kill -0 "${pid}" 2>/dev/null; then
            print_error "Process with PID ${pid} is not running." "" "overwrite"
            echo
            return 1
        fi

        if lsof -i :${http_port} | grep -q LISTEN && lsof -i :${grpc_port} | grep -q LISTEN; then
            print_ok "Service started successfully!" "overwrite"
            echo
            return 0
        fi

        # Update spinning wheel
        case $spin_state in
            0) spinner_char="/" ;;
            1) spinner_char="-" ;;
            2) spinner_char="\\" ;;
            3) spinner_char="|" ;;
        esac
        print_info "$spinner_char" "overwrite"
        spin_state=$(((spin_state + 1) % 4))
        sleep $((interval_ms / 1000)).$((interval_ms % 1000))
        elapsed_ms=$((elapsed_ms + interval_ms))
    done
    print_error "Service did not start up within the expected time." "" "overwrite"
    echo
    return 1
}
# Draw a progress bar for visual feedback
draw_progress_bar() {
    local completed=$1
    local total=$2
    local msg="$3"
    local progress_bar="["

    # Print completed part
    for ((i = 0; i < completed; i++)); do
        progress_bar+=" "
    done

    # Print pending part
    for ((i = completed; i < total; i++)); do
        progress_bar+="-"
    done
    progress_bar+="]${msg}"
    print_info "$progress_bar" "overwrite"
}

# Checks if a port is active and returns the PID of the process using it.
# Parameters:
#   $1 - The port number to check.
# Returns:
#   PID of the process using the port, or an empty string if the port is not active.
check_port_active() {
    local port=$1
    lsof -i:${port} | grep 'LISTEN' | awk 'NR==1 {print $2}'
}

# Start service
start() {
    print_info "--------------------------------starting--------------------------------"
    print_info "Verifying if HTTP port ${highlight_c}${http_port}${esc_c} is not active..."
    pid1=$(check_port_active $http_port)
    if [ -n "${pid1}" ]; then
        print_error "HTTP port ${highlight_c}${http_port}${esc_c} is already active. Process ID (PID): ${highlight_c}${pid1}${esc_c}"
        exit 1
    else
        print_ok "HTTP port ${highlight_c}${http_port}${esc_c} not active"
    fi

    print_info "Verifying if gRPC port ${highlight_c}${grpc_port}${esc_c} is not active..."
    pid2=$(check_port_active $grpc_port)
    if [ -n "${pid2}" ]; then
        print_error "gRPC port ${highlight_c}${grpc_port}${esc_c} is already active. Process ID (PID): ${highlight_c}${pid2}${esc_c}"
        exit 1
    else
        print_ok "gRPC port ${highlight_c}${grpc_port}${esc_c} not active"
    fi

    print_info "Starting services..."
    local startup_error_tmp=$(mktemp)
    #    nohup python "${FATE_FLOW_BASE}/fate_flow_server.py" >>"${LOG_STDOUT}" 2> >(tee -a "${LOG_STDERR}" >>"${startup_error_tmp}") &
    nohup python $FATE_FLOW_BASE/fate_flow_server.py  >> "${LOG_STDOUT}" 2>>"${LOG_STDERR}" &
    pid=$!
    print_info "Process ID (PID): ${highlight_c}${pid}${esc_c}"
    if ! check_service_up "${pid}" 5000 250 ${http_port} ${grpc_port}; then
        print_info "stderr:"
        cat "${startup_error_tmp}"
        rm "${startup_error_tmp}"
        print_info "Please check ${LOG_STDERR} and ${LOG_STDOUT} for more details"
        exit 1
    fi
}

# --------------- Functions for stop---------------
# Function to kill a process
kill_process() {
    local pid=$1
    local signal=$2
    kill ${signal} "${pid}" 2>/dev/null
}

# Stop service
stop_port() {
    local port=$1
    local name=$2
    local pid=$(get_pid ${port})

    print_info "Stopping $name ${highlight_c}${port}${esc_c}..."
    if [ -n "${pid}" ]; then
        for _ in {1..100}; do
            sleep 0.1
            kill_process "${pid}"
            pid=$(get_pid ${port})
            if [ -z "${pid}" ]; then
                print_ok "Stop $name ${highlight_c}${port}${esc_c} success (SIGTERM)"
                return
            fi
        done
        kill_process "${pid}" -9 && print_ok "Stop port success (SIGKILL)" || print_error "Stop port failed"
    else
        print_ok "Stop $name ${highlight_c}${port}${esc_c} success(NOT ACTIVE)"
    fi
}
stop() {
    print_info "--------------------------------stopping--------------------------------"
    stop_port ${http_port} "HTTP port"
    stop_port ${grpc_port} "gRPC port"
}

# --------------- Functions for status---------------
# Check the status of the service
status() {
    print_info "---------------------------------status---------------------------------"
    # Check http_port
    pid1=$(check_port_active $http_port)
    if [ -n "${pid1}" ]; then
        print_ok "Check http port ${highlight_c}${http_port}${esc_c} is active: PID=${highlight_c}${pid1}${esc_c}"
    else
        print_error "http port not active"
    fi

    # Check grpc_port
    pid2=$(check_port_active $grpc_port)
    if [ -n "${pid2}" ]; then
        print_ok "Check grpc port ${highlight_c}${grpc_port}${esc_c} is active: PID=${highlight_c}${pid2}${esc_c}"
    else
        print_error "grpc port not active"
    fi

    # Check if both PIDs are the same
    if [ -n "${pid1}" ] && [ -n "${pid2}" ]; then
        if [ "${pid1}" == "${pid2}" ]; then
            print_ok "Check http port and grpc port from same process: PID=${highlight_c}${pid2}${esc_c}"
        else
            print_error "Found http port and grpc port active but from different process: ${highlight_c}${pid2}${esc_c}!=${highlight_c}${pid2}${esc_c}"
        fi
    fi
}

# --------------- Functions for info---------------
# Print usage information for the script
print_usage() {
    echo -e "${ok_c}FATE Flow${esc_c}"
    echo "---------"
    echo -e "${ok_c}Usage:${esc_c}"
    echo -e "  $0 start          - Start the server application."
    echo -e "  $0 stop           - Stop the server application."
    echo -e "  $0 status         - Check and report the status of the server application."
    echo -e "  $0 restart [time] - Restart the server application. Optionally, specify a sleep time (in seconds) between stop and start."
    echo ""
    echo -e "${ok_c}Examples:${esc_c}"
    echo "  $0 start"
    echo "  $0 restart 5"
    echo ""
    echo -e "${ok_c}Notes:${esc_c}"
    echo "  - The restart command, if given an optional sleep time, will wait for the specified number of seconds between stopping and starting the service."
    echo "    If not provided, it defaults to 10 seconds."
    echo "  - Ensure that the required configuration file 'service_conf.yaml' is properly set up in the expected directory."
    echo ""
    echo "For more detailed information, refer to the script's documentation or visit the official documentation website."
}

# --------------- Main---------------
# Main case for control
case "$2" in
    start)
        load_config
        start
        status
        ;;
    starting)
        load_config
        start front
        ;;
    stop)
        load_config
        stop
        ;;
    status)
        load_config
        status
        ;;
    restart)
        load_config
        stop
        sleep_time=${2:-5}
        print_info "Waiting ${sleep_time} seconds"
        sleep $sleep_time
        start
        status
        ;;
    *)
        print_usage
        exit 1
        ;;
esac
