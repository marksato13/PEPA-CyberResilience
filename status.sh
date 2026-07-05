#!/usr/bin/env bash
GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
BIGDATA_HOME="$HOME/bigdata"
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo -e "${CYAN}=== Estado BigData UPeU ===${NC}"

if pgrep -f event_generator.py > /dev/null; then
    echo -e "${GREEN}[ACTIVO]${NC}  Event Generator"
else
    echo -e "${RED}[INACTIVO]${NC} Event Generator"
fi

if pgrep -f 'streamlit run' > /dev/null; then
    echo -e "${GREEN}[ACTIVO]${NC}  Dashboard → http://$LOCAL_IP:8501"
else
    echo -e "${RED}[INACTIVO]${NC} Dashboard"
fi

if [ -d "$BIGDATA_HOME/output/cybersecurity_joined" ]; then
    echo -e "${GREEN}[OK]${NC}      Parquet existe"
else
    echo -e "${RED}[FALTA]${NC}   Parquet no generado — ejecuta setup.sh"
fi

if [ -f "$BIGDATA_HOME/output/live_events.csv" ]; then
    LINES=$(wc -l < "$BIGDATA_HOME/output/live_events.csv")
    echo -e "${GREEN}[OK]${NC}      live_events.csv: $LINES eventos"
fi
