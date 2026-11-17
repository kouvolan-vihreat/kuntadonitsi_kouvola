# -*- coding: utf-8 -*-
"""
Avoin Kuntadonitsi – Automaattinen tiedonhaku (THL Sotkanet & SYKE Avoimet Rajapinnat)
Copyright (c) 2026 Mika Lammi
SPDX-FileCopyrightText: 2026 Mika Lammi
SPDX-License-Identifier: MIT
"""

import os
from datetime import datetime
import yaml
import requests
import pandas as pd

HEADERS = {
    "User-Agent": "AvoinKuntadonitsi/1.0 (https://github.com; Open Municipal Doughnut)",
    "Accept": "application/json"
}


def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_manual_fallbacks(path="manual_indicators.csv"):
    """Lukee manual_indicators.csv-tiedoston varajärjestelmäksi ja mahdollisille omille lisämittareille."""
    if not os.path.exists(path):
        return {}
    df = pd.read_csv(path)
    fallbacks = {}
    for _, row in df.iterrows():
        fallbacks[str(row["id"]).strip()] = row.to_dict()
    return fallbacks


def evaluate_status(value, threshold, direction):
    """Laskee suhdeluvun (100 % = kestävä tavoiteraja) ja tarkistaa, onko mittari vihreällä kehällä."""
    val = float(value)
    thresh = float(threshold)
    if direction == "lower_is_better":
        ratio_pct = round((val / thresh) * 100, 1) if thresh > 0 else 0.0
        is_safe = val <= thresh
    else:
        ratio_pct = round((thresh / val) * 100, 1) if val > 0 else 999.0
        is_safe = val >= thresh
    return ratio_pct, is_safe


# ==============================================================================
# 1. THL SOTKANET REST API (Sosiaalinen perusta & tukimittarit)
# ==============================================================================
def fetch_sotkanet_series(indicator_id, muni_code, years=None):
    if years is None:
        current_year = datetime.now().year
        years = list(range(2018, current_year + 1))

    year_params = "&".join([f"years={y}" for y in years])
    url = f"https://sotkanet.fi/rest/1.1/json?indicator={indicator_id}&{year_params}&genders=total"

    resp = requests.get(url, headers=HEADERS, timeout=25)
    resp.raise_for_status()
    data = resp.json()

    muni_rows = [
        r for r in data
        if str(r.get("region")) == str(muni_code) and r.get("value") is not None
    ]
    if not muni_rows:
        raise ValueError(f"Sotkanet ID {indicator_id}: ei dataa kunnalle {muni_code}")

    muni_rows.sort(key=lambda x: x["year"])
    series = [(int(r["year"]), round(float(r["value"]), 2)) for r in muni_rows]
    return series, f"SOTKANET (ID {indicator_id})"


