# Manual de Implementacion - PEPA CyberResilience

## Autores

- Ruben Mark Salazar Tocas - Cod. 75184251
- Daniel H. Calderon Camacho - Cod. 71101519
- Uziel Elias Sauñe Fernandez - Cod. 75664788

## Historia

PEPA CyberResilience comenzo como un proyecto academico UPeU 2026-1 para demostrar una arquitectura Big Data aplicada a ciberseguridad. Evoluciono a una herramienta open source replicable con instalador, CLI, dashboard, modo demo, modo laboratorio y base de integracion con logs reales.

## 1. Objetivo

PEPA CyberResilience permite desplegar una arquitectura replicable para analisis de ciberseguridad:

```text
Datos CSV / Logs / Eventos
        -> Pipeline Spark
        -> Parquet particionado
        -> Dashboard Streamlit
        -> Feed en vivo
        -> ML / analitica
```

La idea es que otra persona pueda clonar el proyecto, instalar dependencias, ejecutar el pipeline y abrir un dashboard funcional.

## 2. Requisitos del servidor

Sistema recomendado:

- Ubuntu Server 22.04, 24.04 o superior.
- 4 vCPU minimo recomendado.
- 8 GB RAM recomendado.
- 5 GB libres en disco.
- Acceso a internet para instalar paquetes.
- Usuario con permisos `sudo`.

Herramientas instaladas automaticamente por `setup.sh`:

- Git
- Curl / Wget / Unzip
- OpenJDK 17
- Python 3.12 o Python 3 compatible
- python3-venv / pip
- PySpark
- Pandas
- PyArrow
- Streamlit
- Plotly
- streamlit-autorefresh

## 3. Instalacion desde GitHub

Importante: no ejecutes `setup.sh` con `sudo`. El instalador usa `sudo` internamente para paquetes y servicios, pero debe crear `~/bigdata` y `~/bigdata-env` en el usuario actual.


```bash
git clone https://github.com/marksato13/PEPA-CyberResilience.git
cd PEPA-CyberResilience
chmod +x setup.sh pepa.sh run.sh stop.sh status.sh
./setup.sh
```

El instalador realiza:

1. Actualizacion de paquetes base.
2. Instalacion de Java 17.
3. Configuracion de Python y entorno virtual.
4. Copia de scripts a `~/bigdata`.
5. Copia de datos a `~/bigdata/tablas`.
6. Instalacion de dependencias Python.
7. Ejecucion del pipeline Spark.
8. Generacion de Parquet en `~/bigdata/output/cybersecurity_joined`.
9. Registro de servicios systemd para dashboard y generador.

## 4. Verificacion de instalacion

```bash
./pepa.sh status
```

Debe mostrar:

```text
Event Generator: activo o inactivo segun modo
Dashboard: activo
Parquet: OK
live_events.csv: OK si existe feed en vivo
```

Ver URL:

```bash
./pepa.sh url
```

Abrir en navegador:

```text
http://IP_DEL_SERVIDOR:8501
```

## 5. Comandos principales

```bash
./pepa.sh install              # ejecuta setup.sh
./pepa.sh run --mode demo      # simulador + dashboard
./pepa.sh run --mode lab       # dashboard para datos de laboratorio
./pepa.sh run --mode production# dashboard para fuente real normalizada
./pepa.sh pipeline             # ejecuta pipeline Spark
./pepa.sh status               # estado de procesos y datos
./pepa.sh stop                 # detiene Streamlit y generador
./pepa.sh url                  # muestra URL del dashboard
./pepa.sh logs                 # muestra logs recientes
```

## 6. Flujo de datos

### Entrada

Los datos base se colocan en:

```text
tablas/
├── T1_global_threats.csv
├── T2_ai_ml_events.csv
└── T3_synthesized.csv
```

### Procesamiento

El pipeline ejecuta:

```bash
python3 scripts/pipeline_linux.py
```

Fases principales:

1. Carga CSV con Pandas.
2. Conversion a DataFrames Spark.
3. Limpieza y renombrado de columnas.
4. Agregacion por `Attack_Type` y `Year`.
5. Join triple entre T1, T2 y T3.
6. Escritura Parquet particionada.
7. Analisis exploratorio.
8. Entrenamiento/evaluacion ML basica.

### Salida

```text
~/bigdata/output/cybersecurity_joined/
```

Formato:

```text
Parquet particionado por Attack_Type y Year
```

### Feed en vivo

```text
~/bigdata/output/live_events.csv
```

Esquema esperado:

```text
timestamp,attack_type,severity,country,industry,data_GB,outcome,duration_min
```

## 7. Como usar datos propios

1. Reemplazar los CSV en `tablas/`.
2. Mantener nombres de columnas esperados o ajustar `scripts/pipeline_linux.py`.
3. Ejecutar:

```bash
./pepa.sh pipeline
./pepa.sh run --mode lab
```

Si tus columnas tienen otros nombres, adapta la seccion de transformacion:

```python
.withColumnRenamed("Attack Type", "Attack_Type")
.withColumnRenamed("Target Industry", "Target_Industry")
```

## 8. Integracion con logs reales

Para fuentes reales, PEPA necesita un parser que convierta logs a un esquema comun.

Ejemplo con Suricata `eve.json`:

```bash
python3 scripts/parsers/normalizer_template.py \
  --input /var/log/suricata/eve.json \
  --output ~/bigdata/output/live_events.csv \
  --follow
```

Luego:

```bash
./pepa.sh run --mode production
```

## 9. Publicacion en GitHub

Si el repositorio esta vacio:

```bash
git init
git branch -M main
git add .
git commit -m "Initial open source release of PEPA CyberResilience"
git remote add origin https://github.com/marksato13/PEPA-CyberResilience.git
git push -u origin main
```

Si ya existe remoto:

```bash
git remote -v
git add .
git commit -m "Add implementation manual and PEPA CLI"
git push
```

## 10. Solucion de problemas

### El dashboard no abre

```bash
./pepa.sh status
ss -ltnp | grep 8501
```

Verifica firewall:

```bash
sudo ufw allow 8501/tcp
```

### Spark falla por memoria

Editar `scripts/pipeline_linux.py` y reducir:

```python
.config("spark.driver.memory", "3g")
```

### No se generan eventos en vivo

```bash
./pepa.sh run --mode demo
./pepa.sh logs
```

### El parser de produccion no reconoce campos

Editar:

```text
scripts/parsers/normalizer_template.py
```

Ajustar la funcion `normalize_event()` al formato real de logs.
