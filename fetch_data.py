# -*- coding: utf-8 -*-
"""
Avoin Kuntadonitsi – Automaattinen tiedonhaku
Lähteet: THL Sotkanet REST API, SYKE / Sotkanet, Tilastokeskus StatFin PxWeb,
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
            chosen = next((v for v, t in zip(vals, texts) if "taajama" in t or "taajama" in v.lower()), None)
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
        json={"query": query_items, "response": {"format": "json"}},
        headers=HEADERS,
        timeout=15
    )
    post_r.raise_for_status()
    res_json = post_r.json()

    series = []
    for row in res_json.get("data", []):
        keys = row.get("key", [])
        r_vals = row.get("values", [])
        yr = next((int(str(k)[:4]) for k in keys if str(k)[:4].isdigit() and 2000 <= int(str(k)[:4]) <= 2035 and str(k) != muni_code_padded), None)
        if yr and r_vals and r_vals[0] not in [".", "..", "...", "-", None, ""]:
            v = float(r_vals[0])
            if 5.0 <= v <= 100.0:
                series.append((yr, round(v, 2)))

    if not series:
        raise ValueError("StatFin ei palauttanut taajama-astetta")

    series.sort(key=lambda x: x[0])
    return series


# ==============================================================================
# ULKOKEHÄN MITTARI 1: ALUEELLISET KHK-PÄÄSTÖT (SYKE / SOTKANET API)
# ==============================================================================
def fetch_syke_khk_series(ind, sotkanet_region_id, muni_code_padded):
    """
    Hakee kuntakohtaiset kasvihuonekaasupäästöt (t CO2e/as.) kokeilemalla:
      1. Sotkanetin SYKE-ilmastomittareita (mm. 4007, 5379, 5380, 3364, 5091).
         Jos arvo on kt CO2e tai t CO2e yhteensä, jakaa sen kunnan väkiluvulla (ID 74 / 127).
      2. SYKE:n avointa rajapintaa.
    """
    primary_id = ind.get("indicator_id", 4007)
    candidate_ids = []
    for cid in [primary_id, 5379, 5380, 4007, 3364, 5091]:
        if cid and cid not in candidate_ids:
            candidate_ids.append(cid)

    # Haetaan tarvittaessa kunnan väkiluku (ID 74 = Väkiluku 31.12.) muunnosta varten
    pop_by_year = {}
    for pop_id in [74, 127]:
        try:
            pop_s, _ = fetch_sotkanet_series(pop_id, sotkanet_region_id, muni_code_padded, start_year=2018)
            if pop_s and pop_s[-1][1] > 500:
                pop_by_year = dict(pop_s)
                break
        except Exception:
            continue

    for cid in candidate_ids:
        try:
            raw_series, _ = fetch_sotkanet_series(cid, sotkanet_region_id, muni_code_padded, start_year=2018)
            if not raw_series:
                continue

            latest_val = float(raw_series[-1][1])
            print(f"🔎 KHK-ehdokas Sotkanet ID {cid}: viimeisin arvo = {latest_val}")

            # Tapaus A: Arvo on suoraan t CO2e / asukas (esim. 2.0 .. 25.0)
            if 0.8 <= latest_val <= 30.0:
                return raw_series, f"SYKE / Sotkanet API (ID {cid})"

            # Tapaus B: Arvo on kg CO2e / asukas (esim. 3500 .. 18000 kg) -> muunnetaan tonneiksi (/ 1000)
            if 1000.0 <= latest_val <= 25000.0 and not pop_by_year:
                conv = [(yr, round(v / 1000.0, 2)) for yr, v in raw_series]
                return conv, f"SYKE / Sotkanet API (ID {cid})"

            # Tapaus C: Arvo on kunnan kokonaispäästö (1000 t CO2e tai t CO2e) -> jaetaan väkiluvulla
            if pop_by_year and latest_val > 30.0:
                latest_pop = list(pop_by_year.values())[-1]
                per_capita_series = []
                for yr, v in raw_series:
                    pop = pop_by_year.get(yr, latest_pop)
                    if pop > 0:
                        # Jos kt CO2e (esim. Kouvola ~400 kt), kerrotaan 1000:lla; jos t CO2e (esim. 400 000 t), jaetaan suoraan
                        per_cap = (v * 1000.0) / pop if v < 50000 else v / pop
                        if 0.8 <= per_cap <= 30.0:
                            per_capita_series.append((yr, round(per_cap, 2)))
                if per_capita_series:
                    return per_capita_series, f"SYKE / Sotkanet API (ID {cid})"
        except Exception as e:
            print(f"ℹ️ KHK Sotkanet ID {cid} ohitettiin: {e}")

    raise RuntimeError("SYKE KHK-rajapinta ei vastannut -> käytetään CSV-varatietoa")


# ==============================================================================
# ULKOKEHÄN MITTARI 2: MAANKÄYTTÖPAINE VS. LÄHILUONTO (KOMPOSIITTI-INDEKSI)
# ==============================================================================
def fetch_landuse_pressure_series(sotkanet_region_id, muni_code_padded, muni_name):
    """
    Approksimoi 'Maankäyttöpaine vs. lähiluonto' -mittarin (100 % = 1.0x kestävä raja)
    yhdistämällä avoimista rajapinnoista haettavat osa-indikaattorit:
      1. Taajama-aste (%) [Sotkanet ID 676 tai StatFin 11ra] (paino 0.40)
      2. Yhdyskuntarakenteen hajautuminen / joukkoliikennevyöhyke [SYKE/Sotkanet ID 3218 tai ID 184] (paino 0.25)
      3. Lähiympäristön pienhiukkaskuormitus [SYKE/THL ID 3560] (paino 0.20)
      4. Lähiluonnon ja virkistysalueiden saavutettavuus [JYU Lipas API] (paino 0.15)
    """
    yearly_components = {}
    used_sources = []

    def add_component(yr, score, weight):
        score_clamped = max(25.0, min(220.0, float(score)))
        yearly_components.setdefault(int(yr), []).append((score_clamped, float(weight)))

    # --- OSA 1: Taajama-aste (%) [Sotkanet ID 676 tai StatFin 11ra] (Paino 0.40) ---
    taajama_ok = False
    for tid in [676, 195]:
        try:
            s_taaj, _ = fetch_sotkanet_series(tid, sotkanet_region_id, muni_code_padded, start_year=2018)
            if s_taaj and 10.0 <= s_taaj[-1][1] <= 100.0:
                for yr, val in s_taaj:
                    add_component(yr, (val / 80.0) * 100.0, 0.40)
                used_sources.append(f"Sotkanet ID {tid}")
                taajama_ok = True
                break
        except Exception:
            continue

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

    # --- OSA 2: Yhdyskuntarakenteen hajautuminen [SYKE/Sotkanet ID 3218 tai ID 184] (Paino 0.25) ---
    rakenne_ok = False
    try:
        s_3218, _ = fetch_sotkanet_series(3218, sotkanet_region_id, muni_code_padded, start_year=2018)
        if s_3218:
            for yr, val in s_3218:
                sprawl_score = 60.0 + max(0.0, (100.0 - float(val))) * 0.55
                add_component(yr, sprawl_score, 0.25)
            used_sources.append("SYKE/Sotkanet ID 3218")
            rakenne_ok = True
    except Exception:
        pass

    if not rakenne_ok:
        try:
            s_184, _ = fetch_sotkanet_series(184, sotkanet_region_id, muni_code_padded, start_year=2018)
            if s_184:
                for yr, dens in s_184:
                    dens_score = 72.0 + min(65.0, (float(dens) / 150.0) * 35.0)
                    add_component(yr, dens_score, 0.25)
                used_sources.append("Sotkanet ID 184")
        except Exception:
            pass

    # --- OSA 3: Lähiympäristön pienhiukkaskuormitus [SYKE/THL ID 3560] (Paino 0.20) ---
    try:
        s_3560, _ = fetch_sotkanet_series(3560, sotkanet_region_id, muni_code_padded, start_year=2018)
        if s_3560:
            for yr, val in s_3560:
                v = float(val)
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

    composite_series = []
    for yr in sorted(yearly_components.keys()):
        items = yearly_components[yr]
        total_w = sum(w for _, w in items)
        if total_w > 0:
            weighted_avg = sum(score * w for score, w in items) / total_w
            composite_series.append((yr, round(weighted_avg, 1)))

    source_summary = "Yhdistelmä-API (" + " + ".join(used_sources) + ")"
    return composite_series, source_summary


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
