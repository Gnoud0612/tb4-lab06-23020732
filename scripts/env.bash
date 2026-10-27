#!/usr/bin/env bash
TB4_WORKSPACE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export TB4_WORKSPACE PYTHONDONTWRITEBYTECODE=1
source "${TB4_WORKSPACE}/scripts/local_underlay.bash" || return 1
if [[ -f "${TB4_WORKSPACE}/install/local_setup.bash" ]]; then source "${TB4_WORKSPACE}/install/local_setup.bash"; fi
export ROS_DOMAIN_ID=56 ROS_LOCALHOST_ONLY=1
export IGN_PARTITION=tb4_lab_domain56 GZ_PARTITION=tb4_lab_domain56
export ROS_HOME="${TB4_WORKSPACE}/.runtime/ros" ROS_LOG_DIR="${TB4_WORKSPACE}/.runtime/ros_logs"
export IGN_LOG_PATH="${TB4_WORKSPACE}/.runtime/ign_logs" IGN_FUEL_CACHE_PATH="${TB4_WORKSPACE}/.runtime/fuel"
export XDG_CACHE_HOME="${TB4_WORKSPACE}/.runtime/cache" XDG_CONFIG_HOME="${TB4_WORKSPACE}/.runtime/config"
export XDG_DATA_HOME="${TB4_WORKSPACE}/.runtime/data" MPLCONFIGDIR="${TB4_WORKSPACE}/.runtime/matplotlib"
mkdir -p "${ROS_HOME}" "${ROS_LOG_DIR}" "${IGN_LOG_PATH}" "${IGN_FUEL_CACHE_PATH}" "${XDG_CACHE_HOME}" "${XDG_CONFIG_HOME}" "${XDG_DATA_HOME}"
if [[ -d "${TB4_WORKSPACE}/.venv/lib/python3.10/site-packages" ]]; then
 export PYTHONPATH="${TB4_WORKSPACE}/.venv/lib/python3.10/site-packages:${PYTHONPATH:-}"
fi
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 LP_NUM_THREADS=2 QT_X11_NO_MITSHM=1
