#!/usr/bin/env python3
"""Normalizador base para PEPA CyberResilience.

Convierte logs JSON line-by-line a live_events.csv.
Sirve como plantilla para integrar Suricata, Wazuh, Zeek, Syslog u otras fuentes.
"""
import argparse
import csv
import json
import os
import time
from datetime import datetime
from pathlib import Path

DEFAULT_COLUMNS = [
    "timestamp", "attack_type", "severity", "country", "industry",
    "data_GB", "outcome", "duration_min", "src_ip", "dst_ip", "protocol",
    "source", "raw_event_type"
]

KEYWORDS = [
    ("ransom", "Ransomware"),
    ("ddos", "DDoS"),
    ("denial", "DDoS"),
    ("phish", "Phishing"),
    ("sql", "SQL Injection"),
    ("injection", "SQL Injection"),
    ("malware", "Malware"),
    ("trojan", "Malware"),
    ("mitm", "Man-in-the-Middle"),
    ("man in the middle", "Man-in-the-Middle"),
]

def infer_attack_type(event):
    text = " ".join(str(event.get(k, "")) for k in ["signature", "category", "alert", "event_type", "message"]).lower()
    if isinstance(event.get("alert"), dict):
        alert = event["alert"]
        text += " " + str(alert.get("signature", "")).lower()
        text += " " + str(alert.get("category", "")).lower()
    for needle, attack in KEYWORDS:
        if needle in text:
            return attack
    return "Malware"

def normalize_timestamp(value):
    if not value:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    value = str(value).replace("T", " ").replace("Z", "")
    return value[:19]

def normalize_severity(event):
    alert = event.get("alert") if isinstance(event.get("alert"), dict) else {}
    raw = event.get("severity", alert.get("severity", event.get("level", 5)))
    try:
        sev = int(raw)
    except Exception:
        text = str(raw).lower()
        if text in {"critical", "high"}:
            sev = 8
        elif text == "medium":
            sev = 5
        elif text == "low":
            sev = 2
        else:
            sev = 5
    return max(1, min(10, sev))

def normalize_event(event, source):
    alert = event.get("alert") if isinstance(event.get("alert"), dict) else {}
    length = event.get("flow", {}).get("bytes_toserver", 0) if isinstance(event.get("flow"), dict) else 0
    try:
        data_gb = round(float(length) / (1024 ** 3), 4)
    except Exception:
        data_gb = 0.0
    return {
        "timestamp": normalize_timestamp(event.get("timestamp", event.get("time"))),
        "attack_type": infer_attack_type({**event, **alert}),
        "severity": normalize_severity(event),
        "country": event.get("country", "Unknown"),
        "industry": event.get("industry", "Unknown"),
        "data_GB": data_gb,
        "outcome": "Detected",
        "duration_min": 0,
        "src_ip": event.get("src_ip", event.get("source_ip", "")),
        "dst_ip": event.get("dest_ip", event.get("dst_ip", event.get("destination_ip", ""))),
        "protocol": event.get("proto", event.get("protocol", "")),
        "source": source,
        "raw_event_type": event.get("event_type", "unknown"),
    }

def ensure_output(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("w", newline="") as fh:
            csv.DictWriter(fh, fieldnames=DEFAULT_COLUMNS).writeheader()

def read_new_lines(path, follow):
    with path.open("r", errors="ignore") as fh:
        while True:
            line = fh.readline()
            if line:
                yield line
                continue
            if not follow:
                break
            time.sleep(1)

def main():
    parser = argparse.ArgumentParser(description="Normalizador de logs para PEPA")
    parser.add_argument("--input", required=True, help="Archivo JSON lines de entrada")
    parser.add_argument("--output", required=True, help="CSV normalizado de salida")
    parser.add_argument("--source", default="custom", help="Nombre de la fuente")
    parser.add_argument("--follow", action="store_true", help="Mantener lectura tipo tail -f")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(os.path.expanduser(args.output))
    ensure_output(output_path)

    with output_path.open("a", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=DEFAULT_COLUMNS)
        for line in read_new_lines(input_path, args.follow):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            writer.writerow(normalize_event(event, args.source))
            out.flush()

if __name__ == "__main__":
    main()
