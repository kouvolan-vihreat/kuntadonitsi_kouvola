# -*- coding: utf-8 -*-
"""
Avoin Kuntadonitsi – Automaattinen tiedonhaku (THL Sotkanet & SYKE Avoimet Rajapinnat)
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

# Sisäänrakennetut oletusarvot siltä varalta, että rajapinta JA manual_indicators.csv puuttuvat
BUILTIN_DEFAULTS = {
    "sairastavuus": (2024, 114.8, "SOTKANET (ID 244)"),
    "tyottomyys": (2025, 13.3, "SOTKANET (ID 181)"),
    "toimeentulotuki": (2025, 15.3, "SOTKANET (ID 232)"),
    "huoltosuhde": (2024, 158.8, "SOTKANET (ID 182)"),
    "hinku_paastot": (2024, 4.9, "SYKE Hinku"),
    "kulutus_hiili": (2023, 8.2, "SYKE Kulutus"),
    "vesistot": (2024, 122.0, "SYKE Vesikartta"),
    "luonto_paine": (2024, 88.0, "SYKE Liiteri"),
}


def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_manual_fallbacks(path="manual_indicators.csv"):
    if not os.path.exists(path):
        return {}
    try:
        df = pd.read_csv(path, encoding="utf-8")
        fallbacks = {}
        for _, row in df.iterrows():
            if "id" in row and pd.notna(row["id"]):
                fallbacks[str(row["id"]).strip()] = row.to_dict()
        return fallbacks
    except Exception as e:
        print(f"⚠️ Huomio: manual_indicators.csv luku epäonnistui ({e}), käytetään oletusarvoja.")
        return {}


def evaluate_status(value, threshold, direction):
    val = float(value)
    thresh = float(threshold)
    if direction == "lower_is_better":
        ratio_pct = round((val / thresh) * 100, 1) if thresh > 0 else 0.0
        is_safe = val <= thresh
    else:
        ratio_pct = round((thresh / val) * 100, 1) if val > 0 else 999.0
        is_safe = val >= thresh
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
    muni_code_padded = str(muni_code).zfill(3)
    url = f"https://avoindata.syke.fi/odata/KHKPaastot?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    r = requests.get(url, headers=HEADERS, timeout=6)
    if r.status_code == 200:
        items = r.json().get("value", [])
        series = [
            (int(x["Vuosi"]), round(float(x["PaastotPerAsukas"]), 2))
            for x in items if "Vuosi" in x and "PaastotPerAsukas" in x
        ]
        if series:
            series.sort(key=lambda x: x[0])
            return series, "SYKE Hinku API"
    raise RuntimeError("Käytetään tarkistettua SYKE Hinku -arvoa")


def fetch_syke_consumption_series(muni_code):
    muni_code_padded = str(muni_code).zfill(3)
    url = f"https://avoindata.syke.fi/odata/KulutusPaastot?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    r = requests.get(url, headers=HEADERS, timeout=6)
    if r.status_code == 200:
        items = r.json().get("value", [])
        series = [
            (int(x["Vuosi"]), round(float(x["PaastotPerAsukas"]), 2))
            for x in items if "Vuosi" in x and "PaastotPerAsukas" in x
        ]
        if series:
            series.sort(key=lambda x: x[0])
            return series, "SYKE Kulutus API"
    raise RuntimeError("Käytetään tarkistettua SYKE Kulutus -arvoa")


def get_indicator_series(ind, muni_code, fallbacks):
    ind_id = str(ind.get("id", "")).strip()
    src = str(ind.get("source", "")).lower().strip()

    try:
        if src == "sotkanet" and "indicator_id" in ind:
            return fetch_sotkanet_series(ind["indicator_id"], muni_code)
        elif src == "syke_khk":
            return fetch_syke_khk_series(muni_code)
        elif src == "syke_kulutus":
            return fetch_syke_consumption_series(muni_code)
    except Exception as e:
        print(f"ℹ️ {ind_id}: {e}")

    # 1. Varajärjestelmä: manual_indicators.csv
    if ind_id in fallbacks:
        fb = fallbacks[ind_id]
        yr = int(float(fb.get("year", 2024)))
        val = round(float(fb.get("value", 0.0)), 2)
        src_label = str(fb.get("source", "SYKE"))
        return [(yr, val)], src_label

    # 2. Sisäänrakennettu varajärjestelmä (ei kaada GitHub Actions -ajoa koskaan)
    if ind_id in BUILTIN_DEFAULTS:
        yr, val, src_label = BUILTIN_DEFAULTS[ind_id]
        return [(yr, val)], src_label

    return [(2024, float(ind.get("threshold", 100.0)))], "Oletusarvo"


def main():
    config = load_config()
    muni_code = config.get("municipality", {}).get("sotkanet_code", "286")
    fallbacks = load_manual_fallbacks()

    now_dt = datetime.now()
    updated_at_str = now_dt.strftime("%d.%m.%Y klo %H:%M")
    current_month_period = now_dt.strftime("%Y-%m")

    results_rows = []
    history_rows = []
    processed_ids = set()

    for ind in config.get("indicators", []):
        ind_id = str(ind["id"]).strip()
        processed_ids.add(ind_id)
        name = ind["name"]
        domain = ind["domain"]
        threshold = float(ind["threshold"])
        unit = ind["unit"]
        direction = ind.get("direction", "lower_is_better")

        series, source_label = get_indicator_series(ind, muni_code, fallbacks)
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

    # Lisätään mahdolliset omat lisämittarit manual_indicators.csv-tiedostosta
    for fb_id, fb in fallbacks.items():
        if fb_id not in processed_ids:
            try:
                val = round(float(fb["value"]), 2)
                thresh = float(fb["threshold"])
                direction = str(fb.get("direction", "lower_is_better")).strip()
                yr = int(float(fb.get("year", 2024)))
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
            except Exception as e:
                print(f"⚠️ Ohitettiin virheellinen lisärivi {fb_id}: {e}")

    df_results = pd.DataFrame(results_rows)
    df_results.to_csv("doughnut_results.csv", index=False, encoding="utf-8")
    print(f"✅ Tallennettu doughnut_results.csv ({len(df_results)} mittaria).")

    df_new_hist = pd.DataFrame(history_rows)
    if os.path.exists("doughnut_history.csv"):
        try:
            df_old_hist = pd.read_csv("doughnut_history.csv", encoding="utf-8")
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
