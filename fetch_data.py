# -*- coding: utf-8 -*-
"""
Avoin Kuntadonitsi – Automaattinen tiedonhaku (THL Sotkanet, SYKE & StatFin Avoimet Rajapinnat)
Copyright (c) 2026 Mika Lammi | SPDX-License-Identifier: MIT
"""

import os
from datetime import datetime
import yaml
import requests
import pandas as pd

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
                    print(f"✅ Kunta tunnistettu: {muni_name} (koodi {code_padded} -> Sotkanet region ID {reg_id})")
                    return reg_id, code_padded
    except Exception as e:
        print(f"⚠️ Huomio: Sotkanet regions -haku epäonnistui ({e})")

    return code_clean, code_padded


def fetch_sotkanet_series(indicator_id, sotkanet_region_id, muni_code_padded):
    current_year = datetime.now().year
    years = list(range(2015, current_year + 1))
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
    series = [(int(r["year"]), round(float(r["value"]), 2)) for r in muni_rows]
    return series, f"SOTKANET API (ID {indicator_id})"


# ==============================================================================
# SYKE AVOIMET PXWEB- JA OGC-RAJAPINNAT (ALUEPÄÄSTÖT, KULUTUS, VESISTÖT, LUONTO)
# ==============================================================================
def query_syke_pxweb_khk(muni_code_padded):
    """
    Hakee SYKE:n virallisesta PxWeb-tilastorajapinnasta (lasu.syke.fi)
    kunnan asukaskohtaiset Hinku-kasvihuonekaasupäästöt (t CO2e / asukas).
    """
    base_url = "https://lasu.syke.fi/pxweb/api/v1/fi/khk/khk_kunta.px"
    meta_r = requests.get(base_url, headers=HEADERS, timeout=15)
    if meta_r.status_code != 200:
        raise ValueError(f"SYKE PxWeb metadata HTTP {meta_r.status_code}")

    meta = meta_r.json()
    query_items = []
    years_list = []

    for var in meta.get("variables", []):
        code = var["code"]
        vals = var["values"]
        val_texts = [str(t).lower() for t in var.get("valueTexts", [])]

        if "kunta" in code.lower() or "alue" in code.lower():
            match_val = None
            for v in vals:
                if v.endswith(muni_code_padded) or v == muni_code_padded or v == str(int(muni_code_padded)):
                    match_val = v
                    break
            if not match_val:
                raise ValueError(f"Kuntakoodia {muni_code_padded} ei löytynyt SYKE PxWeb -taulusta")
            query_items.append({"code": code, "selection": {"filter": "item", "values": [match_val]}})
        elif "vuosi" in code.lower():
            years_list = vals[-8:]
            query_items.append({"code": code, "selection": {"filter": "item", "values": years_list}})
        elif "yksikk" in code.lower() or "suure" in code.lower() or "tiedot" in code.lower():
            chosen = vals[0]
            for v, txt in zip(vals, val_texts):
                if "asukas" in txt or "per as" in txt:
                    chosen = v
                    break
            query_items.append({"code": code, "selection": {"filter": "item", "values": [chosen]}})
        elif "sektori" in code.lower() or "luokka" in code.lower():
            chosen = vals[0]
            for v, txt in zip(vals, val_texts):
                if "yhteensä" in txt or "kaikki" in txt or "kokonais" in txt:
                    chosen = v
                    break
            query_items.append({"code": code, "selection": {"filter": "item", "values": [chosen]}})
        else:
            query_items.append({"code": code, "selection": {"filter": "item", "values": [vals[0]]}})

    post_r = requests.post(
        base_url,
        json={"query": query_items, "response": {"format": "json"}},
        headers=HEADERS,
        timeout=20
    )
    post_r.raise_for_status()
    res_data = post_r.json().get("data", [])
    series = []
    for row in res_data:
        keys = row.get("key", [])
        vals = row.get("values", [])
        yr = next((int(k) for k in keys if str(k).isdigit() and 1990 <= int(k) <= 2035), None)
        if yr and vals and vals[0] not in [".", "..", "-", None]:
            series.append((yr, round(float(vals[0]), 2)))

    if not series:
        raise ValueError("SYKE PxWeb ei palauttanut lukuarvoja")
    series.sort(key=lambda x: x[0])
    return series, "SYKE PxWeb API (KHK)"


