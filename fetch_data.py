# -*- coding: utf-8 -*-
"""
Avoin Kuntadonitsi – Automaattinen tiedonhaku (Vain avoimet rajapinnat: THL Sotkanet & SYKE)
Copyright (c) 2026 Mika Lammi | SPDX-License-Identifier: MIT
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


def evaluate_status(value, threshold, direction):
    """Laskee suhdeluvun (100 % = kestävä tavoiteraja) ja tarkistaa, onko mittari vihreällä kehällä."""
    val = float(value)
    thresh = float(threshold)
    if direction == "lower_is_better":
        ratio_pct = round((val / thresh) * 100, 1) if thresh > 0 else 0.0
        is_safe = "true" if val <= thresh else "false"
    else:
        ratio_pct = round((thresh / val) * 100, 1) if val > 0 else 0.0
        is_safe = "true" if val >= thresh else "false"
    return ratio_pct, is_safe


def fetch_sotkanet_series(indicator_id, muni_code):
    current_year = datetime.now().year
    years = list(range(2018, current_year + 1))
    year_params = "&".join([f"years={y}" for y in years])
    url = f"https://sotkanet.fi/rest/1.1/json?indicator={indicator_id}&{year_params}&genders=total"

    resp = requests.get(url, headers=HEADERS, timeout=20)
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


def fetch_syke_khk_series(muni_code):
    """Hakee SYKE:n alueelliset KHK-päästöt (SYKE OData tai SYKE-Sotkanet ID 4007)."""
    muni_code_padded = str(muni_code).zfill(3)
    url = f"https://avoindata.syke.fi/odata/KHKPaastot?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            items = r.json().get("value", [])
            series = [
                (int(x["Vuosi"]), round(float(x["PaastotPerAsukas"]), 2))
                for x in items if "Vuosi" in x and "PaastotPerAsukas" in x
            ]
            if series:
                series.sort(key=lambda x: x[0])
                return series, "SYKE Hinku API"
    except Exception:
        pass

    # SYKE:n virallinen peilaus Sotkanet-rajapinnassa (ID 4007: KHK-päästöt asukasta kohti)
    series, _ = fetch_sotkanet_series(4007, muni_code)
    return series, "SYKE / Sotkanet API (ID 4007)"


def fetch_syke_consumption_series(muni_code):
    """Hakee SYKE:n kulutusperusteisen hiilijalanjäljen avoimesta rajapinnasta."""
    muni_code_padded = str(muni_code).zfill(3)
    url = f"https://avoindata.syke.fi/odata/KulutusPaastot?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    items = r.json().get("value", [])
    series = [
        (int(x["Vuosi"]), round(float(x["PaastotPerAsukas"]), 2))
        for x in items if "Vuosi" in x and "PaastotPerAsukas" in x
    ]
    if not series:
        raise ValueError("SYKE Kulutus API ei palauttanut kuntakohtaisia rivejä")
    series.sort(key=lambda x: x[0])
    return series, "SYKE Kulutus API"


def fetch_syke_water_status(muni_code):
    """Hakee pintavesien tilan SYKE:n OData-rajapinnasta."""
    muni_code_padded = str(muni_code).zfill(3)
    url = f"https://avoindata.syke.fi/odata/PintavesienTila?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    items = r.json().get("value", [])
    if not items:
        raise ValueError("SYKE PintavesienTila API ei palauttanut rivejä")

    good_or_high = sum(
        1 for x in items
        if str(x.get("EkologinenTila", "")).lower() in ["erinomainen", "hyvä", "hyva", "1", "2"]
    )
    good_share = max(0.1, good_or_high / len(items))
    load_index = round((1.0 / good_share) * 100.0, 1)
    yr = max(int(x.get("Vuosi", datetime.now().year)) for x in items)
    return [(yr, load_index)], "SYKE Pintavesien tila API"


def fetch_syke_landuse_pressure(muni_code):
    """Hakee maankäyttöpaineen SYKE:n OData-rajapinnasta."""
    muni_code_padded = str(muni_code).zfill(3)
    url = f"https://avoindata.syke.fi/odata/Maankaytto?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    items = r.json().get("value", [])
    if not items:
        raise ValueError("SYKE Maankäyttö API ei palauttanut rivejä")

    latest = sorted(items, key=lambda x: x.get("Vuosi", 0))[-1]
    val = round(float(latest["KuormitusIndeksi"]), 1)
    yr = int(latest["Vuosi"])
    return [(yr, val)], "SYKE Liiteri API"


def get_indicator_series(ind, muni_code):
    """
    Hakee datan suoraan rajapinnasta. Jos rajapinta palauttaa virheen tai dataa ei ole,
    palautetaan tyhjä lista ja 'no_data'-merkintä (ei manuaalisia varalukuja).
    """
    ind_id = str(ind.get("id", "")).strip()
    src = str(ind.get("source", "")).lower().strip()

    try:
        if "indicator_id" in ind and ind["indicator_id"]:
            return fetch_sotkanet_series(ind["indicator_id"], muni_code)
        elif src == "syke_khk":
            return fetch_syke_khk_series(muni_code)
        elif src == "syke_kulutus":
            return fetch_syke_consumption_series(muni_code)
        elif src == "syke_vesistot":
            return fetch_syke_water_status(muni_code)
        elif src == "syke_maankaytto":
            return fetch_syke_landuse_pressure(muni_code)
        else:
            raise ValueError(f"Tuntematon rajapintalähde: {src}")
    except Exception as e:
        print(f"⚠️ Rajapintahaku epäonnistui mittarille '{ind_id}': {e} -> Merkitään 0 (Ei dataa).")
        return None, "Ei saatavilla (Rajapintavirhe)"


def main():
    config = load_config()
    muni_code = config.get("municipality", {}).get("sotkanet_code", "286")

    now_dt = datetime.now()
    updated_at_str = now_dt.strftime("%d.%m.%Y klo %H:%M")
    current_month_period = now_dt.strftime("%Y-%m")

    results_rows = []
    history_rows = []

    for ind in config.get("indicators", []):
        ind_id = str(ind["id"]).strip()
        name = ind["name"]
        domain = ind["domain"]
        threshold = float(ind["threshold"])
        unit = ind["unit"]
        direction = ind.get("direction", "lower_is_better")

        series, source_label = get_indicator_series(ind, muni_code)

        if series is None or len(series) == 0:
            # Dataa ei saatu rajapinnasta: merkitään arvoksi 0 ja tilaksi 'no_data'
            results_rows.append({
                "id": ind_id,
                "name": name,
                "domain": domain,
                "source": source_label,
                "value": 0.0,
                "threshold": threshold,
                "unit": unit,
                "direction": direction,
                "year": "-",
                "ratio_pct": 0.0,
                "is_safe": "no_data",
                "updated_at": updated_at_str
            })
        else:
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

    df_results = pd.DataFrame(results_rows)
    df_results.to_csv("doughnut_results.csv", index=False, encoding="utf-8")
    print(f"✅ Tallennettu doughnut_results.csv ({len(df_results)} mittaria).")

    df_new_hist = pd.DataFrame(history_rows)
    if os.path.exists("doughnut_history.csv") and not df_new_hist.empty:
        try:
            df_old_hist = pd.read_csv("doughnut_history.csv", encoding="utf-8")
            df_combined = pd.concat([df_old_hist, df_new_hist], ignore_index=True)
            df_combined.drop_duplicates(subset=["id", "period"], keep="last", inplace=True)
        except Exception:
            df_combined = df_new_hist
    else:
        df_combined = df_new_hist

    if not df_combined.empty:
        df_combined.sort_values(by=["id", "period"], inplace=True)
        df_combined.to_csv("doughnut_history.csv", index=False, encoding="utf-8")
        print(f"✅ Tallennettu doughnut_history.csv ({len(df_combined)} aikasarjariviä).")


if __name__ == "__main__":
    main()
