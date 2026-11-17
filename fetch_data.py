# -*- coding: utf-8 -*-
"""
Avoin Kuntadonitsi – Automaattinen tiedonhaku (THL Sotkanet & SYKE-indikaattorit)
Copyright (c) 2026 Mika Lammi | SPDX-License-Identifier: MIT
"""

import os
from datetime import datetime
import yaml
import requests
import pandas as pd

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}


def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


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


def resolve_sotkanet_region_id(muni_code, muni_name):
    code_clean = str(muni_code).strip().lstrip("0")
    code_padded = str(muni_code).strip().zfill(3)
    name_clean = str(muni_name).strip().lower()

    try:
        r = requests.get("https://sotkanet.fi/rest/1.1/regions", headers=HEADERS, timeout=20)
        if r.status_code == 200:
            for reg in r.json():
                reg_code = str(reg.get("code", "")).strip()
                reg_id = str(reg.get("id", "")).strip()
                titles = reg.get("title", {})
                fi_title = str(titles.get("fi", "")).strip().lower() if isinstance(titles, dict) else ""
                if reg_code in [code_clean, code_padded] or fi_title == name_clean:
                    return reg_id, code_padded
    except Exception:
        pass

    return code_clean, code_padded


def fetch_sotkanet_series(indicator_id, sotkanet_region_id, muni_code_padded):
    current_year = datetime.now().year
    years = list(range(2018, current_year + 1))
    year_params = "&".join([f"years={y}" for y in years])
    url = f"https://sotkanet.fi/rest/1.1/json?indicator={indicator_id}&{year_params}&genders=total"

    resp = requests.get(url, headers=HEADERS, timeout=25)
    resp.raise_for_status()
    data = resp.json()

    valid_codes = {str(sotkanet_region_id), str(muni_code_padded), str(muni_code_padded).lstrip("0")}
    muni_rows = [
        r for r in data
        if str(r.get("region")) in valid_codes and r.get("value") is not None
    ]
    if not muni_rows:
        raise ValueError(f"Sotkanet ID {indicator_id}: ei dataa kunnalle")

    muni_rows.sort(key=lambda x: int(x["year"]))
    return [(int(r["year"]), round(float(r["value"]), 2)) for r in muni_rows]


def main():
    config = load_config()
    muni_code = config["municipality"]["sotkanet_code"]
    muni_name = config["municipality"]["name"]
    sotkanet_region_id, muni_code_padded = resolve_sotkanet_region_id(muni_code, muni_name)

    now_dt = datetime.now()
    updated_at_str = now_dt.strftime("%d.%m.%Y klo %H:%M")
    current_month_period = now_dt.strftime("%Y-%m")

    results_rows = []
    history_rows = []

    # 1. Haetaan sosiaalisen perustan mittarit Sotkanetista
    for ind in config.get("indicators", []):
        ind_id = ind["id"]
        name = ind["name"]
        domain = ind["domain"]
        threshold = float(ind["threshold"])
        unit = ind["unit"]
        direction = ind.get("direction", "lower_is_better")
        sotka_id = ind["indicator_id"]

        series = fetch_sotkanet_series(sotka_id, sotkanet_region_id, muni_code_padded)
        latest_year, latest_val = series[-1]
        ratio_pct, is_safe = evaluate_status(latest_val, threshold, direction)

        results_rows.append({
            "id": ind_id,
            "name": name,
            "domain": domain,
            "source": f"SOTKANET (ID {sotka_id})",
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

    # 2. Luetaan ekologisen katon mittarit manual_indicators.csv-tiedostosta
    if os.path.exists("manual_indicators.csv"):
        df_man = pd.read_csv("manual_indicators.csv", encoding="utf-8")
        for _, row in df_man.iterrows():
            ind_id = str(row["id"]).strip()
            name = str(row["name"]).strip()
            domain = str(row["domain"]).strip()
            source = str(row["source"]).strip()
            val = round(float(row["value"]), 2)
            threshold = float(row["threshold"])
            unit = str(row["unit"]).strip()
            direction = str(row.get("direction", "lower_is_better")).strip()
            yr = int(row["year"])

            ratio_pct, is_safe = evaluate_status(val, threshold, direction)

            results_rows.append({
                "id": ind_id,
                "name": name,
                "domain": domain,
                "source": source,
                "value": val,
                "threshold": threshold,
                "unit": unit,
                "direction": direction,
                "year": yr,
                "ratio_pct": ratio_pct,
                "is_safe": is_safe,
                "updated_at": updated_at_str
            })

            history_rows.append({
                "id": ind_id,
                "name": name,
                "domain": domain,
                "period": str(yr),
                "record_type": "Vuositilasto",
                "value": val,
                "threshold": threshold,
                "unit": unit,
                "ratio_pct": ratio_pct,
                "is_safe": is_safe
            })

            history_rows.append({
                "id": ind_id,
                "name": name,
                "domain": domain,
                "period": current_month_period,
                "record_type": "Kuukausiseuranta",
                "value": val,
                "threshold": threshold,
                "unit": unit,
                "ratio_pct": ratio_pct,
                "is_safe": is_safe
            })

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