# ==============================================================================
# 2. SYKE AVOIMET RAJAPINNAT (Ekologinen katto)
# ==============================================================================
def fetch_syke_khk_series(muni_code, muni_name):
    """
    Hakee kunnan asukaskohtaiset Hinku-kasvihuonekaasupäästöt (t CO2e/as.)
    SYKE:n avoimesta päästötietopalvelusta (REST / OData / JSON).
    """
    muni_code_padded = str(muni_code).zfill(3)
    endpoints = [
        f"https://paastot.hiilineutraalisuomi.fi/api/v1/emissions?municipality={muni_code_padded}&calculation=hinku",
        f"https://avoindata.syke.fi/odata/KHKPaastot?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    ]

    for url in endpoints:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                js = r.json()
                items = js.get("value", js) if isinstance(js, dict) else js
                if isinstance(items, list) and len(items) > 0:
                    series = []
                    for item in items:
                        yr = item.get("year") or item.get("Vuosi")
                        val = item.get("emissionsPerCapita") or item.get("PaastotPerAsukas")
                        if yr is not None and val is not None:
                            series.append((int(yr), round(float(val), 2)))
                    if series:
                        series.sort(key=lambda x: x[0])
                        return series, "SYKE Hinku API"
        except Exception:
            continue

    raise RuntimeError("SYKE KHK-rajapinta ei palauttanut suoraa sarjaa, käytetään tarkistettua SYKE-arvoa.")


def fetch_syke_consumption_series(muni_code, muni_name):
    """
    Hakee kunnan kulutusperusteisen hiilijalanjäljen (t CO2e/as.)
    SYKE:n kulutuspäästöjen avoimesta tietopalvelusta.
    """
    muni_code_padded = str(muni_code).zfill(3)
    endpoints = [
        f"https://kulutus.hiilineutraalisuomi.fi/api/v1/emissions?municipality={muni_code_padded}",
        f"https://avoindata.syke.fi/odata/KulutusPaastot?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    ]

    for url in endpoints:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                js = r.json()
                items = js.get("value", js) if isinstance(js, dict) else js
                if isinstance(items, list) and len(items) > 0:
                    series = []
                    for item in items:
                        yr = item.get("year") or item.get("Vuosi")
                        val = item.get("perCapita") or item.get("PaastotPerAsukas")
                        if yr is not None and val is not None:
                            series.append((int(yr), round(float(val), 2)))
                    if series:
                        series.sort(key=lambda x: x[0])
                        return series, "SYKE Kulutus API"
        except Exception:
            continue

    raise RuntimeError("SYKE Kulutus-rajapinta ei vastannut suoraan, käytetään tarkistettua SYKE-arvoa.")


def fetch_syke_water_status(muni_code, muni_name):
    """
    Hakee kunnan pintavesimuodostumien ekologisen tilan SYKE:n OGC API Features /
    OData -rajapinnasta ja laskee ravinnekuormitusindeksin (100 % = kaikki vedet
    hyvässä tai erinomaisessa tilassa).
    """
    muni_code_padded = str(muni_code).zfill(3)
    odata_url = (
        f"https://avoindata.syke.fi/odata/PintavesienTila"
        f"?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    )
    try:
        r = requests.get(odata_url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            items = r.json().get("value", [])
            if items:
                good_or_high = sum(
                    1 for x in items
                    if str(x.get("EkologinenTila", "")).lower() in ["erinomainen", "hyvä", "hyva", "1", "2"]
                )
                good_share = max(0.1, good_or_high / len(items))
                load_index = round((1.0 / good_share) * 100.0, 1)
                yr = max(int(x.get("Vuosi", 2024)) for x in items)
                return [(yr, load_index)], "SYKE Pintavesien tila API"
    except Exception:
        pass

    raise RuntimeError("SYKE Vesistö-rajapinta ei vastannut suoraan, käytetään tarkistettua SYKE-arvoa.")


def fetch_syke_landuse_pressure(muni_code, muni_name):
    """
    Hakee maankäyttöpaineen / rakennetun ympäristön suhteen SYKE Liiteri /
    Sotkanet-ympäristöindikaattoreista.
    """
    odata_url = (
        f"https://avoindata.syke.fi/odata/Maankaytto"
        f"?$filter=Kuntakoodi eq '{str(muni_code).zfill(3)}'&$format=json"
    )
    try:
        r = requests.get(odata_url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            items = r.json().get("value", [])
            if items:
                latest = sorted(items, key=lambda x: x.get("Vuosi", 2024))[-1]
                val = round(float(latest.get("KuormitusIndeksi", 88.0)), 1)
                yr = int(latest.get("Vuosi", 2024))
                return [(yr, val)], "SYKE Liiteri API"
    except Exception:
        pass

    raise RuntimeError("SYKE Maankäyttö-rajapinta ei vastannut suoraan, käytetään tarkistettua SYKE-arvoa.")


def get_indicator_series(ind, muni_code, muni_name, fallbacks):
    """
    Reitittää mittarin oikeaan rajapintaan (Sotkanet tai SYKE) ja käyttää
    tarvittaessa manual_indicators.csv-tiedostoa varajärjestelmänä.
    """
    ind_id = ind["id"]
    src = ind.get("source", "").lower()

    try:
        if src == "sotkanet":
            return fetch_sotkanet_series(ind["indicator_id"], muni_code)
        elif src == "syke_khk":
            return fetch_syke_khk_series(muni_code, muni_name)
        elif src == "syke_kulutus":
            return fetch_syke_consumption_series(muni_code, muni_name)
        elif src == "syke_vesistot":
            return fetch_syke_water_status(muni_code, muni_name)
        elif src == "syke_maankaytto":
            return fetch_syke_landuse_pressure(muni_code, muni_name)
    except Exception as e:
        print(f"ℹ️ Rajapintahaku ({ind_id}) käytti varajärjestelmää: {e}")

    # Varajärjestelmä (Fallback): luetaan arvo manual_indicators.csv-tiedostosta
    if ind_id in fallbacks:
        fb = fallbacks[ind_id]
        yr = int(fb.get("year", 2024))
        val = round(float(fb.get("value", 0.0)), 2)
        src_label = str(fb.get("source", "SYKE"))
        return [(yr, val)], src_label

    raise ValueError(f"Mittarille '{ind_id}' ei saatu arvoa rajapinnasta eikä manual_indicators.csv-tiedostosta.")


def main():
    config = load_config()
    muni_code = config["municipality"]["sotkanet_code"]
    muni_name = config["municipality"]["name"]
    fallbacks = load_manual_fallbacks()

    now_dt = datetime.now()
    updated_at_str = now_dt.strftime("%d.%m.%Y klo %H:%M")
    current_month_period = now_dt.strftime("%Y-%m")

    results_rows = []
    history_rows = []

    processed_ids = set()

    for ind in config.get("indicators", []):
        ind_id = ind["id"]
        processed_ids.add(ind_id)
        name = ind["name"]
        domain = ind["domain"]
        threshold = float(ind["threshold"])
        unit = ind["unit"]
        direction = ind.get("direction", "lower_is_better")

        series, source_label = get_indicator_series(ind, muni_code, muni_name, fallbacks)
        latest_year, latest_val = series[-1]
        ratio_pct, is_safe = evaluate_status(latest_val, threshold, direction)

        results_rows.append({
            "id": ind_id,
            "name": name,
            "domain": domain,
            "source": source_label,
            "value": latest_val,
            "threshold": threshold,
            "unit": unit,
            "direction": direction,
            "year": latest_year,
            "ratio_pct": ratio_pct,
            "is_safe": is_safe,
            "updated_at": updated_at_str
        })

        # Tallennetaan vuosihistoria
        for yr, val in series:
            r_pct, safe_flag = evaluate_status(val, threshold, direction)
            history_rows.append({
                "id": ind_id,
                "name": name,
                "domain": domain,
                "period": str(yr),
                "record_type": "Vuositilasto",
                "value": val,
                "threshold": threshold,
                "unit": unit,
                "ratio_pct": r_pct,
                "is_safe": safe_flag
            })

        # Tallennetaan kuukausittainen ajotilanne
        history_rows.append({
            "id": ind_id,
            "name": name,
            "domain": domain,
            "period": current_month_period,
            "record_type": "Kuukausiseuranta",
            "value": latest_val,
            "threshold": threshold,
            "unit": unit,
            "ratio_pct": ratio_pct,
            "is_safe": is_safe
        })

    # Jos käyttäjä on lisännyt manual_indicators.csv-tiedostoon omia ylimääräisiä mittareita,
    # joita ei ole config.yaml-tiedostossa, otetaan myös ne mukaan!
    for fb_id, fb in fallbacks.items():
        if fb_id not in processed_ids:
            val = round(float(fb["value"]), 2)
            thresh = float(fb["threshold"])
            direction = fb.get("direction", "lower_is_better")
            yr = int(fb.get("year", 2024))
            ratio_pct, is_safe = evaluate_status(val, thresh, direction)

            results_rows.append({
                "id": fb_id,
                "name": fb["name"],
                "domain": fb["domain"],
                "source": fb["source"],
                "value": val,
                "threshold": thresh,
                "unit": fb["unit"],
                "direction": direction,
                "year": yr,
                "ratio_pct": ratio_pct,
                "is_safe": is_safe,
                "updated_at": updated_at_str
            })

            history_rows.append({
                "id": fb_id,
                "name": fb["name"],
                "domain": fb["domain"],
                "period": str(yr),
                "record_type": "Vuositilasto",
                "value": val,
                "threshold": thresh,
                "unit": fb["unit"],
                "ratio_pct": ratio_pct,
                "is_safe": is_safe
            })

    # Tallennetaan tuore tilannekuva (doughnut_results.csv)
    df_results = pd.DataFrame(results_rows)
    df_results.to_csv("doughnut_results.csv", index=False, encoding="utf-8")
    print(f"✅ Tallennettu doughnut_results.csv ({len(df_results)} mittaria).")

    # Yhdistetään olemassa olevaan historiatiedostoon ilman duplikaatteja
    df_new_hist = pd.DataFrame(history_rows)
    if os.path.exists("doughnut_history.csv"):
        try:
            df_old_hist = pd.read_csv("doughnut_history.csv")
            df_combined = pd.concat([df_old_hist, df_new_hist], ignore_index=True)
            df_combined.drop_duplicates(subset=["id", "period"], keep="last", inplace=True)
        except Exception:
            df_combined = df_new_hist
    else:
        df_combined = df_new_hist

    df_combined.sort_values(by=["id", "period"], inplace=True)
    df_combined.to_csv("doughnut_history.csv", index=False, encoding="utf-8")
    print(f"✅ Tallennettu doughnut_history.csv ({len(df_combined)} aikasarjariviä).")


if __name__ == "__main__":
    main()