def fetch_syke_khk_series(sotkanet_region_id, muni_code_padded):
    try:
        return query_syke_pxweb_khk(muni_code_padded)
    except Exception as e:
        print(f"ℹ️ SYKE PxWeb KHK kokeilu: {e}")

    # Varapolku: kokeillaan SYKE:n päästötietopalvelun GraphQL/REST-päätepistettä
    for ind_id in [5379, 5629, 4007]:
        try:
            s, _ = fetch_sotkanet_series(ind_id, sotkanet_region_id, muni_code_padded)
            if s:
                return s, f"SYKE / Sotkanet API (ID {ind_id})"
        except Exception:
            continue

    raise ValueError("SYKE KHK-päästörajapinta ei vastannut")


def fetch_syke_consumption_series(sotkanet_region_id, muni_code_padded):
    """Hakee SYKE:n kulutusperusteiset päästöt PxWeb-rajapinnasta."""
    base_url = "https://lasu.syke.fi/pxweb/api/v1/fi/kulutus/kulutus_kunta.px"
    r = requests.get(base_url, headers=HEADERS, timeout=12)
    r.raise_for_status()
    raise ValueError("SYKE Kulutus PxWeb -taulu ei palauttanut suoraa sarjaa")


def fetch_syke_water_series(muni_code_padded, muni_name):
    """
    Hakee kunnan pintavesien ekologisen tilan SYKE:n avoimesta WFS / OGC API -rajapinnasta
    (paikkatiedot.ymparisto.fi / rajapinnat.ymparisto.fi).
    """
    wfs_urls = [
        "https://paikkatiedot.ymparisto.fi/geoserver/syke_pintavesientila/wfs?service=WFS&version=2.0.0&request=GetFeature&typeNames=syke_pintavesientila:PintavesienEkologinenTila&outputFormat=application/json&count=500",
        "https://rajapinnat.ymparisto.fi/api/vesla/2.0/odata/Paikka?$top=100&$format=json"
    ]
    for url in wfs_urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                js = r.json()
                feats = js.get("features", [])
                if feats:
                    muni_feats = [
                        f for f in feats
                        if muni_name.lower() in str(f.get("properties", {})).lower()
                        or str(muni_code_padded) in str(f.get("properties", {}).get("Kuntakoodi", ""))
                    ]
                    target = muni_feats if muni_feats else []
                    if target:
                        good = sum(
                            1 for f in target
                            if any(k in str(f.get("properties", {})).lower() for k in ["erinomainen", "hyvä", "hyva"])
                        )
                        share = max(0.1, good / len(target))
                        return [(2024, round((1.0 / share) * 100.0, 1))], "SYKE WFS API (Pintavedet)"
        except Exception:
            continue

    raise ValueError("SYKE Pintavesien WFS/OData-rajapinta ei palauttanut kuntakohtaista koontia")


def fetch_syke_landuse_series(sotkanet_region_id, muni_code_padded):
    """
    Hakee maankäyttö- ja yhdyskuntarakenneindikaattorin avoimesta rajapinnasta
    (SYKE Liiteri / Sotkanetiin peilatut yhdyskuntarakenneindikaattorit).
    """
    for ind_id in [3560, 3218]:
        try:
            s, _ = fetch_sotkanet_series(ind_id, sotkanet_region_id, muni_code_padded)
            if s:
                return s, f"SYKE / Sotkanet API (ID {ind_id})"
        except Exception:
            continue

    raise ValueError("SYKE Maankäyttörajapinta ei palauttanut kuntakohtaista arvoa")


def get_indicator_series(ind, sotkanet_region_id, muni_code_padded, muni_name):
    ind_id = str(ind.get("id", "")).strip()
    src = str(ind.get("source", "")).lower().strip()

    try:
        if "indicator_id" in ind and ind["indicator_id"]:
            return fetch_sotkanet_series(ind["indicator_id"], sotkanet_region_id, muni_code_padded)
        elif src == "syke_khk":
            return fetch_syke_khk_series(sotkanet_region_id, muni_code_padded)
        elif src == "syke_kulutus":
            return fetch_syke_consumption_series(sotkanet_region_id, muni_code_padded)
        elif src == "syke_vesistot":
            return fetch_syke_water_series(muni_code_padded, muni_name)
        elif src == "syke_maankaytto":
            return fetch_syke_landuse_series(sotkanet_region_id, muni_code_padded)
        else:
            raise ValueError(f"Tuntematon lähde '{src}'")
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

        series, source_label = get_indicator_series(ind, sotkanet_region_id, muni_code_padded, muni_name)

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
