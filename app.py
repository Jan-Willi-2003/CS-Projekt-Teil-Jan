# WertWohn – Schweizer Immobilienpreisschätzer (Hauptdatei)
import numpy as np
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import database
import ml_model
import data_fetcher
from config import STAEDTE, STADTLISTE, SEITEN, APP_NAME, APP_UNTERTITEL
from utils import chf, typ_bezeichnung, suche_stadt

# ── Seiteneinstellungen ───────────────────────────────────────────────────────
st.set_page_config(page_title=APP_NAME, page_icon="🏠", layout="wide")

# ── Initialisierung beim ersten Start ─────────────────────────────────────────

if "gestartet" not in st.session_state:
    database.initialisieren()
    ml_model.alle_trainieren()
    st.session_state["gestartet"] = True
    st.cache_data.clear()

# Login-Status initialisieren
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "benutzername" not in st.session_state:
    st.session_state["benutzername"] = None

# ── Daten mit Cache laden ─────────────────────────────────────────────────────

@st.cache_data
def daten_holen(typ):
    return database.laden(typ=typ)

@st.cache_data
def stadtdaten_holen():
    return database.stadtdaten_laden()

@st.cache_data
def marktdaten_holen(typ):
    # Marktdaten für die Marktübersicht laden
    return database.marktdaten_laden(typ=typ)


# ── Login / Registrierung in der Sidebar ─────────────────────────────────────

def sidebar_login():
    st.sidebar.markdown("---")
    # Wenn Benutzer bereits eingeloggt ist
    if st.session_state["user_id"] is not None:
        st.sidebar.success(f"👤 {st.session_state['benutzername']}")
        if st.sidebar.button("Abmelden", use_container_width=True):
            st.session_state["user_id"] = None
            st.session_state["benutzername"] = None
            st.rerun()
        return

    # Login-Formular anzeigen
    modus = st.sidebar.radio("Konto", ["Anmelden", "Registrieren"], horizontal=True)
    benutzername = st.sidebar.text_input("Benutzername", key="login_name")
    passwort = st.sidebar.text_input("Passwort", type="password", key="login_pw")

    if modus == "Anmelden":
        if st.sidebar.button("Anmelden", use_container_width=True):
            user_id = database.benutzer_anmelden(benutzername, passwort)
            if user_id:
                st.session_state["user_id"] = user_id
                st.session_state["benutzername"] = benutzername
                st.rerun()
            else:
                st.sidebar.error("Benutzername oder Passwort falsch.")
    else:
        if st.sidebar.button("Registrieren", use_container_width=True):
            if len(benutzername.strip()) < 3:
                st.sidebar.error("Benutzername muss mindestens 3 Zeichen haben.")
            elif len(passwort) < 4:
                st.sidebar.error("Passwort muss mindestens 4 Zeichen haben.")
            else:
                ok = database.benutzer_registrieren(benutzername, passwort)
                if ok:
                    st.sidebar.success("Konto erstellt! Bitte jetzt anmelden.")
                else:
                    st.sidebar.error("Benutzername bereits vergeben.")


# ── Seite 1: Preisschätzung ───────────────────────────────────────────────────

