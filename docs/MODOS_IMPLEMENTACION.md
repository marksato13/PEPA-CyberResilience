# Modos de Implementacion - PEPA CyberResilience

PEPA puede ejecutarse en tres modos. La diferencia principal es la fuente de eventos.

## 1. Modo Demo

### Objetivo

Mostrar PEPA funcionando sin depender de datos reales.

### Fuente de datos

`event_generator.py` genera eventos sinteticos cada pocos segundos.

### Beneficio

- Instalacion rapida para demostraciones.
- No requiere SIEM, IDS ni logs reales.
- Permite validar dashboard, KPIs y feed en vivo.

### Uso

```bash
./pepa.sh run --mode demo
```

### Arquitectura

```text
event_generator.py
        -> live_events.csv
        -> dashboard.py
```

### Cuando usarlo

- Presentaciones.
- Pruebas iniciales.
- Cursos o talleres.
- Validacion visual del sistema.

## 2. Modo Laboratorio

### Objetivo

Analizar datasets propios, historicos o academicos.

### Fuente de datos

CSV o JSON preparados por el usuario.

### Beneficio

- Permite adaptar PEPA a nuevos datasets.
- Sirve para tesis, practicas y pruebas de ML.
- No depende de eventos en tiempo real.

### Uso

```bash
cp mis_datos/*.csv tablas/
./pepa.sh pipeline
./pepa.sh run --mode lab
```

### Arquitectura

```text
tablas/*.csv
        -> pipeline_linux.py
        -> cybersecurity_joined/ Parquet
        -> dashboard.py
```

### Cuando usarlo

- Investigacion.
- Proyectos universitarios.
- Comparacion de datasets.
- Validacion de transformaciones Spark.

## 3. Modo Produccion

### Objetivo

Conectar PEPA a una fuente real de monitoreo o logs.

### Fuente de datos

Puede venir de:

- Suricata `eve.json`
- Wazuh alerts
- Zeek logs
- Syslog
- pfSense
- Firewalls
- Kafka
- Filebeat
- Exportaciones SIEM

### Beneficio

- Permite operar como mini-SIEM analitico.
- Separa parsing, normalizacion, almacenamiento y visualizacion.
- Mantiene el dashboard independiente de la herramienta de origen.

### Uso base

```bash
python3 scripts/parsers/normalizer_template.py \
  --input /ruta/a/log.json \
  --output ~/bigdata/output/live_events.csv \
  --follow

./pepa.sh run --mode production
```

### Arquitectura

```text
Suricata / Wazuh / Zeek / Syslog / Firewall
        -> parser especifico
        -> esquema normalizado PEPA
        -> live_events.csv o Kafka
        -> dashboard.py
        -> almacenamiento historico
```

### Esquema normalizado minimo

```text
timestamp
attack_type
severity
country
industry
data_GB
outcome
duration_min
```

### Recomendacion para produccion real

Para una produccion mas fuerte, reemplazar `live_events.csv` por una cola o almacenamiento de eventos:

- Kafka para streaming.
- Redis Streams para eventos livianos.
- PostgreSQL para consultas operacionales.
- Elasticsearch/OpenSearch para busqueda de logs.
- Parquet diario para historico analitico.

## Decision practica

- Mantener el generador random: si, como modo demo.
- Usar CSV historico: si, como modo laboratorio.
- Integrar SIEM/logs: si, como modo produccion mediante parsers.

El simulador no debe presentarse como dato real. Debe documentarse como herramienta de demostracion y pruebas.
