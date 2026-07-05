#!/usr/bin/env bash
# =============================================================================
# SETUP AUTOMATICO - PEPA CyberResilience
# Compatible: Ubuntu Server 22.04 / 24.04 / 24.10+
# Instala: Git, curl, Java 17, Python, venv, pip, Spark/PySpark, Streamlit y stack analitico
# Uso: chmod +x setup.sh && ./setup.sh
# =============================================================================
set -e

if [ "${EUID:-$(id -u)}" -eq 0 ]; then
    echo "[ERROR] No ejecutes setup.sh con sudo. Usa: ./setup.sh" >&2
    echo "El script pedira sudo solo para instalar paquetes y servicios." >&2
    exit 1
fi


RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()  { echo -e "${CYAN}[15:39:18]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIGDATA_HOME="$HOME/bigdata"
ENV_DIR="$HOME/bigdata-env"
LOG_DIR="$BIGDATA_HOME/logs"

echo -e ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   PEPA CyberResilience — Setup Automatico               ║${NC}"
echo -e "${BOLD}║   Pipeline · ML · Dashboard · Event Generator            ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ── PASO 1: Sistema operativo ──────────────────────────────────────────────
log "PASO 1/7 — Actualizando sistema..."
sudo apt-get update -qq
sudo apt-get install -y -qq curl wget git unzip ca-certificates software-properties-common python3 python3-venv python3-pip
ok "Sistema actualizado"

# ── PASO 2: Java 17 ───────────────────────────────────────────────────────
log "PASO 2/7 — Instalando Java 17..."
if java -version 2>/dev/null | grep -q '17'; then
    ok "Java 17 ya instalado"
else
    sudo apt-get install -y -qq openjdk-17-jdk
    ok "Java 17 instalado"
fi

export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
if ! grep -q 'JAVA_HOME' ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Java — BigData UPeU" >> ~/.bashrc
    echo "export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64" >> ~/.bashrc
    echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> ~/.bashrc
fi
ok "JAVA_HOME configurado: $JAVA_HOME"

# ── PASO 3: Python 3.12 ───────────────────────────────────────────────────
log "PASO 3/7 — Verificando Python 3.12+..."
PY_VER=$(python3 --version 2>&1 | grep -oP '3\.\d+' | head -1)
PY_MINOR=$(echo $PY_VER | cut -d. -f2)
if [ "$PY_MINOR" -ge 12 ]; then
    ok "Python $PY_VER disponible"
else
    warn "Python $PY_VER detectado — instalando 3.12..."
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3.12 python3.12-venv python3.12-dev
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
    ok "Python 3.12 instalado"
fi

sudo apt-get install -y -qq python3-venv python3-pip
ok "python3-venv y pip listos"

# ── PASO 4: Directorios ───────────────────────────────────────────────────
log "PASO 4/7 — Creando estructura de directorios..."
mkdir -p "$BIGDATA_HOME"/{scripts,tablas,output,logs}
mkdir -p "$BIGDATA_HOME/scripts/parsers"
ok "Directorio base: $BIGDATA_HOME"

# Copiar scripts y parsers
cp "$DEPLOY_DIR"/scripts/*.py "$BIGDATA_HOME/scripts/"
if [ -d "$DEPLOY_DIR/scripts/parsers" ]; then
    cp -R "$DEPLOY_DIR"/scripts/parsers/. "$BIGDATA_HOME/scripts/parsers/"
fi
ok "Scripts y parsers copiados -> $BIGDATA_HOME/scripts/"

# Copiar datos
cp "$DEPLOY_DIR"/tablas/*.csv "$BIGDATA_HOME/tablas/"
ok "Datos copiados → $BIGDATA_HOME/tablas/"

# Detectar IP local para Spark
LOCAL_IP=$(hostname -I | awk '{print $1}')
if [ -z "$LOCAL_IP" ]; then LOCAL_IP="127.0.0.1"; fi

if ! grep -q 'SPARK_LOCAL_IP' ~/.bashrc; then
    echo "export SPARK_LOCAL_IP=$LOCAL_IP" >> ~/.bashrc
fi
ok "SPARK_LOCAL_IP=$LOCAL_IP detectado automáticamente"

# ── PASO 5: Entorno virtual Python ───────────────────────────────────────
log "PASO 5/7 — Creando entorno virtual Python..."
if [ -d "$ENV_DIR" ]; then
    warn "Entorno ya existe en $ENV_DIR — actualizando"
else
    python3 -m venv "$ENV_DIR"
    ok "Entorno creado: $ENV_DIR"
fi

source "$ENV_DIR/bin/activate"

log "  Instalando dependencias Python (puede tomar 2-5 min)..."
pip install --upgrade pip --quiet
if [ -f "$DEPLOY_DIR/requirements.txt" ]; then
    pip install --quiet -r "$DEPLOY_DIR/requirements.txt"
else
    pip install --quiet \
        pyspark==4.1.2 \
        pandas==2.2.3 \
        pyarrow==24.0.0 \
        streamlit==1.58.0 \
        streamlit-autorefresh==1.0.1 \
        plotly==6.7.0 \
        python-pptx==1.0.2 \
        matplotlib==3.9.0 \
        numpy
fi

ok "Paquetes instalados:"
pip list | grep -E 'pyspark|streamlit|pandas|pyarrow|plotly' | awk '{printf "    %-30s %s\n", $1, $2}'

# Alias conveniente
if ! grep -q 'alias bigdata' ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# PEPA CyberResilience alias" >> ~/.bashrc
    echo "alias bigdata='source $ENV_DIR/bin/activate && cd $BIGDATA_HOME'" >> ~/.bashrc
fi

# ── PASO 6: Pipeline Spark ───────────────────────────────────────────────
log "PASO 6/7 — Ejecutando pipeline Spark (T1+T2+T3 → Parquet)..."
echo "  Esto puede tomar 2-3 minutos..."
export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
export SPARK_LOCAL_IP=$LOCAL_IP
cd "$BIGDATA_HOME"
python3 scripts/pipeline_linux.py 2>&1 | tee logs/pipeline.log | grep -E 'FASE|OK|Error|filas|Parquet|F1|COMPLETO'
ok "Pipeline ejecutado — Parquet generado en output/cybersecurity_joined/"

# ── PASO 7: Servicios systemd (opcional) ─────────────────────────────────
log "PASO 7/7 — Configurando servicios de inicio automático..."

# Servicio event_generator
sudo tee /etc/systemd/system/bigdata-generator.service > /dev/null << SVC1
[Unit]
Description=PEPA CyberResilience - Event Generator
After=network.target

[Service]
User=$USER
WorkingDirectory=$BIGDATA_HOME
ExecStart=$ENV_DIR/bin/python3 $BIGDATA_HOME/scripts/event_generator.py
Restart=always
RestartSec=5
Environment=HOME=$HOME

[Install]
WantedBy=multi-user.target
SVC1

# Servicio dashboard
sudo tee /etc/systemd/system/bigdata-dashboard.service > /dev/null << SVC2
[Unit]
Description=PEPA CyberResilience - Streamlit Dashboard
After=network.target bigdata-generator.service

[Service]
User=$USER
WorkingDirectory=$BIGDATA_HOME
ExecStart=$ENV_DIR/bin/python3 -m streamlit run $BIGDATA_HOME/scripts/dashboard.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=5
Environment=HOME=$HOME
Environment=JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

[Install]
WantedBy=multi-user.target
SVC2

sudo systemctl daemon-reload
sudo systemctl enable bigdata-generator bigdata-dashboard
sudo systemctl start bigdata-generator bigdata-dashboard
sleep 3
ok "Servicios systemd activos (arrancan solos con el sistema)"

# ── RESUMEN FINAL ─────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║              INSTALACIÓN COMPLETADA ✓                    ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}Dashboard:${NC}       http://$LOCAL_IP:8501"
echo -e "  ${GREEN}Parquet:${NC}         $BIGDATA_HOME/output/cybersecurity_joined/"
echo -e "  ${GREEN}Eventos vivo:${NC}    $BIGDATA_HOME/output/live_events.csv"
echo -e "  ${GREEN}Logs:${NC}            $BIGDATA_HOME/logs/"
echo ""
echo -e "  Comandos útiles:"
echo -e "    ${CYAN}./pepa.sh run --mode demo${NC}        - levantar demo completa"
echo -e "    ${CYAN}./pepa.sh stop${NC}                   - detener sistema"
echo -e "    ${CYAN}./pepa.sh status${NC}                 - ver estado"
echo ""
