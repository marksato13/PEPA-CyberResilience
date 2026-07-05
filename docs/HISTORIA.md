# Historia de PEPA CyberResilience

PEPA CyberResilience comenzo como una arquitectura academica de Big Data aplicada a resiliencia informatica y ciberseguridad.

## Primera etapa: pipeline academico

La primera version se centro en demostrar un flujo completo de datos:

```text
CSV -> Spark -> Join triple -> Parquet -> Dashboard
```

El objetivo era consolidar varias fuentes de datos, transformar columnas, agregar metricas por tipo de ataque y anio, y generar una salida Parquet eficiente para analisis posterior.

## Segunda etapa: visualizacion ejecutiva

Se agrego un dashboard Streamlit para visualizar:

- KPIs de incidentes.
- Perdidas financieras.
- Usuarios afectados.
- Tipos de ataque.
- Severidad.
- Industrias objetivo.
- Feed de eventos en vivo.
- Resultados de modelos ML.

## Tercera etapa: herramienta replicable

El proyecto evoluciono hacia una herramienta open source con:

- `setup.sh` para instalacion automatizada en Ubuntu Server.
- `pepa.sh` como CLI de operacion.
- Modo demo con eventos sinteticos.
- Modo laboratorio para datasets propios.
- Modo produccion para logs reales normalizados.
- Parser base para integrar fuentes como Suricata, Wazuh, Zeek, Syslog o firewalls.

## Estado actual

PEPA ya puede clonarse desde GitHub, instalarse en Ubuntu Server y ejecutarse como dashboard publico o local. El enlace de demostracion actual se publica mediante Cloudflare Quick Tunnel.

## Vision

La vision del proyecto es convertirse en una plantilla abierta para laboratorios de ciberseguridad, clases de Big Data, prototipos de mini-SIEM y analitica de eventos con datos propios.
