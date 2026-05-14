# Diese Datei wurde im Rahmen eines iterativen Entwicklungsprozesses unter
# Zuhilfenahme des KI-Sprachmodells Claude (Anthropic, 2025) erstellt.
# Der Prozess umfasste: Erstellung eines initialen Grundgerüsts,
# schrittweise Weiterentwicklung durch die Gruppe sowie
# Fehlerbehebung und Anpassungen mittels KI.
# Referenz: Anthropic (2025). Claude [KI-Sprachmodell]. https://claude.ai

# Entwickelt unter Zuhilfenahme von Claude (Anthropic, 2025).
# Machine Learning Modell: Preisschätzung mit Random Forest
from datetime import datetime
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import database

# Entwickelt unter Zuhilfenahme von Claude (Anthropic, 2025).
# Speicherung der Modelle nach dem Training
_modelle = {}
_encoder = None

def _encoder_initialisieren(daten):
    # Entwickelt unter Zuhilfenahme von Claude (Anthropic, 2025).
    # Encoder für Stadtnamen
    global _encoder
    if _encoder is None:
        _encoder = LabelEncoder()
        _encoder.fit(daten["stadt"].unique())

def _features_erstellen(daten):
    # Entwickelt unter Zuhilfenahme von Claude (Anthropic, 2025).
    # Erstellung der Eingabedaten für das Modell
    _encoder_initialisieren(daten)
    df = daten.copy()
    df["stadt_nr"] = _encoder.transform(df["stadt"].values)
    df["alter"] = datetime.now().year - df["baujahr"]
    # Features: Stadt (codiert), Fläche, Zimmer, Stockwerk, Parkplatz, Gebäudealter
    return df[["stadt_nr", "flaeche", "zimmer", "stockwerk", "parkplatz", "alter"]]

def trainieren(typ):
    # Entwickelt unter Zuhilfenahme von Claude (Anthropic, 2025).
    # Random Forest für Kauf- oder Mietpreise trainieren und speichern
    global _modelle
    daten = database.marktdaten_laden(typ=typ)
    if len(daten) < 10:
        return
    X = _features_erstellen(daten)
    y = daten["preis"].values
    modell = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    # Quelle Random Forrest: Breiman, L. (2001). Random Forests. Machine Learning, 45(1), 5–32.
    # https://doi.org/10.1023/A:1010933404324
    modell.fit(X, y)
    _modelle[typ] = modell

def alle_trainieren():
    # Beide Modelle (Kauf + Miete) beim App-Start laden
    trainieren("kauf")
    trainieren("miete")

def schaetzen(stadt, flaeche, zimmer, stockwerk, parkplatz, baujahr, typ):
    # Entwickelt unter Zuhilfenahme von Claude (Anthropic, 2025).
    # Preis für eine Immobilie schätzen und als gerundeten CHF-Betrag zurückgeben
    if typ not in _modelle:
        trainieren(typ)
    if typ not in _modelle:
        # Alternative falls kein Modell vorhanden
        return round(flaeche * (8000 if typ == "kauf" else 20), -2)
    try:
        # Unbekannte Städte werden auf den ersten bekannten Wert abgebildet
        stadt_nr = _encoder.transform([stadt])[0]
    except Exception:
        stadt_nr = 0
    alter = datetime.now().year - baujahr
    X = np.array([[stadt_nr, flaeche, zimmer, stockwerk, int(parkplatz), alter]])
    preis = _modelle[typ].predict(X)[0]
    # Kaufpreise auf CHF 1'000, Mieten auf CHF 10 runden
    runden = -3 if typ == "kauf" else -1
    return round(preis, runden)
