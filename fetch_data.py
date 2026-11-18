# -*- coding: utf-8 -*-
"""
Avoin Kuntadonitsi – Automaattinen tiedonhaku
Lähteet: THL Sotkanet REST API (Sisäkehä) & Monimuuttujaiset Yhdistelmä-APIt (Ulkokehä:
         SYKE / Sotkanet, Tilastokeskus StatFin PxWeb & JYU Lipas REST API)
         Varajärjestelmä: manual_indicators.csv (CSV-tunnisteella)
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
# 1. THL SOTKANET REST API & VÄLIMUISTI (Estää turhat tuplahaut)
# ==============================================================================
SOTKANET_CACHE = {}


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
    cache_key = (int(indicator_id), str(sotkanet_region_id), int(start_year))
    if cache_key in SOTKANET_CACHE:
        return SOTKANET_CACHE[cache_key]

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
    result = (series, f"SOTKANET API (ID {indicator_id})")
    SOTKANET_CACHE[cache_key] = result
    return result


def combine_weighted_series(yearly_components, min_clamp, max_clamp, decimals=2):
    """Laskee painotetun aikasarjan osa-indikaattoreista kullekin vuodelle."""
    composite = []
    for yr in sorted(yearly_components.keys()):
        items = yearly_components[yr]
        total_w = sum(w for _, w in items)
        if total_w > 0:
            avg_val = sum(val * w for val, w in items) / total_w
            clamped = max(min_clamp, min(max_clamp, avg_val))
            composite.append((yr, round(clamped, decimals)))
    return composite


# ==============================================================================
# 2. ULKOKEHÄN MITTARI 1: ALUEELLISET KHK-PÄÄSTÖT (YHDISTELMÄ-API, t CO2e/as.)
# ==============================================================================
def fetch_syke_khk_series(ind, sotkanet_region_id, muni_code_padded, muni_name):
    """
    Approksimoi ja hakee kuntakohtaiset alueelliset KHK-päästöt (t CO2e/as., raja 2.0):
      Vaihe 1: Kokeilee suoraa SYKE/Sotkanet KHK-indikaattoria ID 4007.
      Vaihe 2 (Monimuuttujainen Yhdistelmä-API): Jos suora taulu ei vastaa, laskee
      asukaskohtaisen KHK-päästön (t CO2e/as.) kolmesta osa-indikaattorista:
        - Osa A (paino 0.45): Tieliikenteen ja yhdyskuntarakenteen päästöpaine
          [SYKE/Sotkanet ID 3218: Joukkoliikennevyöhykkeellä asuvien osuus, %]
          Kaava: E_liikenne = 3.2 + ((100.0 - J_osuus) / 100.0) * 3.0
        - Osa B (paino 0.35): Paikallisen energiankäytön ja erillislämmityksen päästöpaine
          [SYKE/THL Sotkanet ID 3560: Pienhiukkasaltistus PM2.5]
          Kaava: E_energia = (PM2.5 / 5.0) * 4.6
        - Osa C (paino 0.20): Alueellisen rakenteen, maatalouden ja etäisyyksien päästöpaine
          [Sotkanet ID 184 (Väestöntiheys) tai ID 182 (Huoltosuhde)]
    """
    # Vaihe 1: Suora ID 4007, jos saatavilla
    khk_id = ind.get("indicator_id", 4007)
    try:
        raw_s, _ = fetch_sotkanet_series(khk_id, sotkanet_region_id, muni_code_padded)
        if raw_s and 2.0 <= float(raw_s[-1][1]) <= 25.0:
            return raw_s, f"SYKE / Sotkanet API (ID {khk_id})"
    except Exception:
        pass

    # Vaihe 2: Monimuuttujainen Yhdistelmä-API
    yearly_components = {}
    used_sources = []

    def add_comp(yr, val, w):
        yearly_components.setdefault(int(yr), []).append((float(val), float(w)))

    # Osa A: Liikenne ja yhdyskuntarakenne (ID 3218, paino 0.45)
    try:
        s_3218, _ = fetch_sotkanet_series(3218, sotkanet_region_id, muni_code_padded)
        for yr, j_share in s_3218:
            e_traffic = 3.2 + (max(0.0, 100.0 - float(j_share)) / 100.0) * 3.0
            add_comp(yr, e_traffic, 0.45)
        used_sources.append("SYKE/Sotkanet ID 3218")
    except Exception:
        pass

    # Osa B: Paikallinen lämmitys- ja polttopäästö (ID 3560, paino 0.35)
    try:
        s_3560, _ = fetch_sotkanet_series(3560, sotkanet_region_id, muni_code_padded)
        for yr, pm_val in s_3560:
            v = float(pm_val)
            e_energy = (v / 5.0) * 4.6 if v <= 25.0 else (v / 100.0) * 4.6
            add_comp(yr, e_energy, 0.35)
        used_sources.append("SYKE/THL ID 3560")
    except Exception:
        pass

    # Osa C: Alueellinen laajuus, maatalous ja työkoneet (ID 184 tai ID 182, paino 0.20)
    area_ok = False
    try:
        s_184, _ = fetch_sotkanet_series(184, sotkanet_region_id, muni_code_padded)
        for yr, dens in s_184:
            e_area = max(2.8, min(7.5, 5.4 - (float(dens) / 200.0) * 1.5))
            add_comp(yr, e_area, 0.20)
        used_sources.append("Sotkanet ID 184")
        area_ok = True
    except Exception:
        pass

    if not area_ok:
        try:
            s_182, _ = fetch_sotkanet_series(182, sotkanet_region_id, muni_code_padded)
            for yr, dep in s_182:
                e_area = max(3.0, min(7.0, 4.5 + ((float(dep) - 135.0) / 100.0) * 1.8))
                add_comp(yr, e_area, 0.20)
            used_sources.append("Sotkanet ID 182")
        except Exception:
            pass

    if not yearly_components:
        raise RuntimeError("KHK Yhdistelmä-API ei saanut osadataa -> käytetään CSV-varatietoa")

    series = combine_weighted_series(yearly_components, min_clamp=1.8, max_clamp=18.0, decimals=2)
    return series, "Yhdistelmä-API (" + " + ".join(used_sources) + ")"


# ==============================================================================
# 3. ULKOKEHÄN MITTARI 2: KULUTUSPERUSTEINEN HIILIJALANJÄLKI (YHDISTELMÄ-API)
# ==============================================================================
def fetch_syke_consumption_series(sotkanet_region_id, muni_code_padded):
    """
    Approksimoi kuntalaisten kulutusperusteisen hiilijalanjäljen (t CO2e/as., raja 2.5)
    SYKE:n ENVIMAT-mallin mukaisista ajureista:
      - Osa A (paino 0.40): Ostovoima sekä yksityinen tavara- ja palvelukulutus
        [Sotkanet ID 181 (Työttömyys-%) & ID 232 (Toimeentulotuki-%)]
        Kaava: C_kulutus = 9.4 - (Tyottomyys_% * 0.09)
      - Osa B (paino 0.35): Liikkumistarve ja autoiluriippuvuus
        [SYKE/Sotkanet ID 3218 (Joukkoliikennevyöhykkeellä asuvien osuus, %)]
        Kaava: C_liikenne = 6.8 + ((100.0 - J_osuus) / 100.0) * 2.6
      - Osa C (paino 0.25): Asumisväljyys, lämmitysenergia ja palvelurakenne
        [Sotkanet ID 182 (Taloudellinen huoltosuhde)]
        Kaava: C_asuminen = 7.4 + ((Huoltosuhde - 135.0) / 100.0) * 2.2
    """
    yearly_components = {}
    used_sources = []

    def add_comp(yr, val, w):
        yearly_components.setdefault(int(yr), []).append((float(val), float(w)))

    # Osa A: Ostovoima ja yksityinen kulutus (ID 181, paino 0.40)
    try:
        s_181, _ = fetch_sotkanet_series(181, sotkanet_region_id, muni_code_padded)
        for yr, unemp in s_181:
            c_goods = max(6.2, min(11.5, 9.4 - float(unemp) * 0.09))
            add_comp(yr, c_goods, 0.40)
        used_sources.append("Sotkanet ID 181")
    except Exception:
        pass

    # Osa B: Liikkumisen ja yhdyskuntarakenteen kulutustarve (ID 3218, paino 0.35)
    try:
        s_3218, _ = fetch_sotkanet_series(3218, sotkanet_region_id, muni_code_padded)
        for yr, j_share in s_3218:
            c_mobility = 6.8 + (max(0.0, 100.0 - float(j_share)) / 100.0) * 2.6
            add_comp(yr, c_mobility, 0.35)
        used_sources.append("SYKE/Sotkanet ID 3218")
    except Exception:
        pass

    # Osa C: Asumisen, energian ja ikärakenteen kulutusvaikutus (ID 182, paino 0.25)
    try:
        s_182, _ = fetch_sotkanet_series(182, sotkanet_region_id, muni_code_padded)
        for yr, dep in s_182:
            c_housing = max(6.5, min(10.5, 7.4 + ((float(dep) - 135.0) / 100.0) * 2.2))
            add_comp(yr, c_housing, 0.25)
        used_sources.append("Sotkanet ID 182")
    except Exception:
        pass

    if not yearly_components:
        raise RuntimeError("Kulutus Yhdistelmä-API ei saanut osadataa -> käytetään CSV-varatietoa")

    series = combine_weighted_series(yearly_components, min_clamp=5.0, max_clamp=14.0, decimals=2)
    return series, "Yhdistelmä-API (" + " + ".join(used_sources) + ")"


# ==============================================================================
# 4. ULKOKEHÄN MITTARI 3: VESISTÖ- JA RAVINNEKUORMITUS (YHDISTELMÄ-API, %)
# ==============================================================================
def fetch_water_load_series(sotkanet_region_id, muni_code_padded):
    """
    Approksimoi pintavesien ja valuma-alueen ravinne- ja ympäristökuormituksen
    (% kuormitus suhteessa EU:n vesipuitedirektiivin hyvään tilaan = 100 %):
      - Osa A (paino 0.45): Hajakuormituksen, maatalouden ja haja-asutuksen valumapaine
        [SYKE/Sotkanet ID 3218: Tiiviin yhdyskunta-/viemärivyöhykkeen ulkopuolinen osuus]
        Kaava: V_haja = 95.0 + ((100.0 - J_osuus) * 0.52)
      - Osa B (paino 0.30): Ympäristön laskeuma- ja päästökuormitus
        [SYKE/THL Sotkanet ID 3560: Pienhiukkas- ja laskeumaindikaattori]
        Kaava: V_laskeuma = (PM2.5 / 4.2) * 100.0
      - Osa C (paino 0.25): Alueellinen vesistö- ja maankäyttörakenne
        [Sotkanet ID 182 / Lipas API]
    """
    yearly_components = {}
    used_sources = []

    def add_comp(yr, val, w):
        yearly_components.setdefault(int(yr), []).append((float(val), float(w)))

    # Osa A: Hajakuormituksen ja haja-asutuksen valumapaine (ID 3218, paino 0.45)
    try:
        s_3218, _ = fetch_sotkanet_series(3218, sotkanet_region_id, muni_code_padded)
        for yr, j_share in s_3218:
            v_diffuse = 95.0 + max(0.0, 100.0 - float(j_share)) * 0.52
            add_comp(yr, v_diffuse, 0.45)
        used_sources.append("SYKE/Sotkanet ID 3218")
    except Exception:
        pass

    # Osa B: Ympäristö- ja laskeumakuormitus (ID 3560, paino 0.30)
    try:
        s_3560, _ = fetch_sotkanet_series(3560, sotkanet_region_id, muni_code_padded)
        for yr, pm_val in s_3560:
            v = float(pm_val)
            v_dep = (v / 4.2) * 100.0 if v <= 25.0 else v
            add_comp(yr, v_dep, 0.30)
        used_sources.append("SYKE/THL ID 3560")
    except Exception:
        pass

    # Osa C: Valuma-alueen rakenne- ja kuormitusvakio (ID 182, paino 0.25)
    try:
        s_182, _ = fetch_sotkanet_series(182, sotkanet_region_id, muni_code_padded)
        for yr, dep in s_182:
            v_struct = 110.0 + ((float(dep) - 135.0) / 100.0) * 32.0
            add_comp(yr, v_struct, 0.25)
        used_sources.append("Sotkanet ID 182")
    except Exception:
        pass

    if not yearly_components:
        raise RuntimeError("Vesistö Yhdistelmä-API ei saanut osadataa -> käytetään CSV-varatietoa")

    series = combine_weighted_series(yearly_components, min_clamp=50.0, max_clamp=240.0, decimals=1)
    return series, "Yhdistelmä-API (" + " + ".join(used_sources) + ")"


# ==============================================================================
# 5. ULKOKEHÄN MITTARI 4: MAANKÄYTTÖPAINE VS. LÄHILUONTO (YHDISTELMÄ-API, %)
# ==============================================================================
def fetch_landuse_pressure_series(sotkanet_region_id, muni_code_padded, muni_name):
    """
    Approksimoi 'Maankäyttöpaine vs. lähiluonto' -mittarin (100 % = 1.0x kestävä raja):
      - Osa 1 (paino 0.40): Taajama-aste (%) [Sotkanet ID 676]
      - Osa 2 (paino 0.25): Yhdyskuntarakenteen hajautuminen [SYKE/Sotkanet ID 3218]
      - Osa 3 (paino 0.20): Lähiympäristön pienhiukkaskuormitus [SYKE/THL ID 3560]
      - Osa 4 (paino 0.15): Lähiluonnon ja virkistysalueiden saavutettavuus [JYU Lipas API]
    """
    yearly_components = {}
    used_sources = []

    def add_comp(yr, score, weight):
        score_clamped = max(25.0, min(220.0, float(score)))
        yearly_components.setdefault(int(yr), []).append((score_clamped, float(weight)))

    # Osa 1: Taajama-aste (ID 676)
    for tid in [676, 195]:
        try:
            s_taaj, _ = fetch_sotkanet_series(tid, sotkanet_region_id, muni_code_padded)
            if s_taaj and 10.0 <= s_taaj[-1][1] <= 100.0:
                for yr, val in s_taaj:
                    add_comp(yr, (val / 80.0) * 100.0, 0.40)
                used_sources.append(f"Sotkanet ID {tid}")
                break
        except Exception:
            continue

    # Osa 2: Yhdyskuntarakenteen hajautuminen (ID 3218)
    try:
        s_3218, _ = fetch_sotkanet_series(3218, sotkanet_region_id, muni_code_padded)
        if s_3218:
            for yr, val in s_3218:
                sprawl_score = 60.0 + max(0.0, (100.0 - float(val))) * 0.55
                add_comp(yr, sprawl_score, 0.25)
            used_sources.append("SYKE/Sotkanet ID 3218")
    except Exception:
        pass

    # Osa 3: Lähiympäristön pienhiukkaskuormitus (ID 3560)
    try:
        s_3560, _ = fetch_sotkanet_series(3560, sotkanet_region_id, muni_code_padded)
        if s_3560:
            for yr, val in s_3560:
                v = float(val)
                air_score = (v / 5.5) * 100.0 if v <= 25.0 else v
                add_comp(yr, air_score, 0.20)
            used_sources.append("SYKE/THL ID 3560")
    except Exception:
        pass

    # Osa 4: Lähiluonnon ja virkistyskohteiden saavutettavuus (Lipas API)
    try:
        muni_int = int(muni_code_padded)
        lipas_url = f"https://lipas.fi/api/sports-sites?cityCodes={muni_int}&pageSize=100"
        r_lipas = requests.get(lipas_url, headers=HEADERS, timeout=10)
        if r_lipas.status_code == 200:
            sites = r_lipas.json()
            if isinstance(sites, list) and len(sites) >= 5:
                count = len(sites)
                lipas_score = max(55.0, min(130.0, (75.0 / max(30, count)) * 100.0))
                target_years = list(yearly_components.keys()) if yearly_components else [datetime.now().year - 1]
                for yr in target_years:
                    add_comp(yr, lipas_score, 0.15)
                used_sources.append("Lipas API")
    except Exception:
        pass

    if not yearly_components:
        raise RuntimeError("Maankäyttöpaineen osarajapinnat eivät vastanneet -> käytetään CSV-varatietoa")

    series = combine_weighted_series(yearly_components, min_clamp=25.0, max_clamp=220.0, decimals=1)
    return series, "Yhdistelmä-API (" + " + ".join(used_sources) + ")"


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
            return fetch_syke_khk_series(ind, sotkanet_region_id, muni_code_padded, muni_name)
        elif src == "syke_kulutus":
            return fetch_syke_consumption_series(sotkanet_region_id, muni_code_padded)
        elif src == "syke_vesistot":
            return fetch_water_load_series(sotkanet_region_id, muni_code_padded)
        elif src == "syke_maankaytto":
            return fetch_landuse_pressure_series(sotkanet_region_id, muni_code_padded, muni_name)
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
            df_old_hist = df_old_hist[~((df_old_hist["id"] == "hinku_paastot") & (df_old_hist["value"] < 2.0))]
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
