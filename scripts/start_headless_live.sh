#!/usr/bin/env bash
# shellcheck disable=SC1091
#
# Headless launcher for LiveTradingRuntime.
#  - Activates the `quant_env` conda environment
#  - Runs the unattended live trading loop (Alpaca ready)
#  - Respects environment variables such as ALPACA_API_KEY, LIVE_SYMBOLS, etc.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Activate conda (assumes Miniconda installed under $HOME/miniconda)
if [[ -f "${HOME}/miniconda/etc/profile.d/conda.sh" ]]; then
    # shellcheck source=/dev/null
    source "${HOME}/miniconda/etc/profile.d/conda.sh"
elif [[ -f "/opt/conda/etc/profile.d/conda.sh" ]]; then
    # shellcheck source=/dev/null
    source "/opt/conda/etc/profile.d/conda.sh"
else
    echo "Unable to locate conda.sh. Please adjust the path in scripts/start_headless_live.sh."
    exit 1
fi

conda activate quant_env

cd "${PROJECT_ROOT}"

python scripts/run_headless_live.py \
  --symbols "${LIVE_SYMBOLS:-AAPL,MSFT,TSLA}" \
  --provider "${LIVE_PROVIDER:-alpaca}" \
  --poll-interval "${LIVE_POLL_INTERVAL:-5}" \
  --reconcile-interval "${LIVE_RECONCILE_INTERVAL:-30}"
