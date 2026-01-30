#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
VPS 一键部署 dpw（可重复执行）

用法：
  bash scripts/deploy_vps.sh --dir /opt/dpw --repo <git_url> [--branch main] [--run-tests]

参数：
  --dir        部署目录（默认：/opt/dpw）
  --repo       Git 仓库地址（若在仓库目录内运行可省略）
  --branch     分支/标签（默认：main）
  --run-tests  部署后运行 pytest

示例（在本地一条命令远程部署）：
  ssh user@vps 'bash -s -- --dir /opt/dpw --repo https://github.com/xxx/dpw.git --branch main --run-tests' < scripts/deploy_vps.sh
EOF
}

DEPLOY_DIR="/opt/dpw"
REPO_URL=""
BRANCH="main"
RUN_TESTS="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir)
      DEPLOY_DIR="${2:?}"; shift 2;;
    --repo)
      REPO_URL="${2:?}"; shift 2;;
    --branch)
      BRANCH="${2:?}"; shift 2;;
    --run-tests)
      RUN_TESTS="1"; shift 1;;
    -h|--help)
      usage; exit 0;;
    *)
      echo "Unknown arg: $1" >&2
      usage; exit 2;;
  esac
done

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing command: $1" >&2; exit 1; }
}

need_cmd git
need_cmd python3

ensure_repo() {
  if [[ -d "$DEPLOY_DIR/.git" ]]; then
    return 0
  fi

  if [[ -z "$REPO_URL" ]]; then
    echo "Repo not found at $DEPLOY_DIR and --repo not provided." >&2
    exit 1
  fi

  mkdir -p "$DEPLOY_DIR"
  git clone "$REPO_URL" "$DEPLOY_DIR"
}

update_repo() {
  git -C "$DEPLOY_DIR" fetch --all --prune
  git -C "$DEPLOY_DIR" checkout -f "$BRANCH"
  git -C "$DEPLOY_DIR" pull --ff-only || true
}

setup_venv() {
  if [[ ! -d "$DEPLOY_DIR/.venv" ]]; then
    python3 -m venv "$DEPLOY_DIR/.venv"
  fi
  "$DEPLOY_DIR/.venv/bin/python" -m pip install -U pip
}

install_pkg() {
  local pip="$DEPLOY_DIR/.venv/bin/python -m pip"
  if [[ "$RUN_TESTS" == "1" ]]; then
    $pip install -e "$DEPLOY_DIR[dev]"
  else
    $pip install -e "$DEPLOY_DIR"
  fi
}

run_tests() {
  if [[ "$RUN_TESTS" != "1" ]]; then
    return 0
  fi
  "$DEPLOY_DIR/.venv/bin/python" -m pytest -q
}

echo "[1/4] Ensure repo..."
ensure_repo
echo "[2/4] Update repo ($BRANCH)..."
update_repo
echo "[3/4] Setup venv & install..."
setup_venv
install_pkg
echo "[4/4] Verify..."
run_tests

echo "OK: deployed to $DEPLOY_DIR"
echo "Use python: $DEPLOY_DIR/.venv/bin/python"

