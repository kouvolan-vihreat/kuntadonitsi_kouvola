import time
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

def get_sotkanet_indicator_title(indicator_id):
    """Hakee indikaattorin virallisen suomenkielisen nimen suoraan Sotkanetista."""
    try:
        url = f"https://sotkanet.fi/rest/1.1/indicators/{indicator_id}"
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            return res.json().get("title", {}).get("fi", "")
    except Exception:
        pass
    return ""

def get_sotkanet_value(indicator_id, sotkanet_region_id):
    """Hakee tietyn kunnan tuoreimman arvon THL Sotkanet REST API:sta (sisältää uudelleenyrityksen)."""
    years = range(2018, 2027)
    years_query = "&".join([f"years={y}" for y in years])
    url = f"https://sotkanet.fi/rest/1.1/json?indicator={indicator_id}&{years_query}&genders=total"
    
    for attempt in range(3):
        try:
            time.sleep(1)  # Pieni tauko, jotta THL:n rajapinta ei ruuhkaudu
            res = requests.get(url, headers=HEADERS, timeout=25)
            res.raise_for_status()
            data = res.json()
            
            muni_rows = [
                r for r in data 
                if r.get("region") == sotkanet_region_id and r.get("value") is not None
            ]
            if not muni_rows:
                return 0.0, "N/A"
                
            latest = sorted(muni_rows, key=lambda x: x["year"])[-1]
            return float(latest["value"]), str(latest["year"])
        except Exception as e:
            print(f"Yritys {attempt + 1} epäonnistui (ID {indicator_id}): {e}")
            time.sleep(2)
            
    return 0.0, "Virhe"

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

    muni_sotkanet = config["municipality"]["sotkanet_code"]
    sotkanet_region_id = get_sotkanet_region_id(muni_sotkanet)
    rows = []

    # 1. Haetaan automaattiset API-mittarit Sotkanetista
    for ind in config["indicators"]:
        try:
            val, year = get_sotkanet_value(ind["indicator_id"], sotkanet_region_id)
            official_title = get_sotkanet_indicator_title(ind["indicator_id"])
            if official_title:
                print(f"Haettu ID {ind['indicator_id']} ({official_title}): {val} ({year})")
        except Exception as e:
            print(f"Virhe haettaessa {ind['id']}: {e}")
            val, year = 0.0, "Virhe"

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
            "year": year
        })

    # 2. Luetaan täydentävät mittarit CSV-tiedostosta
    manual_df = pd.read_csv("manual_indicators.csv")
    for _, row in manual_df.iterrows():
        ratio_pct, is_safe = normalize_indicator(
            float(row["value"]), float(row["threshold"]), row["direction"]
        )
        rows.append({
            "id": row["id"],
            "name": row["name"],
            "domain": row["domain"],
            "source": row["source"],
            "value": float(row["value"]),
            "threshold": float(row["threshold"]),
            "unit": row["unit"],
            "ratio_pct": ratio_pct,
            "is_safe": is_safe,
            "year": str(row["year"])
        })

    out_df = pd.DataFrame(rows)
    out_df.to_csv("doughnut_results.csv", index=False)
    print("Kuntadonitsin data päivitetty onnistuneesti!")

if __name__ == "__main__":
    main()
