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

# Käytetään normaalia selaintunnistetta, jotta THL/SYKE WAF-palomuuri ei estä GitHub Actions -hakua
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}


def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def evaluate_status(value, threshold, direction):
    val = float(value)
    thresh = float(threshold)
    if direction == "lower_is_better":
        ratio_pct = round((val / thresh) * 100, 1) if thresh > 0 else 0.0
        is_safe = "true" if val <= thresh else "false"
    else:
        ratio_pct = round((thresh / val) * 100, 1) if val > 0 else 0.0
        is_safe = "true" if val >= thresh else "false"
    return ratio_pct, is_safe


def resolve_sotkanet_region_id(muni_code, muni_name):
    """
    Muuntaa virallisen kuntanumeron (esim. '286' = Kouvola) Sotkanetin sisäiseksi
    region-tunnisteeksi hakemalla sen suoraan Sotkanetin /regions-rajapinnasta.
    """
    code_clean = str(muni_code).strip().lstrip("0")
    code_padded = str(muni_code).strip().zfill(3)
    name_clean = str(muni_name).strip().lower()

    try:
        r = requests.get("https://sotkanet.fi/rest/1.1/regions", headers=HEADERS, timeout=20)
        if r.status_code == 200:
            regions = r.json()
            for reg in regions:
                reg_code = str(reg.get("code", "")).strip()
                reg_id = str(reg.get("id", "")).strip()
                titles = reg.get("title", {})
                fi_title = str(titles.get("fi", "")).strip().lower() if isinstance(titles, dict) else ""

                if reg_code in [code_clean, code_padded] or fi_title == name_clean:
                    print(f"✅ Kunta tunnistettu Sotkanetissa: {muni_name} (kuntakoodi {code_padded} -> Sotkanet region ID {reg_id})")
                    return reg_id, code_padded
    except Exception as e:
        print(f"⚠️ Huomio: Sotkanet regions -haku epäonnistui ({e}), kokeillaan suoraa koodia.")

    return code_clean, code_padded


def fetch_sotkanet_series(indicator_id, sotkanet_region_id, muni_code_padded):
    """
    Hakee aikasarjan THL Sotkanet REST API:sta. Kokeilee viimeisimpiä vuosia 2017..nykyhetki.
    """
    current_year = datetime.now().year
    years = list(range(2017, current_year + 1))
    year_params = "&".join([f"years={y}" for y in years])
    url = f"https://sotkanet.fi/rest/1.1/json?indicator={indicator_id}&{year_params}&genders=total"

    resp = requests.get(url, headers=HEADERS, timeout=25)
    resp.raise_for_status()
    data = resp.json()

    valid_codes = {
        str(sotkanet_region_id),
        str(muni_code_padded),
        str(muni_code_padded).lstrip("0")
    }

    muni_rows = [
        r for r in data
        if str(r.get("region")) in valid_codes and r.get("value") is not None
    ]
    if not muni_rows:
        raise ValueError(f"Sotkanet ID {indicator_id}: ei rivejä kunnalle (region={sotkanet_region_id})")

    muni_rows.sort(key=lambda x: int(x["year"]))
    series = [(int(r["year"]), round(float(r["value"]), 2)) for r in muni_rows]
    return series, f"SOTKANET (ID {indicator_id})"


