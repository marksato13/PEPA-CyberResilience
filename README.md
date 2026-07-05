# PEPA CyberResilience

**PEPA** significa **Plataforma de Eventos y Procesamiento Analitico**.

PEPA CyberResilience es una herramienta open source para replicar una arquitectura Big Data de ciberseguridad con Spark, Parquet, Streamlit, simulacion de eventos en vivo y una ruta de integracion con logs reales tipo SIEM.

## Para que sirve

PEPA permite que estudiantes, investigadores y equipos de seguridad construyan un laboratorio o prototipo de monitoreo analitico usando sus propios datos.

Casos de uso:

- Procesar datasets de ciberseguridad con Apache Spark.
- Consolidar multiples fuentes en un dataset analitico Parquet.
- Visualizar KPIs, perdidas, severidad, industrias, paises y tipos de ataque.
- Ejecutar un feed en vivo usando eventos sinteticos o logs normalizados.
- Adaptar parsers para Suricata, Wazuh, Zeek, Syslog, firewalls o SIEM.
- Usarlo como recurso academico, demo ejecutiva o base de produccion.

## Modos de implementacion

PEPA esta pensado para tres modos:

| Modo | Fuente de datos | Uso principal |
| --- | --- | --- |
| Demo | Eventos sinteticos generados por PEPA | Mostrar el sistema funcionando sin datos reales |
| Laboratorio | CSV/JSON/datasets historicos propios | Analisis academico, pruebas y experimentacion |
| Produccion | Logs reales normalizados | Monitoreo continuo estilo mini-SIEM analitico |

## Instalacion rapida

```bash
git clone https://github.com/marksato13/PEPA-CyberResilience.git
cd PEPA-CyberResilience
chmod +x setup.sh pepa.sh run.sh stop.sh status.sh
sudo ./setup.sh
./pepa.sh status
```

Abrir el dashboard:

```text
http://IP_DEL_SERVIDOR:8501
```

Si ya estas en el servidor, puedes ver la URL con:

```bash
./pepa.sh url
```

## Uso rapido por modo

### Modo Demo

```bash
./pepa.sh run --mode demo
```

Este modo levanta:

- `event_generator.py`: genera eventos sinteticos en vivo.
- `dashboard.py`: muestra el dashboard Streamlit.

### Modo Laboratorio

```bash
cp mis_datos/*.csv tablas/
./pepa.sh pipeline
./pepa.sh run --mode lab
```

Este modo usa los CSV de `tablas/`, ejecuta Spark y abre el dashboard sin depender del simulador.

### Modo Produccion

```bash
python3 scripts/parsers/normalizer_template.py \
  --input /var/log/suricata/eve.json \
  --output ~/bigdata/output/live_events.csv \
  --follow

./pepa.sh run --mode production
```

En produccion, una fuente real debe escribir eventos normalizados hacia `live_events.csv` o hacia el conector que definas.

## Estructura del proyecto

```text
.
├── pepa.sh                         # CLI de implementacion
├── setup.sh                        # instalacion automatizada
├── run.sh                          # arranque manual clasico
├── stop.sh                         # detener procesos
├── status.sh                       # revisar estado
├── config/
│   └── pepa.env.example            # configuracion base
├── docs/
│   ├── IMPLEMENTACION.md           # manual paso a paso
│   └── MODOS_IMPLEMENTACION.md     # demo, laboratorio, produccion
├── scripts/
│   ├── pipeline_linux.py           # Spark: ingesta, transformacion, join, Parquet
│   ├── dashboard.py                # Streamlit UI
│   ├── event_generator.py          # simulador de eventos en vivo
│   ├── ml_v2.py                    # modelos ML
│   └── parsers/
│       └── normalizer_template.py  # plantilla para logs reales
├── tablas/                         # datos de entrada
├── output/                         # salida generada
└── logs/                           # logs de ejecucion
```

## Documentacion

- [Manual de implementacion](docs/IMPLEMENTACION.md)
- [Modos de implementacion](docs/MODOS_IMPLEMENTACION.md)

## Licencia

Recomendado para publicacion open source bajo licencia MIT.
