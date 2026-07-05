#!/usr/bin/env bash
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
echo 'Deteniendo sistema BigData UPeU...'
pkill -f event_generator.py 2>/dev/null && echo -e "${GREEN}[OK]${NC} Event Generator detenido" || echo -e "${RED}[--]${NC} Generator no estaba corriendo"
pkill -f 'streamlit run' 2>/dev/null  && echo -e "${GREEN}[OK]${NC} Dashboard detenido"        || echo -e "${RED}[--]${NC} Dashboard no estaba corriendo"
