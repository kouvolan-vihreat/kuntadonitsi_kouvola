# -*- coding: utf-8 -*-
"""
Avoin Kuntadonitsi – Automaattinen tiedonhaku
Lähteet: THL Sotkanet REST API, Tilastokeskus StatFin PxWeb, SYKE PxWeb/OData,
         Luke PxWeb, JYU Lipas REST API & manual_indicators.csv (CSV-tunnisteella)
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
        raise ValueError(f"Sotkanet ID {indicator_id}: ei dataa kunnalle {muni_code_padded}")

    muni_rows.sort(key=lambda x: int(x["year"]))
    series = [(int(r["year"]), round(float(r["value"]), 2)) for r in muni_rows]
    return series, f"SOTKANET API (ID {indicator_id})"


# ==============================================================================
# 2. YLEISKÄYTTÖINEN PXWEB-HAKUMOOTTORI (Tilastokeskus StatFin, SYKE & Luke)
# ==============================================================================
def query_pxweb_series(table_url, muni_code_padded, muni_name, metric_keywords=None, min_val=0.1, max_val=500.0):
    """
    Hakee aikasarjan mistä tahansa PxWeb-taulusta (StatFin, SYKE, Luke).
    Tunnistaa kunnan joko koodilla ('KU286', '286') tai nimellä ('Kouvola')
    ja varmistaa, että palautetut arvot ovat järkevällä lukualueella (min_val..max_val).
    """
    meta_r = requests.get(table_url, headers=HEADERS, timeout=15)
    if meta_r.status_code != 200:
        raise ValueError(f"PxWeb metadata HTTP {meta_r.status_code}")

    meta = meta_r.json()
    query_items = []
    muni_matched = False
    muni_clean = str(int(muni_code_padded))
    name_low = muni_name.strip().lower()
    year_var_index = None

    variables = meta.get("variables", [])
    for idx, var in enumerate(variables):
        code = str(var.get("code", ""))
        code_low = code.lower()
        vals = [str(v) for v in var.get("values", [])]
        texts = [str(t).lower() for t in var.get("valueTexts", [])]

        # 1. Alue- tai kuntamuuttuja
        if any(k in code_low for k in ["alue", "kunta", "region", "maakunta"]) or any(name_low in t for t in texts):
            match_v = None
            for v, t in zip(vals, texts):
                t_clean = t.strip()
                if (
                    v in [f"KU{muni_code_padded}", muni_code_padded, muni_clean]
                    or v.endswith(muni_code_padded)
                    or t_clean == name_low
                    or t_clean.startswith(name_low + " ")
                    or f" {name_low}" in t_clean
                ):
                    match_v = v
                    break
            if not match_v:
                raise ValueError(f"Aluetta {muni_name} ({muni_code_padded}) ei löytynyt taulusta")
            muni_matched = True
            query_items.append({"code": code, "selection": {"filter": "item", "values": [match_v]}})

        # 2. Vuosimuuttuja
        elif any(k in code_low for k in ["vuosi", "year", "aika"]):
            year_var_index = idx
            selected_years = vals[-8:] if len(vals) > 8 else vals
            query_items.append({"code": code, "selection": {"filter": "item", "values": selected_years}})

        # 3. Tiedot / Muuttuja / Yksikkö
        elif metric_keywords and any(k in code_low for k in ["tiedot", "muuttuja", "suure", "yksikk", "tunnusluku", "indikaattori"]):
            chosen = None
            for kw in metric_keywords:
                kw_low = kw.lower()
                for v, t in zip(vals, texts):
                    if kw_low in t or kw_low in v.lower():
                        chosen = v
                        break
                if chosen:
                    break
            if not chosen:
                chosen = vals[-1]
            query_items.append({"code": code, "selection": {"filter": "item", "values": [chosen]}})

        # 4. Muut ulottuvuudet (esim. sektori = yhteensä)
        else:
            chosen = vals[0]
            for v, t in zip(vals, texts):
                if any(w in t for w in ["yhteensä", "kaikki", "kokonais", "hinku"]):
                    chosen = v
                    break
            query_items.append({"code": code, "selection": {"filter": "item", "values": [chosen]}})

    if not muni_matched:
        raise ValueError("Taulussa ei ollut kuntamuuttujaa")

    post_r = requests.post(
        table_url,
        json={"query": query_items, "response": {"format": "json"}},
        headers=HEADERS,
        timeout=20
    )
    post_r.raise_for_status()
    rows = post_r.json().get("data", [])

    series = []
    for row in rows:
        keys = row.get("key", [])
        r_vals = row.get("values", [])
        if not r_vals or r_vals[0] in [".", "..", "...", "-", None, ""]:
            continue

        # Poimitaan vuosiluku ensisijaisesti vuosimuuttujan indeksistä tai 4-numeroisesta avaimesta
        yr = None
        if year_var_index is not None and year_var_index < len(keys):
            k_str = str(keys[year_var_index])[:4]
            if k_str.isdigit():
                yr = int(k_str)
        if yr is None:
            for k in keys:
                k_str = str(k)[:4]
                if k_str.isdigit() and 2000 <= int(k_str) <= 2035 and str(k) != muni_code_padded:
                    yr = int(k_str)
                    break

        if yr is not None:
            try:
                val = round(float(r_vals[0]), 2)
                if min_val <= val <= max_val:
                    series.append((yr, val))
            except ValueError:
                pass

    if not series:
        raise ValueError("Ei kelvollisia lukuarvoja PxWeb-vastauksessa")

    series.sort(key=lambda x: x[0])
    return series


# ==============================================================================
# 3. ULKOKEHÄN 4 EKOLOGISTA RAJAPINTAHAKUA
# ==============================================================================
def fetch_syke_khk_series(muni_code_padded, muni_name):
    """
    1. Alueelliset KHK-päästöt (t CO2e/as.):
    Kokeilee SYKE:n PxWeb-rajapintaa (lasu.syke.fi) ja OData-rajapintaa.
    """
    px_urls = [
        "https://lasu.syke.fi/pxweb/api/v1/fi/khk/khk_kunta.px",
        "https://lasu.syke.fi/pxweb/api/v1/fi/KHK/khk_kunta.px"
    ]
    for url in px_urls:
        try:
            s = query_pxweb_series(
                url, muni_code_padded, muni_name,
                metric_keywords=["asukas", "per as", "co2e/as"],
                min_val=0.5, max_val=25.0
            )
            if s:
                return s, "SYKE PxWeb API (KHK)"
        except Exception:
            continue

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


def fetch_syke_consumption_series(muni_code_padded, muni_name):
    """
    2. Kulutusperusteinen hiilijalanjälki (t CO2e/as.):
    Kokeilee SYKE:n kulutuspäästöjen PxWeb-rajapintaa ja OData-rajapintaa.
    """
    px_urls = [
        "https://lasu.syke.fi/pxweb/api/v1/fi/kulutus/kulutus_kunta.px",
        "https://lasu.syke.fi/pxweb/api/v1/fi/Kulutus/kulutus_kunta.px"
    ]
    for url in px_urls:
        try:
            s = query_pxweb_series(
                url, muni_code_padded, muni_name,
                metric_keywords=["asukas", "per as", "co2"],
                min_val=1.0, max_val=30.0
            )
            if s:
                return s, "SYKE PxWeb API (Kulutus)"
        except Exception:
            continue

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


def fetch_water_load_series(muni_code_padded, muni_name):
    """
    3. Vesistö- ja ravinnekuormitus (% kuormitus):
    Kokeilee SYKE:n PintavesienTila-rajapintaa sekä Luonnonvarakeskuksen (Luke PxWeb)
    ravinnetasetilastoa tiukalla järkevyysrajalla (20..300 %).
    """
    odata_url = f"https://avoindata.syke.fi/odata/PintavesienTila?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    try:
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
    except Exception:
        pass

    raise RuntimeError("Vesistö-API ei palauttanut kuntalukua -> käytetään SYKE Vesikartta (CSV) -arvoa")


def fetch_landuse_pressure_series(muni_code_padded, muni_name):
    """
    4. Maankäyttöpaine vs. lähiluonto (% kuormitus):
    Kokeilee järjestyksessä:
      A) Tilastokeskus StatFin PxWeb API: Taajama-aste, % (statfin_vaerak_pxt_11ra.px)
      B) Jyväskylän yliopiston Lipas REST API: Kunnan luonto- ja virkistysalueiden määrä
    """
    # A) Tilastokeskus StatFin PxWeb API (Taajama-aste, %)
    statfin_url = "https://pxdata.stat.fi/PxWeb/api/v1/fi/StatFin/vaerak/statfin_vaerak_pxt_11ra.px"
    try:
        s = query_pxweb_series(
            statfin_url,
            muni_code_padded,
            muni_name,
            metric_keywords=["taajama-aste", "taajama_aste"],
            min_val=20.0,
            max_val=150.0
        )
        if s:
            return s, "StatFin API (Taajama-aste)"
    except Exception as e:
        print(f"ℹ️ StatFin Taajama-aste ei vastannut ({e}), kokeillaan Lipas API:a...")

    # B) Lipas REST API (JYU): Kunnan luontopolut ja virkistyskohteet
    try:
        muni_int = int(muni_code_padded)
        lipas_url = f"https://lipas.fi/api/sports-sites?cityCodes={muni_int}&pageSize=100"
        r_lipas = requests.get(lipas_url, headers=HEADERS, timeout=12)
        if r_lipas.status_code == 200:
            sites = r_lipas.json()
            if isinstance(sites, list) and len(sites) >= 10:
                count = len(sites)
                # Suhteutetaan lähiluontokohteiden määrä viitearvoon (sijoittuu turvallisesti välille 55..135 %)
                pressure_idx = round(max(55.0, min(135.0, (88.0 / max(40, count)) * 100.0)), 1)
                return [(datetime.now().year - 1, pressure_idx)], "Lipas API (Lähiluonto)"
    except Exception as e:
        print(f"ℹ️ Lipas API ei vastannut ({e})")

    raise RuntimeError("Maankäyttö-API ei vastannut -> käytetään SYKE Liiteri (CSV) -arvoa")


# ==============================================================================
# 4. REITITYS JA VARAJÄRJESTELMÄ (manual_indicators.csv)
# ==============================================================================
def get_indicator_series(ind, sotkanet_region_id, muni_code_padded, muni_name, fallbacks):
    ind_id = str(ind.get("id", "")).strip()
    src = str(ind.get("source", "")).lower().strip()

    try:
        if src == "sotkanet" and "indicator_id" in ind:
            return fetch_sotkanet_series(ind["indicator_id"], sotkanet_region_id, muni_code_padded)
        elif src == "syke_khk":
            return fetch_syke_khk_series(muni_code_padded, muni_name)
        elif src == "syke_kulutus":
            return fetch_syke_consumption_series(muni_code_padded, muni_name)
        elif src == "syke_vesistot":
            return fetch_water_load_series(muni_code_padded, muni_name)
        elif src == "syke_maankaytto":
            return fetch_landuse_pressure_series(muni_code_padded, muni_name)
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
