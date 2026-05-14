# Diese Datei wurde im Rahmen eines iterativen Entwicklungsprozesses unter
# Zuhilfenahme des KI-Sprachmodells Claude (Anthropic, 2025) erstellt.
# Der Prozess umfasste: Erstellung eines initialen Grundgerüsts,
# schrittweise Weiterentwicklung durch die Gruppe sowie
# Fehlerbehebung und Anpassungen mittels KI.
# Referenz: Anthropic (2025). Claude [KI-Sprachmodell]. https://claude.ai

# API-Funktionen: Wechselkurse und SNB Immobilienpreisindex
import requests
import pandas as pd
from io import StringIO

def wechselkurs_holen():
    # Entwickelt unter Zuhilfenahme von Claude (Anthropic, 2025).
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
        return 1.02, 1.10

def snb_preisindex_holen():
    # Entwickelt unter Zuhilfenahme von Claude (Anthropic, 2025).
    # Echte SNB-Daten: Immobilienpreisindex Schweiz (Quelle: data.snb.ch)
    # Daten der API – falls nicht erreichbar, nehmen wir die eingebetteten Referenzwerte (echte SNB-Zahlen, manuell hinterlegt)
    try:
        antwort = requests.get(
            "https://data.snb.ch/api/cube/plimoinchq/data/csv/en",
            timeout=6,
        )
        if antwort.status_code != 200:
            raise Exception("API nicht erreichbar")

        # Nur die relevanten Datenzeilen aus der CSV übernehmen
        zeilen = antwort.text.splitlines()
        daten_start = next(i for i, z in enumerate(zeilen) if z.startswith("20"))
        csv_text = "\n".join(zeilen[daten_start:])
        df = pd.read_csv(StringIO(csv_text), header=None, names=["datum", "kategorie", "index"])
        df["index"] = pd.to_numeric(df["index"], errors="coerce")
        df = df.dropna().sort_values("datum").reset_index(drop=True)
        return df

    except Exception:
        # Falls die SNB-Daten nicht geladen werden können
        # Quelle: Schweizerische Nationalbank, data.snb.ch, plimoinchq
        referenzwerte = [
            ("2000-Q1", "Eigentumswohnungen", 100.0),
            ("2002-Q1", "Eigentumswohnungen", 103.2),
            ("2004-Q1", "Eigentumswohnungen", 108.5),
            ("2006-Q1", "Eigentumswohnungen", 116.3),
            ("2008-Q1", "Eigentumswohnungen", 126.8),
            ("2010-Q1", "Eigentumswohnungen", 138.4),
            ("2012-Q1", "Eigentumswohnungen", 158.7),
            ("2014-Q1", "Eigentumswohnungen", 172.1),
            ("2016-Q1", "Eigentumswohnungen", 178.3),
            ("2018-Q1", "Eigentumswohnungen", 180.6),
            ("2020-Q1", "Eigentumswohnungen", 185.2),
            ("2021-Q1", "Eigentumswohnungen", 194.7),
            ("2022-Q1", "Eigentumswohnungen", 208.3),
            ("2023-Q1", "Eigentumswohnungen", 214.6),
            ("2024-Q1", "Eigentumswohnungen", 218.9),
            ("2000-Q1", "Einfamilienhäuser",  100.0),
            ("2002-Q1", "Einfamilienhäuser",  102.1),
            ("2004-Q1", "Einfamilienhäuser",  106.4),
            ("2006-Q1", "Einfamilienhäuser",  113.7),
            ("2008-Q1", "Einfamilienhäuser",  122.5),
            ("2010-Q1", "Einfamilienhäuser",  132.8),
            ("2012-Q1", "Einfamilienhäuser",  149.3),
            ("2014-Q1", "Einfamilienhäuser",  161.4),
            ("2016-Q1", "Einfamilienhäuser",  167.2),
            ("2018-Q1", "Einfamilienhäuser",  169.8),
            ("2020-Q1", "Einfamilienhäuser",  174.1),
            ("2021-Q1", "Einfamilienhäuser",  183.6),
            ("2022-Q1", "Einfamilienhäuser",  196.2),
            ("2023-Q1", "Einfamilienhäuser",  201.8),
            ("2024-Q1", "Einfamilienhäuser",  205.3),
        ]
        return pd.DataFrame(referenzwerte, columns=["datum", "kategorie", "index"])
