import yaml
import requests
import pandas as pd

def get_statfin_value(muni_code, metric_code):
    """Hakee tuoreimman arvon Tilastokeskuksen Kuntien avainluvut -rajapinnasta."""
    url = "https://pxdata.stat.fi/PxWeb/api/v1/fi/Kuntien_avainluvut/uusin/142h.px"
    payload = {
        "query": [
            {"code": "Alue", "selection": {"filter": "item", "values": [muni_code]}},
            {"code": "Tiedot", "selection": {"filter": "item", "values": [metric_code]}}
        ],
        "response": {"format": "json-stat2"}
    }
    res = requests.post(url, json=payload, timeout=20)
    res.raise_for_status()
    data = res.json()
    values = [v for v in data["value"] if v is not None]
    return float(values[-1]), "Uusin"

def get_sotkanet_value(indicator_id):
    """Hakee esimerkinomaisesti viimeisimmän vuositiedon THL Sotkanet REST API:sta."""
    # Tarkistetaan viimeisimmät tilastovuodet
    for year in [2025, 2024, 2023, 2022, 2021]:
        url = f"https://sotkanet.fi/rest/1.1/json?indicator={indicator_id}&years={year}&genders=total"
        res = requests.get(url, headers={"User-Agent": "Kuntadonitsi/1.0"}, timeout=15)
        if res.status_code == 200 and len(res.json()) > 0:
            df = pd.DataFrame(res.json())
            return float(df["value"].median()), str(year)
    return 0.0, "N/A"

def normalize_indicator(value, threshold, domain, direction):
    """Muuntaa mittarin prosenttiluvuksi suhteessa kestävään rajaan (100 % = raja)."""
    if direction == "higher_is_better":
        # Esim. työllisyys 70 % / tavoite 75 % = 93 %
        ratio_pct = round((value / threshold) * 100, 1)
        is_safe = value >= threshold
    else:
        # Kun pienempi luku on parempi (esim. päästöt tai sairastavuus)
        ratio_pct = round((value / threshold) * 100, 1)
        is_safe = value <= threshold
    return ratio_pct, is_safe

def main():
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    muni_statfin = config["municipality"]["statfin_code"]
    rows = []

    # 1. Haetaan automaattiset API-mittarit
    for ind in config["indicators"]:
        try:
            if ind["source"] == "statfin":
                val, year = get_statfin_value(muni_statfin, ind["metric_code"])
            else:
                val, year = get_sotkanet_value(ind["indicator_id"])
        except Exception as e:
            print(f"Virhe haettaessa {ind['id']}: {e}")
            val, year = ind["threshold"], "Virhe"

        ratio_pct, is_safe = normalize_indicator(
            val, ind["threshold"], ind["domain"], ind["direction"]
        )
        rows.append({
            "id": ind["id"],
            "name": ind["name"],
            "domain": ind["domain"],
            "source": ind["source"].upper(),
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
            float(row["value"]), float(row["threshold"]), row["domain"], row["direction"]
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
