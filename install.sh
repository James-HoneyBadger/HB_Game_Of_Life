#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
REQUIREMENTS_FILE="$ROOT_DIR/requirements.txt"

log() {
  echo "[lifegrid-install] $*"
}

detect_pkg_manager() {
  if command -v dnf >/dev/null 2>&1; then
    echo "dnf"
    return
  fi
  if command -v apt-get >/dev/null 2>&1; then
    echo "apt"
    return
  fi
  if command -v pacman >/dev/null 2>&1; then
    echo "pacman"
    return
  fi
  if command -v zypper >/dev/null 2>&1; then
    echo "zypper"
    return
  fi
  echo ""
}

run_as_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
    return
  fi

  if command -v sudo >/dev/null 2>&1; then
    sudo "$@"
    return
  fi

  log "Need root privileges to install system dependencies, but sudo is unavailable."
  return 1
}

install_packages() {
  local manager="$1"
  shift

  case "$manager" in
    dnf)
      run_as_root dnf -y install "$@"
      ;;
    apt)
      run_as_root apt-get update
      run_as_root apt-get -y install "$@"
      ;;
    pacman)
      run_as_root pacman --noconfirm -Sy "$@"
      ;;
    zypper)
      run_as_root zypper --non-interactive install "$@"
      ;;
    *)
      return 1
      ;;
  esac
}

ensure_system_dependencies() {
  local manager
  manager="$(detect_pkg_manager)"

  if ! command -v python3 >/dev/null 2>&1; then
    log "python3 is missing. Attempting to install it."
    case "$manager" in
      dnf) install_packages "$manager" python3 ;;
      apt) install_packages "$manager" python3 ;;
      pacman) install_packages "$manager" python ;;
      zypper) install_packages "$manager" python3 ;;
      *)
        log "No supported package manager found to install python3 automatically."
        return 1
        ;;
    esac
  fi

  if ! python3 - <<'PY' >/dev/null 2>&1
import tkinter
PY
  then
    log "tkinter is missing. Attempting to install it."
    case "$manager" in
      dnf) install_packages "$manager" python3-tkinter ;;
      apt) install_packages "$manager" python3-tk ;;
      pacman) install_packages "$manager" tk ;;
      zypper) install_packages "$manager" python3-tk ;;
      *)
        log "No supported package manager found to install tkinter automatically."
        return 1
        ;;
    esac
  fi

  if ! python3 - <<'PY' >/dev/null 2>&1
import venv
PY
  then
    log "python venv module is missing. Attempting to install it."
    case "$manager" in
      dnf) install_packages "$manager" python3-pip ;;
      apt) install_packages "$manager" python3-venv python3-pip ;;
      pacman) install_packages "$manager" python-pip ;;
      zypper) install_packages "$manager" python3-pip ;;
      *)
        log "No supported package manager found to install python venv/pip automatically."
        return 1
        ;;
    esac
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    log "python3 is still missing after auto-install attempt."
    return 1
  fi

  if ! python3 - <<'PY' >/dev/null 2>&1
import tkinter
PY
  then
    log "tkinter is still missing after auto-install attempt."
    return 1
  fi
}

check_python_version() {
  python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11+ is required")
PY
}

ensure_requirements_file() {
  if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
    log "Missing requirements file: $REQUIREMENTS_FILE"
    return 1
  fi
}

setup_virtualenv() {
  if [[ ! -x "$VENV_DIR/bin/python" || ! -f "$VENV_DIR/bin/activate" ]]; then
    if [[ -d "$VENV_DIR" ]]; then
      log "Repairing incomplete virtual environment at $VENV_DIR"
    else
      log "Creating virtual environment at $VENV_DIR"
    fi
    python3 -m venv --clear "$VENV_DIR"
  fi

  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"

  log "Upgrading pip when possible"
  if ! python -m pip install --upgrade pip; then
    log "Could not upgrade pip (possibly offline). Continuing with existing pip."
  fi

  log "Installing Python requirements"
  python -m pip install -r "$REQUIREMENTS_FILE"

  log "Installing LifeGrid in editable mode"
  python -m pip install -e "$ROOT_DIR"
}

main() {
  log "Checking and installing system dependencies"
  ensure_system_dependencies

  log "Checking Python version"
  check_python_version

  ensure_requirements_file

  setup_virtualenv

  log "Installation complete"
  log "Run the simulation with: ./run.sh"
}

main "$@"
