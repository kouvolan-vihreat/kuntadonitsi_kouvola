# -*- coding: utf-8 -*-
"""
Avoin Kuntadonitsi – Automaattinen tiedonhaku (THL Sotkanet, SYKE PxWeb & Tilastokeskus StatFin)
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


# ==============================================================================
# 1. THL SOTKANET REST API (Kuntatunnistus & Aikasarjahaku)
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
                    print(f"✅ Kunta tunnistettu: {muni_name} (kuntakoodi {code_padded} -> Sotkanet ID {reg_id})")
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
        raise ValueError(f"Sotkanet ID {indicator_id}: ei rivejä kunnalle")

    muni_rows.sort(key=lambda x: int(x["year"]))
    series = [(int(r["year"]), round(float(r["value"]), 2)) for r in muni_rows]
    return series, f"SOTKANET API (ID {indicator_id})"


# ==============================================================================
# 2. YLEISKÄYTTÖINEN PXWEB-HAKUMOOTTORI (SYKE lasu.syke.fi & StatFin pxdata.stat.fi)
# ==============================================================================
def discover_pxweb_tables(root_url, keyword="", max_depth=3):
    """Etsii PxWeb-palvelimelta automaattisesti .px-taulujen täydet URL-osoitteet."""
    found = []
    try:
        r = requests.get(root_url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return found
        items = r.json()
        if not isinstance(items, list):
            return found
        for item in items:
            item_id = str(item.get("id", ""))
            item_type = str(item.get("type", "")).lower()
            item_text = str(item.get("text", "")).lower()
            next_url = root_url.rstrip("/") + "/" + item_id
            if item_type == "t" or item_id.endswith(".px"):
                if not keyword or keyword.lower() in item_id.lower() or keyword.lower() in item_text:
                    found.append(next_url)
            elif item_type == "l" and max_depth > 1:
                found.extend(discover_pxweb_tables(next_url, keyword, max_depth - 1))
    except Exception:
        pass
    return found


def query_pxweb_table(table_url, muni_code_padded, muni_name, unit_keywords=None, sector_keywords=None):
    """Tekee automaattisen metadata- ja POST-kyselyn mihin tahansa SYKE/StatFin PxWeb-tauluun."""
    meta_r = requests.get(table_url, headers=HEADERS, timeout=15)
    if meta_r.status_code != 200:
        raise ValueError(f"PxWeb metadata HTTP {meta_r.status_code} ({table_url})")

    meta = meta_r.json()
    query_items = []
    muni_matched = False
    muni_clean = str(int(muni_code_padded))

    for var in meta.get("variables", []):
        code = str(var.get("code", ""))
        code_low = code.lower()
        vals = [str(v) for v in var.get("values", [])]
        texts = [str(t).lower() for t in var.get("valueTexts", [])]

        # 1. Alue- tai kuntamuuttuja
        if any(k in code_low for k in ["kunta", "alue", "region"]) or any(muni_name.lower() in t for t in texts):
            match_val = None
            for v, t in zip(vals, texts):
                if (
                    v in [muni_code_padded, f"KU{muni_code_padded}", muni_clean]
                    or v.endswith(muni_code_padded)
                    or muni_name.lower() == t.strip()
                    or t.startswith(muni_name.lower() + " ")
                ):
                    match_val = v
                    break
            if not match_val:
                raise ValueError(f"Kuntaa {muni_name} ({muni_code_padded}) ei löytynyt taulusta {table_url}")
            muni_matched = True
            query_items.append({"code": code, "selection": {"filter": "item", "values": [match_val]}})

        # 2. Vuosimuuttuja
        elif "vuosi" in code_low or "year" in code_low or "aika" in code_low:
            selected_years = vals[-8:] if len(vals) > 8 else vals
            query_items.append({"code": code, "selection": {"filter": "item", "values": selected_years}})

        # 3. Suure / Yksikkö / Tiedot
        elif unit_keywords and any(k in code_low for k in ["yksikk", "suure", "tiedot", "muuttuja", "tunnusluku"]):
            chosen = vals[0]
            for kw in unit_keywords:
                for v, t in zip(vals, texts):
                    if kw.lower() in t or kw.lower() in v.lower():
                        chosen = v
                        break
                if chosen != vals[0]:
                    break
            query_items.append({"code": code, "selection": {"filter": "item", "values": [chosen]}})

        # 4. Sektori / Luokka
        elif sector_keywords and any(k in code_low for k in ["sektori", "luokka", "toimiala", "kayttovoima", "polttoaine"]):
            chosen = vals[0]
            for kw in sector_keywords:
                for v, t in zip(vals, texts):
                    if kw.lower() in t or kw.lower() in v.lower():
                        chosen = v
                        break
                if chosen != vals[0]:
                    break
            query_items.append({"code": code, "selection": {"filter": "item", "values": [chosen]}})

        # 5. Muut muuttujat (valitaan ensimmäinen kokonais-/oletusarvo)
        else:
            chosen = vals[0]
            for v, t in zip(vals, texts):
                if any(w in t for w in ["yhteensä", "kaikki", "hinku", "kokonais"]):
                    chosen = v
                    break
            query_items.append({"code": code, "selection": {"filter": "item", "values": [chosen]}})

    if not muni_matched:
        raise ValueError(f"Taulussa {table_url} ei ole kuntamuuttujaa")

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
        yr = next((int(str(k)[:4]) for k in keys if str(k)[:4].isdigit() and 1990 <= int(str(k)[:4]) <= 2035), None)
        if yr and r_vals and r_vals[0] not in [".", "..", "...", "-", None, ""]:
            try:
                series.append((yr, round(float(r_vals[0]), 2)))
            except ValueError:
                pass

    if not series:
        raise ValueError(f"Taulu {table_url} ei palauttanut lukuarvoja")

    series.sort(key=lambda x: x[0])
    return series


# ==============================================================================
# 3. EKOLOGISEN KATON NELJÄ RAJAPINTAHAKUA
# ==============================================================================
def fetch_syke_khk_series(sotkanet_region_id, muni_code_padded, muni_name):
    """
    1. Alueelliset KHK-päästöt (t CO2e/as.):
    Hakee SYKE:n lasu.syke.fi PxWeb-rajapinnasta tai Sotkanetin SYKE-peilauksesta.
    """
    candidate_urls = [
        "https://lasu.syke.fi/pxweb/api/v1/fi/khk/khk_kunta.px",
        "https://lasu.syke.fi/pxweb/api/v1/fi/KHK/khk_kunta.px"
    ]
    discovered = discover_pxweb_tables("https://lasu.syke.fi/pxweb/api/v1/fi", keyword="khk")
    for u in discovered:
        if u not in candidate_urls:
            candidate_urls.append(u)

    for url in candidate_urls:
        try:
            s = query_pxweb_table(
                url, muni_code_padded, muni_name,
                unit_keywords=["asukas", "per as", "co2e/as"],
                sector_keywords=["yhteensä", "kaikki", "kokonais"]
            )
            if s:
                return s, "SYKE PxWeb API (KHK)"
        except Exception:
            continue

    # Varapolku: Sotkanetiin peilatut viralliset kasvihuonekaasu- ja ympäristöindikaattorit
    for ind_id in [4007, 5379, 5629, 3561]:
        try:
            s, _ = fetch_sotkanet_series(ind_id, sotkanet_region_id, muni_code_padded)
            if s:
                return s, f"SYKE / Sotkanet API (ID {ind_id})"
        except Exception:
            continue

    raise ValueError("SYKE KHK-päästöjä ei saatu PxWeb- eikä Sotkanet-rajapinnasta")


def fetch_syke_consumption_series(sotkanet_region_id, muni_code_padded, muni_name):
    """
    2. Kulutusperusteinen hiilijalanjälki (t CO2e/as.):
    Hakee SYKE:n lasu.syke.fi PxWeb-rajapinnasta (kulutusosio).
    """
    candidate_urls = [
        "https://lasu.syke.fi/pxweb/api/v1/fi/kulutus/kulutus_kunta.px",
        "https://lasu.syke.fi/pxweb/api/v1/fi/Kulutus/kulutus_kunta.px"
    ]
    discovered = discover_pxweb_tables("https://lasu.syke.fi/pxweb/api/v1/fi", keyword="kulutus")
    for u in discovered:
        if u not in candidate_urls:
            candidate_urls.append(u)

    for url in candidate_urls:
        try:
            s = query_pxweb_table(
                url, muni_code_padded, muni_name,
                unit_keywords=["asukas", "per as", "co2"],
                sector_keywords=["yhteensä", "kaikki", "kokonais"]
            )
            if s:
                return s, "SYKE PxWeb API (Kulutus)"
        except Exception:
            continue

    raise ValueError("SYKE Kulutus PxWeb -rajapinta ei vastannut")


def fetch_statfin_traffic_series(sotkanet_region_id, muni_code_padded, muni_name):
    """
    3. Fossiilikäyttöisten autojen osuus / Liikenteen kuormitus (%):
    Hakee Tilastokeskuksen StatFin PxWeb -rajapinnasta (Moottoriajoneuvokanta kunnittain)
    tai Sotkanetin liikennerajapinnasta.
    """
    statfin_urls = [
        "https://pxdata.stat.fi/PxWeb/api/v1/fi/StatFin/mkan/statfin_mkan_pxt_11ic.px",
        "https://pxdata.stat.fi/PxWeb/api/v1/fi/StatFin/mkan/statfin_mkan_pxt_11id.px"
    ]
    for url in statfin_urls:
        try:
            meta_r = requests.get(url, headers=HEADERS, timeout=15)
            if meta_r.status_code != 200:
                continue
            meta = meta_r.json()
            q_items = []
            muni_ok = False
            for var in meta.get("variables", []):
                code = var["code"]
                vals = [str(v) for v in var["values"]]
                texts = [str(t).lower() for t in var.get("valueTexts", [])]
                if "alue" in code.lower() or "kunta" in code.lower():
                    target_v = None
                    for v, t in zip(vals, texts):
                        if v in [f"KU{muni_code_padded}", muni_code_padded] or muni_name.lower() == t.strip():
                            target_v = v
                            break
                    if not target_v:
                        break
                    muni_ok = True
                    q_items.append({"code": code, "selection": {"filter": "item", "values": [target_v]}})
                elif "käyttövoima" in code.lower() or "kayttovoima" in code.lower() or "polttoaine" in code.lower():
                    # Haetaan Yhteensä ('SSS' / vals[0]), Bensiini ('01') ja Diesel ('02')
                    sel_v = [vals[0]]
                    for v, t in zip(vals, texts):
                        if "bensiini" in t or "diesel" in t:
                            sel_v.append(v)
                    q_items.append({"code": code, "selection": {"filter": "item", "values": list(dict.fromkeys(sel_v))}})
                elif "vuosi" in code.lower():
                    q_items.append({"code": code, "selection": {"filter": "item", "values": vals[-5:]}})
                else:
                    q_items.append({"code": code, "selection": {"filter": "item", "values": [vals[0]]}})

            if not muni_ok:
                continue

            post_r = requests.post(url, json={"query": q_items, "response": {"format": "json"}}, headers=HEADERS, timeout=20)
            if post_r.status_code == 200:
                rows = post_r.json().get("data", [])
                by_year = {}
                for row in rows:
                    keys = row.get("key", [])
                    val_str = row.get("values", [None])[0]
                    yr = next((int(k) for k in keys if str(k).isdigit() and 2010 <= int(k) <= 2035), None)
                    if yr and val_str not in [".", "..", "-", None]:
                        by_year.setdefault(yr, []).append(float(val_str))
                series = []
                for yr, nums in sorted(by_year.items()):
                    total = max(nums)
                    fossil = sum(n for n in nums if n != total)
                    if total > 0 and fossil > 0:
                        pct = round(min(99.9, (fossil / total) * 100.0), 1)
                        series.append((yr, pct))
                if series:
                    return series, "Tilastokeskus StatFin API (Ajoneuvokanta)"
        except Exception:
            continue

    # Varapolku: Sotkanetin avoimet ympäristö- ja yhdyskuntamittarit
    for ind_id in [3218, 254]:
        try:
            s, _ = fetch_sotkanet_series(ind_id, sotkanet_region_id, muni_code_padded)
            if s:
                return s, f"Sotkanet API (ID {ind_id})"
        except Exception:
            continue

    raise ValueError("Tilastokeskus StatFin -liikennerajapinta ei vastannut")


def fetch_sotkanet_env_series(ind, sotkanet_region_id, muni_code_padded):
    """
    4. Pienhiukkasaltistus ja lähiympäristö (THL Sotkanet / SYKE):
    Kokeilee ensisijaisesti määriteltyä indicator_id:tä (esim. 3560) ja varalla muita
    Sotkanetin virallisia ympäristöterveysmittareita (3369, 3218).
    """
    primary_id = ind.get("indicator_id", 3560)
    candidate_ids = [primary_id, 3560, 3369, 3218]
    seen = set()
    for cid in candidate_ids:
        if cid in seen:
            continue
        seen.add(cid)
        try:
            s, label = fetch_sotkanet_series(cid, sotkanet_region_id, muni_code_padded)
            if s:
                return s, f"THL / SYKE Sotkanet API (ID {cid})"
        except Exception:
            continue

    raise ValueError("Ympäristöindikaattoria ei löytynyt Sotkanet-rajapinnasta")


def get_indicator_series(ind, sotkanet_region_id, muni_code_padded, muni_name):
    ind_id = str(ind.get("id", "")).strip()
    src = str(ind.get("source", "")).lower().strip()

    try:
        if src == "sotkanet":
            return fetch_sotkanet_series(ind["indicator_id"], sotkanet_region_id, muni_code_padded)
        elif src == "syke_khk":
            return fetch_syke_khk_series(sotkanet_region_id, muni_code_padded, muni_name)
        elif src == "syke_kulutus":
            return fetch_syke_consumption_series(sotkanet_region_id, muni_code_padded, muni_name)
        elif src == "statfin_liikenne":
            return fetch_statfin_traffic_series(sotkanet_region_id, muni_code_padded, muni_name)
        elif src == "sotkanet_ymparisto":
            return fetch_sotkanet_env_series(ind, sotkanet_region_id, muni_code_padded)
        elif "indicator_id" in ind and ind["indicator_id"]:
            return fetch_sotkanet_series(ind["indicator_id"], sotkanet_region_id, muni_code_padded)
        else:
            raise ValueError(f"Tuntematon rajapintalähde '{src}'")
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