def seite_preisschaetzung():
    st.title("🏠 WertWohn")
    st.markdown("### Schweizer Immobilienpreise einfach schätzen")
    st.markdown("""Kennst du das? Du interessierst dich für eine Wohnung in Zürich oder Basel –
aber weisst nicht ob der Preis fair ist. Makler sind teuer, Vergleichsportale
zeigen nur Angebotspreise und niemand gibt dir eine klare Antwort.

**WertWohn löst genau dieses Problem.** Unser Modell analysiert
den Schweizer Immobilienmarkt und liefert dir in Sekunden eine realistische
Preisschätzung – für Kauf und Miete, kostenlos und mit persönlichem Konto.
    """)

    col1, col2 = st.columns(2)
    col1.metric("Städte", "10 Schweizer Städte")
    col2.metric("Währungen", "CHF · EUR · USD")

    st.markdown("---")

    # ── Suche und Preistyp ────────────────────────────────────────────────────
    col_suche, col_typ = st.columns([2, 1])
    with col_suche:
        eingabe = st.text_input("🔍 PLZ oder Stadtname eingeben", placeholder="z. B. 8000 oder Zürich")
    with col_typ:
        typ_wahl = st.radio("Preistyp", ["Kaufpreis", "Mietpreis"], horizontal=True)

    # Stadtauswahl: Sucheingabe vorfiltern, dann Dropdown
    gefundene_stadt = suche_stadt(eingabe, STADTLISTE) if eingabe else None
    if eingabe and not gefundene_stadt:
        st.caption("Stadt nicht gefunden – bitte unten manuell auswählen.")

    standard_index = STADTLISTE.index(gefundene_stadt) if gefundene_stadt else 0
    stadt = st.selectbox("Stadt", STADTLISTE, index=standard_index)

    # ── Immobilien-Eigenschaften ──────────────────────────────────────────────
    st.markdown("#### Angaben zur Immobilie")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        zimmer = st.select_slider(
            "Anzahl Zimmer", [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0], value=3.5
        )
        flaeche = st.slider("Wohnfläche (m²)", 25, 300, 85)
    with col_b:
        stockwerk = st.slider("Stockwerk", 0, 15, 2)
        baujahr = st.slider("Baujahr", 1900, 2026, 2000)
    with col_c:
        parkplatz = st.checkbox("Parkplatz vorhanden", value=False)
        st.write("")
        st.write("")
        berechnen = st.button("Preis schätzen", type="primary", use_container_width=True)

    # ── Ergebnis anzeigen ─────────────────────────────────────────────────────
    typ_intern = "kauf" if typ_wahl == "Kaufpreis" else "miete"

    if berechnen:
        preis = ml_model.schaetzen(stadt, flaeche, zimmer, stockwerk, parkplatz, baujahr, typ_intern)
        st.session_state["letzter_preis"] = preis
        # Auch Eingaben merken für korrekte Anzeige nach Neuberechnung
        st.session_state["letzter_typ"] = typ_intern
    elif "letzter_preis" in st.session_state:
        preis = st.session_state["letzter_preis"]
        typ_intern = st.session_state.get("letzter_typ", typ_intern)
    else:
        preis = None

    st.markdown("---")

    if preis is not None:
        # Tippfehler-Fix: "Geschätzte" statt "Geschätzter" bei Mietpreis
        if typ_intern == "miete":
            st.markdown("### Geschätzte monatliche Miete")
        else:
            st.markdown(f"### Geschätzter {typ_bezeichnung(typ_intern)}")

        col_l, col_m, col_r = st.columns([1, 2, 1])
        with col_m:
            st.metric(
                label=f"{zimmer}-Zimmer-Wohnung, {flaeche} m² in {stadt}",
                value=chf(preis),
            )
            if typ_intern == "kauf":
                preis_m2 = preis / flaeche
                st.caption(f"ca. {chf(preis_m2)} pro m²")
            else:
                st.caption(f"ca. {chf(preis * 12)} pro Jahr")

        daten = daten_holen(typ_intern)
        if len(daten) > 0:
            schweizer_schnitt = daten["preis"].mean()
            st.info(f"Schweizer Durchschnitt: {chf(schweizer_schnitt)}")

        eur_kurs, usd_kurs = data_fetcher.wechselkurs_holen()
        st.markdown(f"**Preis in anderen Währungen:** € {float(preis) * eur_kurs:,.0f} EUR | $ {float(preis) * usd_kurs:,.0f} USD")
        st.caption("Wechselkurs: frankfurter.app · Live")
    else:
        st.info("Bitte Angaben eingeben und auf 'Preis schätzen' klicken.")


# ── Seite 2: Marktübersicht ───────────────────────────────────────────────────

