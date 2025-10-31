#!/usr/bin/env bash
# shellcheck disable=SC1091
#
# Install or update the systemd service that keeps the headless live runtime running.
#
# Usage:
#   sudo bash scripts/install_quant_service.sh \
#       --project-root /opt/quant_trading \
#       --env-file /etc/quant_trading.env \
#       --conda-profile /opt/conda/etc/profile.d/conda.sh
#

set -euo pipefail

PROJECT_ROOT="/opt/quant_trading"
ENV_FILE="/etc/quant_trading.env"
CONDA_PROFILE="/opt/conda/etc/profile.d/conda.sh"
SERVICE_NAME="quant-trading.service"
SYSTEMD_PATH="/etc/systemd/system/${SERVICE_NAME}"
USER_NAME="azureuser"

usage() {
    cat <<EOF
Usage: sudo $0 [options]

Options:
  --project-root PATH     项目根目录 (默认: ${PROJECT_ROOT})
  --env-file PATH         环境变量文件路径 (默认: ${ENV_FILE})
  --conda-profile PATH    conda.sh 路径 (默认: ${CONDA_PROFILE})
  --user NAME             运行服务的用户 (默认: ${USER_NAME})
  --service-name NAME     systemd 服务名 (默认: ${SERVICE_NAME})
  --help                  显示本帮助
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project-root) PROJECT_ROOT="$2"; shift 2 ;;
        --env-file) ENV_FILE="$2"; shift 2 ;;
        --conda-profile) CONDA_PROFILE="$2"; shift 2 ;;
        --user) USER_NAME="$2"; shift 2 ;;
        --service-name) SERVICE_NAME="$2"; SYSTEMD_PATH="/etc/systemd/system/${SERVICE_NAME}"; shift 2 ;;
        --help) usage; exit 0 ;;
        *) echo "未知选项: $1"; usage; exit 1 ;;
    esac
done

if [[ $EUID -ne 0 ]]; then
    echo "请使用 sudo 执行此脚本。"
    exit 1
fi

if [[ ! -d "${PROJECT_ROOT}" ]]; then
    echo "项目目录不存在: ${PROJECT_ROOT}"
    exit 1
fi

START_SCRIPT="${PROJECT_ROOT}/scripts/start_headless_live.sh"
if [[ ! -x "${START_SCRIPT}" ]]; then
    echo "启动脚本不可执行: ${START_SCRIPT}"
    exit 1
fi

cat <<EOF | tee "${SYSTEMD_PATH}" >/dev/null
[Unit]
Description=Quant Trading Live Runtime
After=network.target

[Service]
Type=simple
WorkingDirectory=${PROJECT_ROOT}
EnvironmentFile=${ENV_FILE}
Environment=CONDA_PROFILE=${CONDA_PROFILE}
ExecStart=${START_SCRIPT}
Restart=on-failure
RestartSec=10
User=${USER_NAME}

[Install]
WantedBy=multi-user.target
EOF

echo "已写入 ${SYSTEMD_PATH}"

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"

echo "服务 ${SERVICE_NAME} 已启用，可用以下命令启动："
echo "  sudo systemctl start ${SERVICE_NAME}"
