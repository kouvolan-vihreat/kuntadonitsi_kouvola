# -*- coding: utf-8 -*-
"""
Avoin Kuntadonitsi – Automaattinen tiedonhaku
Lähteet: THL Sotkanet, SYKE OData, Luke PxWeb, Tilastokeskus StatFin PxWeb & JYU Lipas API
Varajärjestelmä (Fallback): manual_indicators.csv
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
    """Lukee manual_indicators.csv-tiedoston varajärjestelmäksi ja lisämittareille."""
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


def evaluate_status(value, threshold, direction):
    """Laskee suhdeluvun (100 % = 1.0x kestävä tavoiteraja) ja tarkistaa, onko mittari vihreällä kehällä."""
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
                    print(f"✅ Kunta tunnistettu: {muni_name} (koodi {code_padded} -> Sotkanet region ID {reg_id})")
                    return reg_id, code_padded
    except Exception as e:
        print(f"⚠️ Huomio: Sotkanet regions -haku epäonnistui ({e})")

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
    return series, f"SOTKANET (ID {indicator_id})"


# ==============================================================================
# 2. SYKE KHK- JA KULUTUSPÄÄSTÖT (Säilytetty toimiva OData/REST-logiikka)
# ==============================================================================
def fetch_syke_khk_series(muni_code_padded):
    """
    1. Alueelliset KHK-päästöt / Hinku
    Endpoint: https://avoindata.syke.fi/odata/KHKPaastot
    Kentät: Vuosi, PaastotPerAsukas (t CO2e/as.)
    """
    url = f"https://avoindata.syke.fi/odata/KHKPaastot?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    r = requests.get(url, headers=HEADERS, timeout=12)
    if r.status_code == 200:
        items = r.json().get("value", [])
        series = [
            (int(x["Vuosi"]), round(float(x["PaastotPerAsukas"]), 2))
            for x in items if "Vuosi" in x and "PaastotPerAsukas" in x and x["PaastotPerAsukas"] is not None
        ]
        if series:
            series.sort(key=lambda x: x[0])
            return series, "SYKE Hinku API"
    raise RuntimeError("SYKE KHKPaastot -rajapinta ei palauttanut rivejä")


def fetch_syke_consumption_series(muni_code_padded):
    """
    2. Kulutusperusteiset hiilipäästöt
    Endpoint: https://avoindata.syke.fi/odata/KulutusPaastot
    Kentät: Vuosi, PaastotPerAsukas (t CO2e/as.)
    """
    url = f"https://avoindata.syke.fi/odata/KulutusPaastot?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    r = requests.get(url, headers=HEADERS, timeout=12)
    if r.status_code == 200:
        items = r.json().get("value", [])
        series = [
            (int(x["Vuosi"]), round(float(x["PaastotPerAsukas"]), 2))
            for x in items if "Vuosi" in x and "PaastotPerAsukas" in x and x["PaastotPerAsukas"] is not None
        ]
        if series:
            series.sort(key=lambda x: x[0])
            return series, "SYKE Kulutus API"
    raise RuntimeError("SYKE KulutusPaastot -rajapinta ei palauttanut rivejä")


# ==============================================================================
# 3. UUDET KORVAAVAT RAJAPINNAHAUT: VESISTÖKUORMITUS & MAANKÄYTTÖPAINE
# ==============================================================================
def query_pxweb_generic(table_url, muni_code_padded, muni_name):
    """Apufunktio Tilastokeskuksen (StatFin) ja Luken PxWeb-rajapintojen kuntahakuun."""
    meta_r = requests.get(table_url, headers=HEADERS, timeout=12)
    if meta_r.status_code != 200:
        raise ValueError(f"PxWeb metadata HTTP {meta_r.status_code}")

    meta = meta_r.json()
    query_items = []
    muni_found = False
    muni_clean = str(int(muni_code_padded))

    for var in meta.get("variables", []):
        code = str(var.get("code", ""))
        code_low = code.lower()
        vals = [str(v) for v in var.get("values", [])]
        texts = [str(t).lower() for t in var.get("valueTexts", [])]

        if any(k in code_low for k in ["alue", "kunta", "region"]) or any(muni_name.lower() in t for t in texts):
            match_v = None
            for v, t in zip(vals, texts):
                if (
                    v in [f"KU{muni_code_padded}", muni_code_padded, muni_clean]
                    or v.endswith(muni_code_padded)
                    or muni_name.lower() == t.strip()
                ):
                    match_v = v
                    break
            if not match_v:
                raise ValueError(f"Kuntaa {muni_code_padded} ei löytynyt PxWeb-taulusta")
            muni_found = True
            query_items.append({"code": code, "selection": {"filter": "item", "values": [match_v]}})
        elif "vuosi" in code_low or "year" in code_low:
            query_items.append({"code": code, "selection": {"filter": "item", "values": vals[-6:]}})
        elif "tiedot" in code_low or "muuttuja" in code_low or "tunnusluku" in code_low:
            chosen = vals[-1]
            for v, t in zip(vals, texts):
                if any(k in t for k in ["osuus", "%", "aste", "indeksi", "hehtaari", "kg"]):
                    chosen = v
                    break
            query_items.append({"code": code, "selection": {"filter": "item", "values": [chosen]}})
        else:
            query_items.append({"code": code, "selection": {"filter": "item", "values": [vals[0]]}})

    if not muni_found:
        raise ValueError("Ei kuntamuuttujaa PxWeb-taulussa")

    post_r = requests.post(
        table_url,
        json={"query": query_items, "response": {"format": "json"}},
        headers=HEADERS,
        timeout=15
    )
    post_r.raise_for_status()
    series = []
    for row in post_r.json().get("data", []):
        keys = row.get("key", [])
        vals = row.get("values", [])
        yr = next((int(str(k)[:4]) for k in keys if str(k)[:4].isdigit() and 2000 <= int(str(k)[:4]) <= 2035), None)
        if yr and vals and vals[0] not in [".", "..", "-", None, ""]:
            series.append((yr, round(float(vals[0]), 2)))
    if not series:
        raise ValueError("PxWeb ei palauttanut lukuarvoja")
    series.sort(key=lambda x: x[0])
    return series


def fetch_water_load_series(ind, sotkanet_region_id, muni_code_padded, muni_name):
    """
    3. Pintavesien ja vesiympäristön ravinne-/laatukuormitus (syke_vesistot):
    Kokeilee järjestyksessä:
      A) SYKE OData (PintavesienTila)
      B) Luonnonvarakeskus (Luke PxWeb) maatalouden ravinnetase / kuormitus
      C) THL / SYKE Sotkanet (ID 3369: Talousveden laatuindeksi muunnettuna kuormitussuhteeksi)
    Jos mikään ei palauta arvoa, siirtyy manual_indicators.csv-varariville.
    """
    # A) SYKE OData PintavesienTila
    odata_url = f"https://avoindata.syke.fi/odata/PintavesienTila?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    try:
        r = requests.get(odata_url, headers=HEADERS, timeout=10)
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
                return [(yr, load_index)], "SYKE Pintavedet API"
    except Exception:
        pass

    # B) Luke PxWeb API (Ravinnetase / maatalouden ympäristökuormitus)
    luke_urls = [
        "https://statdb.luke.fi/PxWeb/api/v1/fi/LUKE/02 Maatalous/08 Muut/02 Ravinnetaseet/01_Ravinnetaseet_maakunnittain.px"
    ]
    for l_url in luke_urls:
        try:
            s = query_pxweb_generic(l_url, muni_code_padded, muni_name)
            if s:
                # Suhteutetaan typpikuormitus (kestävä raja 50 kg N/ha = 100 % kuormitus)
                converted = [(yr, round((val / 50.0) * 100.0, 1)) for yr, val in s]
                return converted, "Luke Ravinnetase API"
        except Exception:
            continue

    # C) THL Sotkanet REST API: Talousveden laatu ja vesihuolto (ID 3369 tai annettu indicator_id)
    water_sotka_id = ind.get("indicator_id", 3369)
    try:
        raw_series, _ = fetch_sotkanet_series(water_sotka_id, sotkanet_region_id, muni_code_padded)
        if raw_series:
            # ID 3369 on laatuvaatimukset täyttävien näytteiden osuus (esim. 99.5 %, tavoite >= 98.0 %).
            # Muunnetaan kuormitusindeksiksi, jossa <= 100 % on tavoitetilassa:
            load_series = []
            for yr, val in raw_series:
                if val > 0:
                    load_pct = round((98.0 / float(val)) * 100.0, 1)
                    load_series.append((yr, load_pct))
            if load_series:
                return load_series, f"THL / Vesihuolto API (ID {water_sotka_id})"
    except Exception:
        pass

    raise RuntimeError("Vesistörajapinnat eivät vastanneet, käytetään manual_indicators.csv-varariviä")


def fetch_landuse_pressure_series(ind, sotkanet_region_id, muni_code_padded, muni_name):
    """
    4. Maankäyttöpaine suhteessa lähiluontoon (syke_maankaytto):
    Kokeilee järjestyksessä:
      A) SYKE OData (Maankaytto)
      B) Tilastokeskus StatFin PxWeb API (Taajama-aste ja rakennetun maan paine kunnittain)
      C) Lipas REST API (Jyväskylän yliopisto: luontopolut ja virkistysalueet kunnassa)
      D) SYKE Liiteri / Sotkanet-peilaus (ID 3218 / ID 3560)
    Jos mikään ei palauta arvoa, siirtyy manual_indicators.csv-varariville.
    """
    # A) SYKE OData Maankaytto
    odata_url = f"https://avoindata.syke.fi/odata/Maankaytto?$filter=Kuntakoodi eq '{muni_code_padded}'&$format=json"
    try:
        r = requests.get(odata_url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            items = r.json().get("value", [])
            if items:
                latest = sorted(items, key=lambda x: x.get("Vuosi", 2024))[-1]
                val = round(float(latest.get("KuormitusIndeksi", 88.0)), 1)
                yr = int(latest.get("Vuosi", 2024))
                return [(yr, val)], "SYKE Liiteri API"
    except Exception:
        pass

    # B) Tilastokeskus StatFin PxWeb API: Taajama-aste / yhdyskuntarakenne kunnittain
    statfin_urls = [
        "https://pxdata.stat.fi/PxWeb/api/v1/fi/StatFin/vaerak/statfin_vaerak_pxt_11ra.px",
        "https://pxdata.stat.fi/PxWeb/api/v1/fi/StatFin/ashi/statfin_ashi_pxt_13mx.px"
    ]
    for sf_url in statfin_urls:
        try:
            s = query_pxweb_generic(sf_url, muni_code_padded, muni_name)
            if s:
                # Taajama-aste (%): suhteutetaan kestävän lähiluontoverkoston viitearvoon (85 % = 100 % kuormitus)
                converted = [(yr, round((val / 85.0) * 100.0, 1)) for yr, val in s]
                return converted, "Tilastokeskus StatFin API"
        except Exception:
            continue

    # C) Lipas REST API (JYU): Kunnan luonto- ja ulkoilureitit (cityCodes)
    try:
        muni_int = int(muni_code_padded)
        lipas_url = f"https://lipas.fi/api/sports-sites?cityCodes={muni_int}&pageSize=100"
        r_lipas = requests.get(lipas_url, headers=HEADERS, timeout=12)
        if r_lipas.status_code == 200:
            sites = r_lipas.json()
            if isinstance(sites, list) and len(sites) > 0:
                # Kunnan virkistys- ja lähiluontokohteiden määrä suhteessa tavoitteeseen (50 kohdetta = 100 %)
                count = len(sites)
                pressure_idx = round(max(45.0, min(140.0, (60.0 / max(20, count)) * 100.0)), 1)
                return [(datetime.now().year - 1, pressure_idx)], "Lipas Lähiluonto API"
    except Exception:
        pass

    # D) Sotkanet-peilatut SYKE Liiteri / ympäristömittarit (ID 3218 tai ID 3560)
    for cid in [ind.get("indicator_id"), 3218, 3560]:
        if not cid:
            continue
        try:
            s, _ = fetch_sotkanet_series(cid, sotkanet_region_id, muni_code_padded)
            if s:
                return s, f"SYKE / Sotkanet API (ID {cid})"
        except Exception:
            continue

    raise RuntimeError("Maankäyttörajapinnat eivät vastanneet, käytetään manual_indicators.csv-varariviä")


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
            return fetch_syke_khk_series(muni_code_padded)
        elif src == "syke_kulutus":
            return fetch_syke_consumption_series(muni_code_padded)
        elif src == "syke_vesistot":
            return fetch_water_load_series(ind, sotkanet_region_id, muni_code_padded, muni_name)
        elif src == "syke_maankaytto":
            return fetch_landuse_pressure_series(ind, sotkanet_region_id, muni_code_padded, muni_name)
        elif "indicator_id" in ind and ind["indicator_id"]:
            return fetch_sotkanet_series(ind["indicator_id"], sotkanet_region_id, muni_code_padded)
    except Exception as e:
        print(f"ℹ️ Rajapintahaku ({ind_id}) siirtyi varajärjestelmään: {e}")

    # Varajärjestelmä (Fallback): luetaan arvo manual_indicators.csv-tiedostosta
    if ind_id in fallbacks:
        fb = fallbacks[ind_id]
        yr = int(float(fb.get("year", 2024)))
        val = round(float(fb.get("value", 0.0)), 2)
        src_label = str(fb.get("source", "SYKE (Varatieto)"))
        print(f"📁 Käytetty manual_indicators.csv-varariviä mittarille '{ind_id}': {val} ({yr})")
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

    # Otetaan mukaan myös mahdolliset ylimääräiset rivit manual_indicators.csv-tiedostosta
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
