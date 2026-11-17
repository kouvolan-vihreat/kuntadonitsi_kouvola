# -*- coding: utf-8 -*-
"""
Avoin Kuntadonitsi – Automaattinen tiedonhaku
Lähteet: THL Sotkanet REST API, SYKE / Sotkanet (ID 4007), Tilastokeskus StatFin PxWeb,
         JYU Lipas REST API & manual_indicators.csv (CSV-tunnisteella)
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
        print(f"⚠️ Huomio: manual_indicators.csv luku epäonnistui ({e}).")
        return {}


def format_csv_source(raw_source):
    """Lisää '(CSV)'-tunnisteen lähteen nimeen, kun arvo luetaan manual_indicators.csv-tiedostosta."""
    s = str(raw_source or "SYKE").strip()
    return s if "csv" in s.lower() else f"{s} (CSV)"


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


# ==============================================================================
# 1. THL SOTKANET REST API (Kuntatunnistus ja aikasarjahaku)
# ==============================================================================
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
                    print(f"✅ Kunta tunnistettu: {muni_name} (koodi {code_padded} -> Sotkanet ID {reg_id})")
                    return reg_id, code_padded
    except Exception as e:
        print(f"⚠️ Sotkanet regions -haku epäonnistui: {e}")

    return code_clean, code_padded


def fetch_sotkanet_series(indicator_id, sotkanet_region_id, muni_code_padded, start_year=2018):
    current_year = datetime.now().year
    years = list(range(start_year, current_year + 1))
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
        raise ValueError(f"Sotkanet ID {indicator_id}: ei dataa kunnalle {muni_code_padded}")

    muni_rows.sort(key=lambda x: int(x["year"]))
    series = [(int(r["year"]), round(float(r["value"]), 2)) for r in muni_rows]
    return series, f"SOTKANET API (ID {indicator_id})"


# ==============================================================================
# 2. TILASTOKESKUS STATFIN PXWEB (Tukee sekä json- että json-stat2-vastauksia)
# ==============================================================================
def fetch_statfin_urban_degree(muni_code_padded, muni_name):
    """Hakee Tilastokeskuksen StatFin-rajapinnasta kunnan taajama-asteen (%)."""
    url = "https://pxdata.stat.fi/PxWeb/api/v1/fi/StatFin/vaerak/statfin_vaerak_pxt_11ra.px"
    meta_r = requests.get(url, headers=HEADERS, timeout=15)
    meta_r.raise_for_status()
    meta = meta_r.json()

    query_items = []
    selected_years = []
    name_low = muni_name.strip().lower()
    muni_clean = str(int(muni_code_padded))

    for var in meta.get("variables", []):
        code = str(var.get("code", ""))
        code_low = code.lower()
        vals = [str(v) for v in var.get("values", [])]
        texts = [str(t).lower() for t in var.get("valueTexts", [])]

        if "alue" in code_low or "kunta" in code_low:
            match_v = None
            for v, t in zip(vals, texts):
                if v in [f"KU{muni_code_padded}", muni_code_padded, muni_clean] or t.strip() == name_low or t.strip().startswith(name_low + " "):
                    match_v = v
                    break
            if not match_v:
                raise ValueError(f"Kuntaa {muni_name} ei löytynyt StatFin 11ra -taulusta")
            query_items.append({"code": code, "selection": {"filter": "item", "values": [match_v]}})
        elif "tiedot" in code_low:
            chosen = next((v for v, t in zip(vals, texts) if "taajama-aste" in t or "taajama_aste" in v.lower()), None)
            if not chosen:
                raise ValueError("Taajama-astetta ei löytynyt StatFin 11ra -taulusta")
            query_items.append({"code": code, "selection": {"filter": "item", "values": [chosen]}})
        elif "vuosi" in code_low:
            selected_years = vals[-8:] if len(vals) > 8 else vals
            query_items.append({"code": code, "selection": {"filter": "item", "values": selected_years}})
        else:
            query_items.append({"code": code, "selection": {"filter": "item", "values": [vals[0]]}})

    post_r = requests.post(
        url,
        json={"query": query_items, "response": {"format": "json-stat2"}},
        headers=HEADERS,
        timeout=15
    )
    post_r.raise_for_status()
    res_json = post_r.json()

    series = []
    # 1. Luetaan json-stat2 'value'-taulukko
    if "value" in res_json and isinstance(res_json["value"], list):
        raw_vals = res_json["value"]
        yr_list = [int(str(y)[:4]) for y in selected_years if str(y)[:4].isdigit()]
        for yr, v in zip(yr_list, raw_vals):
            if v is not None and 5.0 <= float(v) <= 100.0:
                series.append((yr, round(float(v), 2)))

    # 2. Varalla vanha 'data'-taulukko
    if not series and "data" in res_json:
        for row in res_json.get("data", []):
            keys = row.get("key", [])
            r_vals = row.get("values", [])
            yr = next((int(str(k)[:4]) for k in keys if str(k)[:4].isdigit() and 2000 <= int(str(k)[:4]) <= 2035 and str(k) != muni_code_padded), None)
            if yr and r_vals and r_vals[0] not in [".", "..", "-", None, ""]:
                v = float(r_vals[0])
                if 5.0 <= v <= 100.0:
                    series.append((yr, round(v, 2)))

    if not series:
        raise ValueError("StatFin ei palauttanut taajama-astetta")

    series.sort(key=lambda x: x[0])
    return series


# ==============================================================================
# 3. ULKOKEHÄN MITTARI 1: ALUEELLISET KHK-PÄÄSTÖT (SYKE / SOTKANET API)
# ==============================================================================
def fetch_syke_khk_series(ind, sotkanet_region_id, muni_code_padded):
    """
    Toteuttaa ulkokehän mittarin 1 (Alueelliset KHK-päästöt, t CO2e/as.):
      A) Hakee ensisijaisesti THL Sotkanetiin peilatun SYKE:n virallisen KHK-mittarin
         (ID 4007 tai config.yaml:ssa annettu indicator_id, varalla ID 5379).
      B) Jos Sotkanet-indikaattori on annettu kokonaispäästöinä (1000 t CO2e),
         suhteuttaa sen automaattisesti kunnan väkilukuun (Sotkanet ID 127).
    """
    primary_id = ind.get("indicator_id", 4007)
    candidate_ids = []
    for cid in [primary_id, 4007, 5379]:
        if cid and cid not in candidate_ids:
            candidate_ids.append(cid)

    for cid in candidate_ids:
        try:
            raw_series, _ = fetch_sotkanet_series(cid, sotkanet_region_id, muni_code_padded, start_year=2015)
            if not raw_series:
                continue

            latest_val = raw_series[-1][1]
            # Jos arvo on suoraan t CO2e / asukas (tyypillisesti Suomessa 1.5 .. 25.0 t CO2e/as.)
            if 0.5 <= latest_val <= 35.0:
                return raw_series, f"SYKE / Sotkanet API (ID {cid})"

            # Jos arvo on 1000 t CO2e yhteensä (esim. > 50), jaetaan kunnan asukasluvulla (ID 127)
            if latest_val > 35.0:
                pop_series, _ = fetch_sotkanet_series(127, sotkanet_region_id, muni_code_padded, start_year=2015)
                pop_by_year = dict(pop_series)
                per_capita_series = []
                for yr, val in raw_series:
                    pop = pop_by_year.get(yr) or (pop_series[-1][1] if pop_series else None)
                    if pop and pop > 0:
                        # Jos yksikkö on kt CO2e (1000 t), kerrotaan 1000:lla ja jaetaan asukasluvulla
                        per_cap = (val * 1000.0) / pop if val < 10000 else val / pop
                        if 0.5 <= per_cap <= 35.0:
                            per_capita_series.append((yr, round(per_cap, 2)))
                if per_capita_series:
                    return per_capita_series, f"SYKE / Sotkanet API (ID {cid})"
        except Exception as e:
            print(f"ℹ️ KHK Sotkanet ID {cid} ei palauttanut suoraa sarjaa: {e}")

    # Varalla SYKE OData
    odata_url = f"https://avoindata.syke.fi/odata/KHKPaastot?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    r = requests.get(odata_url, headers=HEADERS, timeout=8)
    if r.status_code == 200:
        items = r.json().get("value", [])
        series = [
            (int(x["Vuosi"]), round(float(x["PaastotPerAsukas"]), 2))
            for x in items if "Vuosi" in x and "PaastotPerAsukas" in x and x["PaastotPerAsukas"] is not None
        ]
        if series:
            series.sort(key=lambda x: x[0])
            return series, "SYKE Hinku API"

    raise RuntimeError("SYKE KHK-rajapinta ei vastannut -> käytetään CSV-varatietoa")


# ==============================================================================
# 4. ULKOKEHÄN MITTARI 2: MAANKÄYTTÖPAINE VS. LÄHILUONTO (KOMPOSIITTI-INDEKSI)
# ==============================================================================
def fetch_landuse_pressure_series(sotkanet_region_id, muni_code_padded, muni_name):
    """
    Approksimoi 'Maankäyttöpaine vs. lähiluonto' -mittarin (100 % = 1.0x kestävä raja)
    yhdistämällä useita avoimista rajapinnoista haettavia osa-indikaattoreita:

      1. S_taajama (paino 0.40): Taajama-aste (%) [Sotkanet ID 195 tai StatFin 11ra].
         Korkea rakennetun taajaman osuus kasvattaa maankäyttöpainetta:
         S_taajama = (Taajama_aste / 80.0) * 100.0
      2. S_rakenne (paino 0.25): Yhdyskuntarakenteen hajautuminen / liikkuminen
         [Sotkanet ID 3218 (joukkoliikennevyöhyke) tai ID 184 (väestöntiheys)].
      3. S_ilma (paino 0.20): Elinympäristön pienhiukkas-/liikennepaine
         [Sotkanet ID 3560 (PM2.5 altistus suhteessa WHO:n 5.5 ug/m3 viitearvoon)].
      4. S_virkistys (paino 0.15): Lähiluonnon ja virkistyskohteiden saavutettavuuspaine
         [JYU Lipas REST API: luontopolut ja virkistysalueet kunnassa].

    Palauttaa painotetun vuosiaikasarjan sekä tarkan kuvauksen käytetyistä rajapinnoista.
    """
    yearly_components = {}  # { vuosi: [(normeerattu_arvo, paino), ...] }
    used_sources = []

    def add_component(yr, score, weight):
        score_clamped = max(25.0, min(220.0, float(score)))
        yearly_components.setdefault(int(yr), []).append((score_clamped, float(weight)))

    # --- OSA 1: Taajama-aste (%) [Sotkanet ID 195 tai Tilastokeskus StatFin] (Paino 0.40) ---
    taajama_ok = False
    try:
        s_195, _ = fetch_sotkanet_series(195, sotkanet_region_id, muni_code_padded, start_year=2018)
        if s_195:
            for yr, val in s_195:
                # 80 % taajama-aste vastaa 100 % viitekuormitusta
                add_component(yr, (val / 80.0) * 100.0, 0.40)
            used_sources.append("Sotkanet ID 195")
            taajama_ok = True
    except Exception:
        pass

    if not taajama_ok:
        try:
            s_sf = fetch_statfin_urban_degree(muni_code_padded, muni_name)
            if s_sf:
                for yr, val in s_sf:
                    add_component(yr, (val / 80.0) * 100.0, 0.40)
                used_sources.append("StatFin 11ra")
                taajama_ok = True
        except Exception as e:
            print(f"ℹ️ Osamittari Taajama-aste ei vastannut: {e}")

    # --- OSA 2: Yhdyskuntarakenteen hajautuminen / tiheys [Sotkanet ID 3218 tai ID 184] (Paino 0.25) ---
    rakenne_ok = False
    try:
        # ID 3218: Kestävän liikkumisen / joukkoliikenteen vyöhykkeellä asuvat (%)
        s_3218, _ = fetch_sotkanet_series(3218, sotkanet_region_id, muni_code_padded, start_year=2018)
        if s_3218:
            for yr, val in s_3218:
                # Mitä pienempi osuus asuu vyöhykkeellä, sitä suurempi hajarakentamisen ja autoilun maankäyttöpaine
                sprawl_score = 60.0 + max(0.0, (100.0 - float(val))) * 0.55
                add_component(yr, sprawl_score, 0.25)
            used_sources.append("SYKE/Sotkanet ID 3218")
            rakenne_ok = True
    except Exception:
        pass

    if not rakenne_ok:
        try:
            # ID 184: Väestöntiheys (asukasta / maapinta-alan km2)
            s_184, _ = fetch_sotkanet_series(184, sotkanet_region_id, muni_code_padded, start_year=2018)
            if s_184:
                for yr, dens in s_184:
                    # Kohtuullinen tiheys + suuri luontoala pitää paineen hallinnassa (normeerattu 65..135 %)
                    dens_score = 72.0 + min(65.0, (float(dens) / 150.0) * 35.0)
                    add_component(yr, dens_score, 0.25)
                used_sources.append("Sotkanet ID 184")
        except Exception:
            pass

    # --- OSA 3: Lähiympäristön pienhiukkas- ja päästökuormitus [Sotkanet ID 3560] (Paino 0.20) ---
    try:
        s_3560, _ = fetch_sotkanet_series(3560, sotkanet_region_id, muni_code_padded, start_year=2018)
        if s_3560:
            for yr, val in s_3560:
                v = float(val)
                # Jos arvo on ug/m3 (tyypillisesti 3..10), suhteutetaan 5.5 ug/m3 kestävyysrajaan
                air_score = (v / 5.5) * 100.0 if v <= 25.0 else v
                add_component(yr, air_score, 0.20)
            used_sources.append("SYKE/THL ID 3560")
    except Exception:
        pass

    # --- OSA 4: Lähiluonnon ja virkistyskohteiden saavutettavuus [JYU Lipas REST API] (Paino 0.15) ---
    lipas_score = None
    try:
        muni_int = int(muni_code_padded)
        lipas_url = f"https://lipas.fi/api/sports-sites?cityCodes={muni_int}&pageSize=100"
        r_lipas = requests.get(lipas_url, headers=HEADERS, timeout=10)
        if r_lipas.status_code == 200:
            sites = r_lipas.json()
            if isinstance(sites, list) and len(sites) >= 5:
                count = len(sites)
                # Runsas virkistys- ja luontokohdeverkosto (esim. >= 85 kohdetta) alentaa lähiluontopainetta (< 90 %)
                lipas_score = max(55.0, min(130.0, (75.0 / max(30, count)) * 100.0))
                used_sources.append("Lipas API")
    except Exception:
        pass

    if lipas_score is not None:
        target_years = list(yearly_components.keys()) if yearly_components else [datetime.now().year - 1]
        for yr in target_years:
            add_component(yr, lipas_score, 0.15)

    if not yearly_components:
        raise RuntimeError("Maankäyttöpaineen osarajapinnat eivät vastanneet -> käytetään CSV-varatietoa")

    # Lasketaan painotettu yhdistelmäindeksi jokaiselle vuodelle
    composite_series = []
    for yr in sorted(yearly_components.keys()):
        items = yearly_components[yr]
        total_w = sum(w for _, w in items)
        if total_w > 0:
            weighted_avg = sum(score * w for score, w in items) / total_w
            composite_series.append((yr, round(weighted_avg, 1)))

    source_summary = "Yhdistelmä-API (" + " + ".join(used_sources[:3]) + ")"
    return composite_series, source_summary


# ==============================================================================
# 5. MUUT ULKOKEHÄN MITTARIT (Kulutuspäästöt & Vesistöt)
# ==============================================================================
def fetch_syke_consumption_series(muni_code_padded):
    odata_url = f"https://avoindata.syke.fi/odata/KulutusPaastot?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    r = requests.get(odata_url, headers=HEADERS, timeout=8)
    if r.status_code == 200:
        items = r.json().get("value", [])
        series = [
            (int(x["Vuosi"]), round(float(x["PaastotPerAsukas"]), 2))
            for x in items if "Vuosi" in x and "PaastotPerAsukas" in x and x["PaastotPerAsukas"] is not None
        ]
        if series:
            series.sort(key=lambda x: x[0])
            return series, "SYKE Kulutus API"
    raise RuntimeError("SYKE Kulutus-rajapinta ei vastannut -> käytetään CSV-varatietoa")


def fetch_water_load_series(muni_code_padded):
    odata_url = f"https://avoindata.syke.fi/odata/PintavesienTila?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    r = requests.get(odata_url, headers=HEADERS, timeout=8)
    if r.status_code == 200:
        items = r.json().get("value", [])
        if items:
            good_or_high = sum(
                1 for x in items
                if str(x.get("EkologinenTila", "")).lower() in ["erinomainen", "hyvä", "hyva", "1", "2"]
            )
            good_share = max(0.25, good_or_high / len(items))
            load_index = round((1.0 / good_share) * 100.0, 1)
            if 20.0 <= load_index <= 300.0:
                yr = max(int(x.get("Vuosi", 2024)) for x in items)
                return [(yr, load_index)], "SYKE Pintavedet API"
    raise RuntimeError("Vesistö-API ei palauttanut kuntalukua -> käytetään CSV-varatietoa")


# ==============================================================================
# 6. REITITYS JA VARAJÄRJESTELMÄ (manual_indicators.csv)
# ==============================================================================
def get_indicator_series(ind, sotkanet_region_id, muni_code_padded, muni_name, fallbacks):
    ind_id = str(ind.get("id", "")).strip()
    src = str(ind.get("source", "")).lower().strip()

    try:
        if src == "sotkanet" and "indicator_id" in ind:
            return fetch_sotkanet_series(ind["indicator_id"], sotkanet_region_id, muni_code_padded)
        elif src == "syke_khk":
            return fetch_syke_khk_series(ind, sotkanet_region_id, muni_code_padded)
        elif src == "syke_maankaytto":
            return fetch_landuse_pressure_series(sotkanet_region_id, muni_code_padded, muni_name)
        elif src == "syke_kulutus":
            return fetch_syke_consumption_series(muni_code_padded)
        elif src == "syke_vesistot":
            return fetch_water_load_series(muni_code_padded)
        elif "indicator_id" in ind and ind["indicator_id"]:
            return fetch_sotkanet_series(ind["indicator_id"], sotkanet_region_id, muni_code_padded)
    except Exception as e:
        print(f"ℹ️ {ind_id}: {e}")

    # Varajärjestelmä (manual_indicators.csv): merkitään selkeästi '(CSV)'-tunnisteella
    if ind_id in fallbacks:
        fb = fallbacks[ind_id]
        yr = int(float(fb.get("year", 2024)))
        val = round(float(fb.get("value", 0.0)), 2)
        src_label = format_csv_source(fb.get("source", "SYKE"))
        return [(yr, val)], src_label

    return None, "Ei saatavilla"


def main():
    config = load_config()
    muni_code = config.get("municipality", {}).get("sotkanet_code", "286")
    muni_name = config.get("municipality", {}).get("name", "Kouvola")
    fallbacks = load_manual_fallbacks()

    sotkanet_region_id, muni_code_padded = resolve_sotkanet_region_id(muni_code, muni_name)

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

        series, source_label = get_indicator_series(
            ind, sotkanet_region_id, muni_code_padded, muni_name, fallbacks
        )

        if not series:
            continue

        latest_year, latest_val = series[-1]
        ratio_pct, is_safe = evaluate_status(latest_val, threshold, direction)
        print(f"📊 {name}: {latest_val} {unit} ({latest_year}) [{source_label}] -> {ratio_pct} %")

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

    # Mahdolliset lisärivit suoraan manual_indicators.csv-tiedostosta saavat myös (CSV)-tunnisteen
    for fb_id, fb in fallbacks.items():
        if fb_id not in processed_ids:
            val = round(float(fb["value"]), 2)
            thresh = float(fb["threshold"])
            direction = str(fb.get("direction", "lower_is_better")).strip()
            yr = int(float(fb.get("year", 2024)))
            ratio_pct, is_safe = evaluate_status(val, thresh, direction)
            src_label = format_csv_source(fb.get("source", "SYKE"))

            results_rows.append({
                "id": fb_id,
                "name": fb["name"],
                "domain": fb["domain"],
                "source": src_label,
                "value": val,
                "threshold": thresh,
                "unit": fb["unit"],
                "direction": direction,
                "year": yr,
                "ratio_pct": ratio_pct,
                "is_safe": is_safe,
                "updated_at": updated_at_str
            })

    df_results = pd.DataFrame(results_rows)
    df_results.to_csv("doughnut_results.csv", index=False, encoding="utf-8")
    print(f"✅ Tallennettu doughnut_results.csv ({len(df_results)} mittaria).")

    df_new_hist = pd.DataFrame(history_rows)
    if os.path.exists("doughnut_history.csv") and not df_new_hist.empty:
        try:
            df_old_hist = pd.read_csv("doughnut_history.csv", encoding="utf-8")
            df_old_hist = df_old_hist[(df_old_hist["ratio_pct"] >= 10.0) & (df_old_hist["ratio_pct"] <= 1000.0)]
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
