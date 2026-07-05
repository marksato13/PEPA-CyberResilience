# Despliegue publico del dashboard

GitHub solo almacena el codigo. Para que el dashboard tenga un link publico, necesitas desplegar la app Streamlit en una plataforma que ejecute Python o exponer el servidor donde ya esta corriendo.

## Demo publico actual

```text
https://immunology-doll-bios-treatments.trycloudflare.com
```

Este enlace usa Cloudflare Quick Tunnel apuntando al dashboard local `http://localhost:8501` del servidor de demostracion. El servicio quedo configurado con `systemd` como `pepa-cloudflared.service` para reiniciarse si cae.

Comandos utiles en el servidor:

```bash
systemctl status pepa-cloudflared.service
grep -o 'https://[^ ]*trycloudflare.com' ~/bigdata/logs/cloudflared.log | tail -1
sudo systemctl restart pepa-cloudflared.service
```

Nota: como no hay dominio propio, la URL puede cambiar si se reinicia el tunel. Para URL estable usa un dominio con Cloudflare Tunnel nombrado.

## Opcion recomendada: Streamlit Community Cloud

1. Entra a <https://share.streamlit.io/> con tu cuenta GitHub.
2. Clic en **Create app**.
3. Selecciona el repositorio:

```text
marksato13/PEPA-CyberResilience
```

4. Rama:

```text
main
```

5. Main file path:

```text
app.py
```

6. Deploy.

La plataforma instalara:

- Dependencias Python desde `requirements.txt`.
- Java desde `packages.txt`.
- El dashboard iniciara desde `app.py`.

Cuando termine, Streamlit dara una URL publica parecida a:

```text
https://pepa-cyberresilience.streamlit.app
```

Esa URL se puede colocar en el README como **Live Demo**.

## Importante

El primer arranque puede tardar porque `app.py` prepara `~/bigdata` y genera el Parquet si no existe. Para un demo mas rapido, se recomienda en una version futura publicar un dataset Parquet pequeno de muestra o crear un dashboard demo basado solo en CSV.

## Alternativas

### VPS o servidor propio

Si quieres usar tu servidor Ubuntu actual, debes exponer el puerto 8501 publicamente:

```bash
./pepa.sh run --mode demo
sudo ufw allow 8501/tcp
```

Luego configura red/NAT/firewall para permitir acceso externo a:

```text
http://IP_PUBLICA:8501
```

Para un enlace profesional, apunta un dominio o subdominio hacia el servidor y usa Nginx + HTTPS.

### Hugging Face Spaces

Tambien se puede publicar como Space. Para Streamlit, Hugging Face recomienda usar Docker SDK o la plantilla Streamlit disponible en Spaces. El puerto esperado para Streamlit es 8501.
