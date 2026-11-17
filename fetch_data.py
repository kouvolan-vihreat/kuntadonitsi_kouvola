import os
import time
from datetime import datetime, timezone, timedelta
import yaml
import requests
import pandas as pd

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Kuntadonitsi/1.0)"}

def get_sotkanet_region_id(muni_code_str):
    """Etsii kunnan virallisella numerolla (esim. '286') Sotkanetin sisäisen region-ID:n."""
    url = "https://sotkanet.fi/rest/1.1/regions"
    res = requests.get(url, headers=HEADERS, timeout=25)
    res.raise_for_status()
    for reg in res.json():
        if str(reg.get("code")) == str(muni_code_str) and reg.get("category") == "KUNTA":
            return reg["id"]
    raise ValueError(f"Kuntakoodia {muni_code_str} ei löytynyt Sotkanetista.")

def get_sotkanet_series(indicator_id, sotkanet_region_id):
    """Hakee kunnan koko aikasarjan (2018-2026) ja tuoreimman arvon Sotkanetista."""
    years = range(2018, 2027)
    years_query = "&".join([f"years={y}" for y in years])
    url = f"https://sotkanet.fi/rest/1.1/json?indicator={indicator_id}&{years_query}&genders=total"
    
    for attempt in range(3):
        try:
            time.sleep(1)
            res = requests.get(url, headers=HEADERS, timeout=25)
            res.raise_for_status()
            data = res.json()
            
            muni_rows = [
                r for r in data 
                if r.get("region") == sotkanet_region_id and r.get("value") is not None
            ]
            if not muni_rows:
                return 0.0, "N/A", []
                
            sorted_rows = sorted(muni_rows, key=lambda x: x["year"])
            latest = sorted_rows[-1]
            return float(latest["value"]), str(latest["year"]), sorted_rows
        except Exception as e:
            print(f"Yritys {attempt + 1} epäonnistui (ID {indicator_id}): {e}")
            time.sleep(2)
            
    return 0.0, "Virhe", []

def normalize_indicator(value, threshold, direction):
    """Muuntaa mittarin prosenttiluvuksi suhteessa kestävään rajaan (100 % = raja)."""
    if value <= 0.0:
        return 0.0, False
    ratio_pct = round((value / threshold) * 100, 1)
    if direction == "higher_is_better":
        is_safe = value >= threshold
    else:
        is_safe = value <= threshold
    return ratio_pct, is_safe

def main():
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Suomen aikavyöhyke (UTC+2 / UTC+3) aikaleimaa varten
    now_fi = datetime.now(timezone(timedelta(hours=2)))
    timestamp_str = now_fi.strftime("%d.%m.%Y klo %H:%M")
    snapshot_month = now_fi.strftime("%Y-%m")

    muni_sotkanet = config["municipality"]["sotkanet_code"]
    sotkanet_region_id = get_sotkanet_region_id(muni_sotkanet)
    
    rows = []
    history_records = []

    # 1. Haetaan automaattiset API-mittarit ja niiden vuosihistoria Sotkanetista
    for ind in config["indicators"]:
        val, year, series = get_sotkanet_series(ind["indicator_id"], sotkanet_region_id)
        ratio_pct, is_safe = normalize_indicator(val, ind["threshold"], ind["direction"])
        
        rows.append({
            "id": ind["id"],
            "name": ind["name"],
            "domain": ind["domain"],
            "source": f"SOTKANET (ID {ind['indicator_id']})",
            "value": val,
            "threshold": ind["threshold"],
            "unit": ind["unit"],
            "ratio_pct": ratio_pct,
            "is_safe": is_safe,
            "year": year,
            "updated_at": timestamp_str
        })

        # Tallennetaan myös mittarin aiemmat tilastovuodet historiakäyrää varten
        for item in series:
            h_val = float(item["value"])
            h_ratio, h_safe = normalize_indicator(h_val, ind["threshold"], ind["direction"])
            history_records.append({
                "period": str(item["year"]),
                "record_type": "Tilastovuosi",
                "id": ind["id"],
                "name": ind["name"],
                "domain": ind["domain"],
                "value": h_val,
                "threshold": ind["threshold"],
                "unit": ind["unit"],
                "ratio_pct": h_ratio,
                "is_safe": h_safe
            })

    # 2. Luetaan täydentävät mittarit CSV-tiedostosta
    manual_df = pd.read_csv("manual_indicators.csv")
    for _, row in manual_df.iterrows():
        val = float(row["value"])
        thresh = float(row["threshold"])
        ratio_pct, is_safe = normalize_indicator(val, thresh, row["direction"])
        
        rows.append({
            "id": row["id"],
            "name": row["name"],
            "domain": row["domain"],
            "source": row["source"],
            "value": val,
            "threshold": thresh,
            "unit": row["unit"],
            "ratio_pct": ratio_pct,
            "is_safe": is_safe,
            "year": str(row["year"]),
            "updated_at": timestamp_str
        })

        history_records.append({
            "period": str(row["year"]),
            "record_type": "Tilastovuosi",
            "id": row["id"],
            "name": row["name"],
            "domain": row["domain"],
            "value": val,
            "threshold": thresh,
            "unit": row["unit"],
            "ratio_pct": ratio_pct,
            "is_safe": is_safe
        })

    # 3. Lisätään kuluvan kuukauden (YYYY-MM) tallennuspiste kaikille mittareille
    for r in rows:
        history_records.append({
            "period": snapshot_month,
            "record_type": "Kuukausiseuranta",
            "id": r["id"],
            "name": r["name"],
            "domain": r["domain"],
            "value": r["value"],
            "threshold": r["threshold"],
            "unit": r["unit"],
            "ratio_pct": r["ratio_pct"],
            "is_safe": r["is_safe"]
        })

    # Tallennetaan nykyhetken tilannekuva
    out_df = pd.DataFrame(rows)
    out_df.to_csv("doughnut_results.csv", index=False)

    # Yhdistetään uudet historiarivit mahdolliseen aiempaan doughnut_history.csv -tiedostoon
    new_hist_df = pd.DataFrame(history_records)
    if os.path.exists("doughnut_history.csv"):
        old_hist_df = pd.read_csv("doughnut_history.csv")
        combined_hist = pd.concat([old_hist_df, new_hist_df], ignore_index=True)
        # Pidetään vain tuorein arvo per ajanjakso (period) ja mittari (id)
        combined_hist = combined_hist.drop_duplicates(subset=["period", "id", "record_type"], keep="last")
    else:
        combined_hist = new_hist_df

    combined_hist = combined_hist.sort_values(by=["id", "period"])
    combined_hist.to_csv("doughnut_history.csv", index=False)
    print(f"Data ja historiatiedosto päivitetty onnistuneesti ({timestamp_str})!")

if __name__ == "__main__":
    main()