def seite_markt():
    st.header("Marktübersicht Schweiz")

    typ_wahl = st.radio("Preistyp anzeigen:", ["Kaufpreise", "Mietpreise"], horizontal=True)
    typ_intern = "kauf" if typ_wahl == "Kaufpreise" else "miete"
    einheit = "CHF" if typ_intern == "kauf" else "CHF/Mt."

    daten = marktdaten_holen(typ_intern)
    stadtdaten = stadtdaten_holen()

    # Stadtdurchschnitte für Karte und Balkendiagramm berechnen
    agg = (
        daten.groupby("stadt", as_index=False)
        .agg(durchschnitt=("preis", "mean"), anzahl=("id", "count"))
        .merge(stadtdaten[["stadt", "lat", "lon", "kanton"]], on="stadt", how="left")
    )

    # ── Karte der Schweiz ─────────────────────────────────────────────────────
    st.subheader("Preiskarte Schweiz")
    st.caption("Die Karte zeigt den durchschnittlichen Immobilienpreis pro Stadt. Farben im roten Bereich bedeuten höhere Preise.")
    agg_karte = agg.copy()
    agg_karte["groesse"] = 10
    karte = px.scatter_mapbox(
        agg_karte,
        lat="lat", lon="lon",
        size="groesse",
        color="durchschnitt",
        hover_name="stadt",
        hover_data={"kanton": True, "durchschnitt": ":,.0f", "anzahl": True, "lat": False, "lon": False, "groesse": False},
        color_continuous_scale=[[0, "#1a7a4a"], [0.5, "#f4a261"], [1, "#d62828"]],
        zoom=6.5, height=430, size_max=40,
        labels={"durchschnitt": f"Ø {einheit}", "anzahl": "Inserate"},
    )
    karte.update_layout(mapbox_style="open-street-map", margin={"l": 0, "r": 0, "t": 0, "b": 0})
    st.plotly_chart(karte, use_container_width=True)

    # ── Balkendiagramm: Städtevergleich ──────────────────────────────────────
    st.subheader("Durchschnittspreise nach Stadt")
    st.caption("Vergleich der durchschnittlichen Preise aller Schweizer Städte in unserer Datenbank.")

    agg_sortiert = agg.sort_values("durchschnitt", ascending=True)
    # Dynamische Höhe damit alle Balken gut sichtbar sind
    chart_hoehe = max(380, len(agg_sortiert) * 48)

    balken = px.bar(
        agg_sortiert,
        x="durchschnitt", y="stadt",
        orientation="h",
        color="durchschnitt",
        color_continuous_scale=[[0, "#1a7a4a"], [0.5, "#f4a261"], [1, "#d62828"]],
        labels={"durchschnitt": f"Ø Preis ({einheit})", "stadt": "Stadt"},
        height=chart_hoehe,
    )
    # Zahlen innerhalb der Balken anzeigen – kein Abschneiden am Rand
    balken.update_traces(
        text=agg_sortiert["durchschnitt"].apply(lambda x: f"{x:,.0f}"),
        textposition="inside",
        insidetextanchor="end",
        textfont={"color": "white", "size": 13},
    )
    balken.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        margin={"l": 10, "r": 20, "t": 20, "b": 20},
        xaxis={"tickformat": ",.0f"},
    )
    st.plotly_chart(balken, use_container_width=True)

    # ── Scatter Plot: Fläche vs. Preis mit Trendlinie ─────────────────────────
    st.subheader("Wohnfläche vs. Preis")
    st.caption("Jeder Punkt steht für ein Inserat. Die gestrichelte Linie zeigt den allgemeinen Trend: grössere Wohnungen kosten mehr.")
    scatter = px.scatter(
        daten, x="flaeche", y="preis",
        color="stadt", opacity=0.55,
        labels={"flaeche": "Wohnfläche (m²)", "preis": f"Preis ({einheit})", "stadt": "Stadt"},
    )
    if len(daten) > 2:
        x_werte = daten["flaeche"].values
        y_werte = daten["preis"].values
        koeffizienten = np.polyfit(x_werte, y_werte, 1)
        poly = np.poly1d(koeffizienten)
        x_linie = np.linspace(x_werte.min(), x_werte.max(), 100)
        scatter.add_trace(go.Scatter(
            x=x_linie, y=poly(x_linie),
            mode="lines", name="Trend",
            line={"color": "#1b5e20", "width": 2, "dash": "dash"},
        ))
    scatter.update_layout(legend={"font": {"size": 12}})
    st.plotly_chart(scatter, use_container_width=True)


# ── Seite 3: Meine Immobilien ─────────────────────────────────────────────────

