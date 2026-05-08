# API-Funktionen: Wechselkurse und SNB Immobilienpreisindex
import requests
import pandas as pd
from io import StringIO

def wechselkurs_holen():
    # Aktuellen Wechselkurs von frankfurter.app API laden
    try:
        antwort = requests.get(
            "https://api.frankfurter.app/latest",
            params={"from": "CHF", "to": "EUR,USD"},
            timeout=4,
        )
        daten = antwort.json()
        eur = daten["rates"]["EUR"]
        usd = daten["rates"]["USD"]
        return eur, usd
    except Exception:
        # Fallback auf fixe Kurse wenn API nicht erreichbar
        return 1.02, 1.10

def snb_preisindex_holen():
    # Immobilienpreisindex der Schweizer Nationalbank laden
    # Quelle: data.snb.ch – kostenlos, kein API-Key nötig
    # Gibt quartalsweise Preisindizes für Eigentumswohnungen und Einfamilienhäuser zurück
    try:
        antwort = requests.get(
            "https://data.snb.ch/api/cube/plimoinchq/data/csv/en",
            timeout=6,
        )
        # CSV einlesen – SNB-Format hat 3 Kopfzeilen die wir überspringen
        df = pd.read_csv(StringIO(antwort.text), skiprows=3)
        df.columns = ["datum", "kategorie", "index"]
        df = df.dropna()
        df["index"] = pd.to_numeric(df["index"], errors="coerce")
        df = df.dropna()
        return df
    except Exception:
        # Fallback: leerer DataFrame wenn API nicht erreichbar
        return pd.DataFrame(columns=["datum", "kategorie", "index"])
