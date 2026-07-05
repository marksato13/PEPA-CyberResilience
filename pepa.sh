#!/usr/bin/env bash
set -euo pipefail

APP_NAME="PEPA CyberResilience"
DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PEPA_HOME="${PEPA_HOME:-$HOME/bigdata}"
PEPA_ENV="${PEPA_ENV:-$HOME/bigdata-env}"
PEPA_PORT="${PEPA_PORT:-8501}"
PEPA_HOST="${PEPA_HOST:-0.0.0.0}"
JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk-amd64}"
LIVE_CSV="${PEPA_LIVE_CSV:-$PEPA_HOME/output/live_events.csv}"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'

ok() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
info() { echo -e "${CYAN}[PEPA]${NC} $1"; }

usage() {
  cat <<'HELP'
PEPA CyberResilience - CLI de implementacion

Uso:
  ./pepa.sh install
  ./pepa.sh run --mode demo|lab|production
  ./pepa.sh pipeline
  ./pepa.sh status
  ./pepa.sh stop
  ./pepa.sh url
  ./pepa.sh logs

Modos:
  demo        Generador sintetico + dashboard
  lab         Pipeline/datasets propios + dashboard
  production Fuente real ya normalizada + dashboard

Ejemplos:
  ./pepa.sh install
  ./pepa.sh run --mode demo
  ./pepa.sh pipeline
  ./pepa.sh run --mode lab
  ./pepa.sh run --mode production
HELP
}

activate_env() {
  [ -d "$PEPA_ENV" ] || err "No existe el entorno $PEPA_ENV. Ejecuta: ./pepa.sh install"
  # shellcheck disable=SC1091
  source "$PEPA_ENV/bin/activate"
  export JAVA_HOME
  export HOME
}

ensure_dirs() {
  mkdir -p "$PEPA_HOME/scripts" "$PEPA_HOME/output" "$PEPA_HOME/logs" "$PEPA_HOME/tablas"
}

ensure_live_csv() {
  ensure_dirs
  if [ ! -f "$LIVE_CSV" ]; then
    echo 'timestamp,attack_type,severity,country,industry,data_GB,outcome,duration_min' > "$LIVE_CSV"
    ok "Feed vivo creado: $LIVE_CSV"
  fi
}

local_ip() {
  hostname -I 2>/dev/null | awk '{print $1}'
}

start_dashboard() {
  activate_env
  ensure_dirs
  pkill -f 'streamlit run' 2>/dev/null || true
  nohup python3 -m streamlit run "$PEPA_HOME/scripts/dashboard.py" \
    --server.port "$PEPA_PORT" \
    --server.address "$PEPA_HOST" \
    --server.headless true \
    > "$PEPA_HOME/logs/dashboard.log" 2>&1 &
  ok "Dashboard iniciado en puerto $PEPA_PORT"
}

start_generator() {
  activate_env
  ensure_live_csv
  pkill -f event_generator.py 2>/dev/null || true
  nohup python3 "$PEPA_HOME/scripts/event_generator.py" \
    > "$PEPA_HOME/logs/generator.log" 2>&1 &
  ok "Generador demo iniciado"
}

cmd_install() {
  chmod +x "$DEPLOY_DIR/setup.sh" "$DEPLOY_DIR/run.sh" "$DEPLOY_DIR/stop.sh" "$DEPLOY_DIR/status.sh" 2>/dev/null || true
  "$DEPLOY_DIR/setup.sh"
}

cmd_pipeline() {
  activate_env
  ensure_dirs
  [ -f "$PEPA_HOME/scripts/pipeline_linux.py" ] || err "No existe $PEPA_HOME/scripts/pipeline_linux.py"
  cd "$PEPA_HOME"
  python3 scripts/pipeline_linux.py 2>&1 | tee logs/pipeline.log
  ok "Pipeline finalizado"
}

cmd_run() {
  local mode="demo"
  while [ $# -gt 0 ]; do
    case "$1" in
      --mode) mode="${2:-}"; shift 2 ;;
      *) err "Parametro no reconocido: $1" ;;
    esac
  done

  case "$mode" in
    demo)
      info "Modo demo: eventos sinteticos + dashboard"
      start_generator
      sleep 2
      start_dashboard
      ;;
    lab)
      info "Modo laboratorio: datasets propios + dashboard"
      ensure_live_csv
      start_dashboard
      ;;
    production)
      info "Modo produccion: fuente real normalizada + dashboard"
      ensure_live_csv
      warn "Asegurate de tener un parser escribiendo en: $LIVE_CSV"
      start_dashboard
      ;;
    *) err "Modo invalido: $mode" ;;
  esac

  sleep 3
  cmd_url
}

cmd_stop() {
  pkill -f event_generator.py 2>/dev/null && ok "Generador detenido" || warn "Generador no estaba activo"
  pkill -f 'streamlit run' 2>/dev/null && ok "Dashboard detenido" || warn "Dashboard no estaba activo"
}

cmd_status() {
  echo "=== $APP_NAME ==="
  pgrep -f event_generator.py >/dev/null && ok "Event Generator activo" || warn "Event Generator inactivo"
  pgrep -f 'streamlit run' >/dev/null && ok "Dashboard activo" || warn "Dashboard inactivo"
  [ -d "$PEPA_HOME/output/cybersecurity_joined" ] && ok "Parquet existe" || warn "Parquet no encontrado"
  if [ -f "$LIVE_CSV" ]; then
    local lines
    lines=$(wc -l < "$LIVE_CSV")
    ok "Feed vivo: $lines lineas"
  else
    warn "Feed vivo no encontrado"
  fi
}

cmd_url() {
  local ip
  ip=$(local_ip)
  [ -n "$ip" ] || ip="127.0.0.1"
  echo "Dashboard: http://$ip:$PEPA_PORT"
}

cmd_logs() {
  echo "--- dashboard.log ---"
  tail -n 80 "$PEPA_HOME/logs/dashboard.log" 2>/dev/null || warn "Sin dashboard.log"
  echo "--- generator.log ---"
  tail -n 40 "$PEPA_HOME/logs/generator.log" 2>/dev/null || warn "Sin generator.log"
}

cmd="${1:-help}"
shift || true
case "$cmd" in
  install) cmd_install "$@" ;;
  run) cmd_run "$@" ;;
  pipeline) cmd_pipeline "$@" ;;
  status) cmd_status "$@" ;;
  stop) cmd_stop "$@" ;;
  url) cmd_url "$@" ;;
  logs) cmd_logs "$@" ;;
  help|-h|--help) usage ;;
  *) usage; err "Comando no reconocido: $cmd" ;;
esac
