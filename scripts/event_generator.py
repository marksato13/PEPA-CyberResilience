"""
Generador de eventos en vivo — simula un stream de ciberataques en tiempo real.
Escribe una fila nueva cada 1-2 segundos en live_events.csv.
Ejecutar en background: python3 event_generator.py &
"""
import pandas as pd
import random
import time
import os
from datetime import datetime

LIVE_CSV = os.path.join(os.path.expanduser("~"), "bigdata", "output", "live_events.csv")

ATTACK_TYPES = ["DDoS", "Malware", "Phishing", "Ransomware", "SQL Injection",
                "Man-in-the-Middle"]
COUNTRIES    = ["USA", "China", "Russia", "Germany", "UK", "Brazil",
                "India", "France", "Japan", "Australia", "Canada", "Mexico"]
INDUSTRIES   = ["Healthcare", "Finance", "Government", "Education",
                "Retail", "Technology", "Energy", "Manufacturing"]
OUTCOMES     = ["Success", "Failure"]

# Pesos: DDoS y Phishing más frecuentes (simulación realista)
ATTACK_WEIGHTS = [0.25, 0.18, 0.22, 0.15, 0.12, 0.08]

def generate_event():
    attack = random.choices(ATTACK_TYPES, weights=ATTACK_WEIGHTS)[0]
    severity = random.randint(1, 10)
    # Ransomware tiende a mayor severidad
    if attack == "Ransomware":
        severity = random.randint(5, 10)
    elif attack == "Phishing":
        severity = random.randint(2, 7)
    return {
        "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "attack_type": attack,
        "severity":    severity,
        "country":     random.choice(COUNTRIES),
        "industry":    random.choice(INDUSTRIES),
        "data_GB":     round(random.uniform(0.1, 150), 2),
        "outcome":     random.choices(OUTCOMES, weights=[0.45, 0.55])[0],
        "duration_min":random.randint(1, 300),
    }

print(f"[{datetime.now().strftime('%H:%M:%S')}] Generador iniciado → {LIVE_CSV}")
print("Ctrl+C para detener\n")

# Inicializar o continuar el CSV
if not os.path.exists(LIVE_CSV):
    pd.DataFrame(columns=["timestamp","attack_type","severity","country",
                           "industry","data_GB","outcome","duration_min"]
                 ).to_csv(LIVE_CSV, index=False)
    print("Archivo live_events.csv creado.")

count = 0
try:
    while True:
        event = generate_event()
        row = pd.DataFrame([event])
        row.to_csv(LIVE_CSV, mode="a", header=False, index=False)
        count += 1
        print(f"[{event['timestamp']}] #{count:>4}  "
              f"{event['attack_type']:<22} sev={event['severity']}  "
              f"{event['country']:<12} {event['outcome']}")
        time.sleep(random.uniform(0.8, 2.5))
except KeyboardInterrupt:
    print(f"\nGenerador detenido. Total eventos generados: {count}")
