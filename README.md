# PEPA CyberResilience

**PEPA** significa **Plataforma de Eventos y Procesamiento Analitico**.

PEPA CyberResilience es una herramienta open source para replicar una arquitectura Big Data de ciberseguridad en **Ubuntu Server**. Incluye instalacion automatizada, pipeline Spark, almacenamiento Parquet, dashboard Streamlit, simulador de eventos en vivo y una plantilla para integrar logs reales tipo SIEM.


## Live demo publico

El dashboard puede publicarse como app Streamlit desde este repositorio. La forma recomendada es Streamlit Community Cloud:

```text
Repositorio: marksato13/PEPA-CyberResilience
Branch: main
Main file path: app.py
```

Cuando Streamlit genere la URL publica, reemplaza este placeholder:

```text
Live Demo: pendiente de despliegue
```

Guia completa: [Despliegue publico](docs/DESPLIEGUE_PUBLICO.md).

## Que instala automaticamente

El script `setup.sh` prepara el servidor e instala las herramientas necesarias para duplicar el proyecto:

| Componente | Uso en PEPA |
| --- | --- |
| `git`, `curl`, `wget`, `unzip` | descarga, clonacion y utilidades base |
| `OpenJDK 17` | runtime requerido por Apache Spark |
| `python3`, `python3-venv`, `python3-pip` | entorno Python aislado |
| `pyspark` | procesamiento distribuido local con Spark |
| `pandas`, `numpy` | lectura y preparacion de datos |
| `pyarrow` | lectura/escritura Parquet |
| `streamlit` | dashboard web |
| `streamlit-autorefresh` | actualizacion automatica del feed en vivo |
| `plotly`, `matplotlib` | graficos analiticos |
| `python-pptx` | soporte para artefactos/reportes del proyecto |
| `systemd services` | arranque automatico del dashboard y generador |

El instalador usa `sudo` internamente solo cuando necesita instalar paquetes o crear servicios. **No ejecutes `setup.sh` con `sudo`**, porque debe instalar PEPA en el home del usuario actual.

## Requisitos

Servidor recomendado:

- Ubuntu Server 22.04, 24.04 o 24.10+.
- Usuario con permisos `sudo`.
- Internet para descargar paquetes apt y dependencias Python.
- 4 vCPU recomendado.
- 8 GB RAM recomendado.
- 5 GB libres en disco.
- Puerto `8501/tcp` accesible para el dashboard.

## Instalacion desde cero en Ubuntu Server

Estos comandos son suficientes para duplicar el proyecto en un servidor limpio:

```bash
sudo apt-get update
sudo apt-get install -y git

git clone https://github.com/marksato13/PEPA-CyberResilience.git
cd PEPA-CyberResilience
chmod +x setup.sh pepa.sh run.sh stop.sh status.sh
./setup.sh
./pepa.sh status
./pepa.sh url
```

Abrir en el navegador:

```text
http://IP_DEL_SERVIDOR:8501
```

Si usas firewall local:

```bash
sudo ufw allow 8501/tcp
```

## Que hace `setup.sh` paso a paso

1. Actualiza paquetes del sistema.
2. Instala utilidades base: Git, curl, wget, unzip y certificados.
3. Instala Java 17 para Spark.
4. Verifica Python 3.12+ o instala Python 3.12 en sistemas que lo requieran.
5. Instala `python3-venv` y `python3-pip`.
6. Crea la estructura de runtime en `~/bigdata`.
7. Copia scripts, parsers y datos CSV al runtime.
8. Crea el entorno virtual en `~/bigdata-env`.
9. Instala dependencias desde `requirements.txt`.
10. Ejecuta el pipeline Spark y genera Parquet en `~/bigdata/output/cybersecurity_joined`.
11. Crea servicios systemd para generador y dashboard.
12. Levanta el dashboard en el puerto `8501`.

## Modos de implementacion

PEPA tiene tres modos de uso.

| Modo | Comando | Fuente | Para que sirve |
| --- | --- | --- | --- |
| Demo | `./pepa.sh run --mode demo` | eventos sinteticos | mostrar el sistema sin datos reales |
| Laboratorio | `./pepa.sh run --mode lab` | CSV/JSON historicos | tesis, cursos, pruebas y datasets propios |
| Produccion | `./pepa.sh run --mode production` | logs reales normalizados | monitoreo continuo estilo mini-SIEM analitico |

## Modo Demo

Usa el simulador incluido `event_generator.py`. Genera eventos aleatorios pero controlados, con campos como ataque, severidad, pais, industria, volumen de datos y resultado.

```bash
./pepa.sh run --mode demo
```

Flujo:

```text
event_generator.py -> live_events.csv -> dashboard.py
```

Este modo es ideal para mostrar PEPA apenas termina la instalacion.

## Modo Laboratorio

Usa datasets propios colocados en `tablas/`.

```bash
cp mis_datos/*.csv tablas/
./pepa.sh pipeline
./pepa.sh run --mode lab
```

Flujo:

```text
tablas/*.csv -> pipeline_linux.py -> Parquet -> dashboard.py
```

Si tus columnas tienen nombres diferentes, ajusta la seccion de transformacion en `scripts/pipeline_linux.py`.

## Modo Produccion

Usa una fuente real de logs ya parseada o normalizada. PEPA incluye una plantilla:

```bash
python3 scripts/parsers/normalizer_template.py \
  --input /var/log/suricata/eve.json \
  --output ~/bigdata/output/live_events.csv \
  --source suricata \
  --follow

./pepa.sh run --mode production
```

Flujo esperado:

```text
Suricata / Wazuh / Zeek / Syslog / Firewall / SIEM
        -> parser o normalizador
        -> live_events.csv
        -> dashboard.py
```

Esquema minimo esperado para eventos en vivo:

```text
timestamp,attack_type,severity,country,industry,data_GB,outcome,duration_min
```

## Comandos principales

```bash
./pepa.sh install               # ejecuta setup.sh
./pepa.sh pipeline              # vuelve a ejecutar Spark y genera Parquet
./pepa.sh run --mode demo       # simulador + dashboard
./pepa.sh run --mode lab        # dashboard para datos de laboratorio
./pepa.sh run --mode production # dashboard para logs reales normalizados
./pepa.sh status                # estado de procesos y datos
./pepa.sh url                   # URL del dashboard
./pepa.sh logs                  # logs recientes
./pepa.sh stop                  # detiene generador y dashboard
```

## Estructura

```text
.
├── pepa.sh
├── setup.sh
├── requirements.txt
├── config/
│   └── pepa.env.example
├── docs/
│   ├── IMPLEMENTACION.md
│   └── MODOS_IMPLEMENTACION.md
├── scripts/
│   ├── pipeline_linux.py
│   ├── dashboard.py
│   ├── event_generator.py
│   ├── ml_v2.py
│   └── parsers/
│       └── normalizer_template.py
└── tablas/
    ├── T1_global_threats.csv
    ├── T2_ai_ml_events.csv
    └── T3_synthesized.csv
```

## Verificacion rapida

```bash
./pepa.sh status
curl http://127.0.0.1:8501/_stcore/health
```

Respuesta esperada del healthcheck:

```text
ok
```

## Documentacion

- [Manual de implementacion](docs/IMPLEMENTACION.md)
- [Modos de implementacion](docs/MODOS_IMPLEMENTACION.md)

## Licencia

MIT License.
