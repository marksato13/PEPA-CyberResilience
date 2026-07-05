#!/usr/bin/env bash
# Levanta event_generator y dashboard manualmente
set -e
BIGDATA_HOME="/home/m4rk/bigdata"
ENV_DIR="/home/m4rk/bigdata-env"
LOCAL_IP=$(hostname -I | awk '{print $1}')

GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}Levantando sistema BigData UPeU...${NC}"

# Verificar que el Parquet existe
if [ ! -d "$BIGDATA_HOME/output/cybersecurity_joined" ]; then
    echo "[ERROR] Parquet no encontrado. Ejecuta primero: ./setup.sh"
    exit 1
fi

source "$ENV_DIR/bin/activate"
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Matar procesos previos si existen
pkill -f event_generator.py 2>/dev/null || true
pkill -f 'streamlit run' 2>/dev/null || true
sleep 1

# Iniciar generador
nohup python3 "$BIGDATA_HOME/scripts/event_generator.py"     > "$BIGDATA_HOME/logs/generator.log" 2>&1 &
GEN_PID=$!
echo -e "${GREEN}[OK]${NC} Event Generator iniciado (PID $GEN_PID)"

sleep 2

# Iniciar dashboard
nohup python3 -m streamlit run "$BIGDATA_HOME/scripts/dashboard.py"     --server.port 8501     --server.address 0.0.0.0     --server.headless true     > "$BIGDATA_HOME/logs/dashboard.log" 2>&1 &
DASH_PID=$!
echo -e "${GREEN}[OK]${NC} Dashboard iniciado (PID $DASH_PID)"

sleep 4
echo ""
echo -e "${GREEN}Sistema activo → http://$LOCAL_IP:8501${NC}"
echo "  Logs: $BIGDATA_HOME/logs/"