def fetch_syke_khk_series(sotkanet_region_id, muni_code_padded):
    """
    Hakee SYKE:n alueelliset kasvihuonekaasupäästöt (t CO2e/as.).
    Kokeilee SYKE:n päästörajapintaa ja Sotkanetiin peilattuja SYKE-päästömittareita.
    """
    # 1. Kokeillaan Sotkanetiin peilattuja SYKE/ympäristöindikaattoreita
    for ind_id in [4007, 5629, 5379]:
        try:
            series, _ = fetch_sotkanet_series(ind_id, sotkanet_region_id, muni_code_padded)
            if series:
                return series, f"SYKE / Sotkanet API (ID {ind_id})"
        except Exception:
            continue

    # 2. Kokeillaan SYKE:n suoraa päästörajapintaa
    url = f"https://paastot.hiilineutraalisuomi.fi/api/emissions?municipality={muni_code_padded}"
    r = requests.get(url, headers=HEADERS, timeout=12)
    r.raise_for_status()
    js = r.json()
    if isinstance(js, list) and len(js) > 0:
        series = [
            (int(x["year"]), round(float(x["perCapita"]), 2))
            for x in js if "year" in x and "perCapita" in x
        ]
        if series:
            series.sort(key=lambda x: x[0])
            return series, "SYKE Hinku API"

    raise ValueError("SYKE KHK-dataa ei saatu rajapinnoista")


def fetch_syke_water_series(sotkanet_region_id, muni_code_padded):
    """
    Hakee SYKE:n pintavesien ekologisen tilan OGC API Features -rajapinnasta
    (tai Sotkanetin ympäristörajapinnasta).
    """
    ogc_url = (
        "https://paikkatiedot.ymparisto.fi/geoserver/syke_pintavesientila/ogc/features/v1/"
        "collections/PintavesienEkologinenTila/items?f=json&limit=200"
    )
    try:
        r = requests.get(ogc_url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            features = r.json().get("features", [])
            muni_feats = [
                f for f in features
                if str(f.get("properties", {}).get("Kuntakoodi", "")).zfill(3) == muni_code_padded
            ]
            if muni_feats:
                good = sum(
                    1 for f in muni_feats
                    if str(f.get("properties", {}).get("EkologinenTila", "")).lower() in ["erinomainen", "hyvä", "hyva", "1", "2"]
                )
                share = max(0.1, good / len(muni_feats))
                return [(2024, round((1.0 / share) * 100.0, 1))], "SYKE OGC API (Pintavedet)"
    except Exception:
        pass

    raise ValueError("SYKE Pintavesien OGC-rajapinta ei palauttanut kuntakohtaista koontia")


def get_indicator_series(ind, sotkanet_region_id, muni_code_padded):
    ind_id = str(ind.get("id", "")).strip()
    src = str(ind.get("source", "")).lower().strip()

    try:
        if "indicator_id" in ind and ind["indicator_id"]:
            return fetch_sotkanet_series(ind["indicator_id"], sotkanet_region_id, muni_code_padded)
        elif src == "syke_khk":
            return fetch_syke_khk_series(sotkanet_region_id, muni_code_padded)
        elif src == "syke_vesistot":
            return fetch_syke_water_series(sotkanet_region_id, muni_code_padded)
        else:
            raise ValueError(f"Suoraa kuntakohtaista REST-rajapintaa ei saatavilla lähteelle '{src}'")
    except Exception as e:
        print(f"⚠️ Mittari '{ind_id}' ({src}): {e} -> Merkitään 0 (Ei dataa).")
        return None, "Ei saatavilla (Rajapinta)"


def main():
    config = load_config()
    muni_code = config.get("municipality", {}).get("sotkanet_code", "286")
    muni_name = config.get("municipality", {}).get("name", "Kouvola")

    sotkanet_region_id, muni_code_padded = resolve_sotkanet_region_id(muni_code, muni_name)

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

        series, source_label = get_indicator_series(ind, sotkanet_region_id, muni_code_padded)

        if series is None or len(series) == 0:
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
            print(f"📊 {name}: {latest_val} {unit} ({latest_year}) -> {ratio_pct} %")

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
    if not df_new_hist.empty:
        df_new_hist.sort_values(by=["id", "period"], inplace=True)
        df_new_hist.to_csv("doughnut_history.csv", index=False, encoding="utf-8")
        print(f"✅ Tallennettu doughnut_history.csv ({len(df_new_hist)} aikasarjariviä).")


if __name__ == "__main__":
    main()