def seite_immobilien():
    st.header("Meine Immobilien")

    # Login prüfen
    if st.session_state["user_id"] is None:
        st.info("👤 Bitte melde dich links in der Seitenleiste an, um deine Immobilien zu verwalten.")
        return

    user_id = st.session_state["user_id"]

    # ── Formular: neue Immobilie hinzufügen ───────────────────────────────────
    st.subheader("Immobilie eintragen")

    # Eingabefelder
    col1, col2, col3 = st.columns(3)
    with col1:
        stadt = st.selectbox("Stadt", STADTLISTE, key="immo_stadt")
        zimmer = st.select_slider(
            "Anzahl Zimmer", [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0], value=3.0, key="immo_zimmer"
        )
        flaeche = st.slider("Wohnfläche (m²)", 25, 300, 80, key="immo_flaeche")
    with col2:
        baujahr = st.slider("Baujahr", 1900, 2026, 2000, key="immo_baujahr")
        stockwerk = st.slider("Stockwerk", 0, 15, 2, key="immo_stockwerk")
        parkplatz = st.checkbox("Parkplatz vorhanden", key="immo_parkplatz")
    with col3:
        typ_eingabe = st.radio("Preistyp", ["Kaufpreis", "Mietpreis"], key="immo_typ")
        if typ_eingabe == "Kaufpreis":
            preis = st.slider("Kaufpreis (CHF)", 200000, 5000000, 800000, step=10000, key="immo_preis_kauf")
            st.caption(f"CHF {preis:,.0f}".replace(",", "'"))
        else:
            preis = st.slider("Monatliche Miete (CHF)", 500, 10000, 2000, step=50, key="immo_preis_miete")
            st.caption(f"CHF {preis:,.0f}".replace(",", "'"))
        speichern = st.button("Eintrag speichern", type="primary", use_container_width=True)

    if speichern:
        typ_intern = "kauf" if typ_eingabe == "Kaufpreis" else "miete"
        database.einfuegen(user_id, stadt, flaeche, zimmer, stockwerk, int(parkplatz), baujahr, preis, typ_intern)
        st.success("Immobilie wurde gespeichert.")

    # ── Liste: gespeicherte Immobilien ────────────────────────────────────────
    st.markdown("---")
    st.subheader("Gespeicherte Einträge")

    typ_filter = st.radio("Anzeigen:", ["Alle", "Nur Kauf", "Nur Miete"], horizontal=True)
    if typ_filter == "Nur Kauf":
        anzeige_daten = database.laden("kauf", user_id=user_id)
    elif typ_filter == "Nur Miete":
        anzeige_daten = database.laden("miete", user_id=user_id)
    else:
        anzeige_daten = database.laden(user_id=user_id)

    if anzeige_daten.empty:
        st.info("Noch keine Immobilien gespeichert. Trage oben deine erste ein!")
        return

    # Spalten auf Deutsch umbenennen für die Anzeige
    anzeige = anzeige_daten.rename(columns={
        "stadt": "Stadt", "kanton": "Kanton", "flaeche": "Fläche (m²)",
        "zimmer": "Zimmer", "stockwerk": "Stockwerk", "parkplatz": "Parkplatz",
        "baujahr": "Baujahr", "preis": "Preis (CHF)", "typ": "Typ",
    }).drop(columns=["id", "user_id"], errors="ignore")
    anzeige.insert(0, "Nr.", range(1, len(anzeige) + 1))
    anzeige["Typ"] = anzeige["Typ"].map({"kauf": "Kauf", "miete": "Miete"})
    anzeige["Parkplatz"] = anzeige["Parkplatz"].map({1: "Ja", 0: "Nein"})

    st.dataframe(anzeige, use_container_width=True, hide_index=True)

    # Lösch-Buttons pro Zeile
    st.markdown("---")
    for nr, (_, zeile) in enumerate(anzeige_daten.iterrows(), start=1):
        col1, col2 = st.columns([8, 1])
        with col1:
            st.write(f"#{nr} | {zeile['stadt']} | {zeile['flaeche']} m² | {zeile['zimmer']} Zi. | {zeile['baujahr']} | CHF {zeile['preis']:,.0f}")
        with col2:
            if st.button("🗑️", key=f"loeschen_{zeile['id']}"):
                conn = database.verbindung()
                conn.execute("DELETE FROM immobilien WHERE id=? AND user_id=?", (zeile['id'], user_id))
                conn.commit()
                conn.close()
                st.rerun()


# ── Navigation ────────────────────────────────────────────────────────────────

st.sidebar.title(APP_NAME)
st.sidebar.caption(APP_UNTERTITEL)
st.sidebar.markdown("---")
seite = st.sidebar.radio("Navigation", SEITEN, label_visibility="collapsed")

# Login-Bereich in der Sidebar anzeigen
sidebar_login()

if seite == SEITEN[0]:
    seite_preisschaetzung()
elif seite == SEITEN[1]:
    seite_markt()
else:
    seite_immobilien()
