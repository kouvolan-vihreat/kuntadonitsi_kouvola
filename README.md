# 🍩 Avoin Kuntadonitsi – toteutusopas ja dokumentaatio

Tämä tietovarasto ja vaiheittainen opas näyttävät, kuinka rakennat mille tahansa suomalaiselle kunnalle automaattisesti päivittyvän donitsitalousmallin (Kuntadonitsin) täysin **ilmaisilla, avoimen lähdekoodin työkaluilla**. 

Toteutus ei vaadi omaa palvelinta, ulkoisia pilvipalveluita, maksullisia ohjelmistolisenssejä eikä aiempaa syvällistä ohjelmointikokemusta – kaikki tiedostot, automaattinen tiedonhaku, historiatallennus ja salamannopea julkinen verkkosivu pyörivät **100 % suoraan GitHubin sisällä** (GitHub Actions & GitHub Pages).

*(Oletusasetuksissa esimerkkinä on Kouvolan kaupunki, kuntakoodi `286`, mutta muiden kuntien edustajat voivat vaihtaa minkä tahansa Suomen 309 kunnasta muuttamalla kuntanumeron asetustiedostossa!)*

---

## 1. Mitä työkaluja käytämme ja miksi?

Ratkaisu koostuu neljästä ilmaisesta työkalusta, jotka toimivat suoraan GitHubissa:

| Työkalu | Mikä se on? | Mitä se tekee tässä projektissa? | Hinta |
| :--- | :--- | :--- | :--- |
| **GitHub-tietovarasto (Repository)** | Pilvipohjainen kansio koodille ja tiedostoille | Säilyttää projektin asetustiedostot, hakuskriptin, tilasto- ja historiadatan sekä verkkosivun. | 0 € (Julkinen projekti) |
| **GitHub Actions** | GitHubin sisäänrakennettu ajastin ja automaattirobotti | Herää automaattisesti kerran kuukaudessa (tai heti kun muokkaat asetuksia), hakee tuoreet kuntaluvut ja aikasarjat THL:n Sotkanet-rajapinnasta ja tallentaa ne GitHubiin. | 0 € (2000 min/kk ilmaista ajoaikaa) |
| **Python (Pandas ja Requests)** | Avoimen lähdekoodin ohjelmointikieli ja datakirjastot | Hakee datan rajapinnoista, laskee suhdeluvut verrattuna kestäviin raja-arvoihin ja ylläpitää kuukausittaista historiatiedostoa. | 0 € (Avoin lähdekoodi) |
| **GitHub Pages (HTML + Plotly.js)** | GitHubin oma, välitön verkkosivujen julkaisualusta | Lukee kunnan nimen, tuoreimman tilanteen sekä historiadatan ja piirtää interaktiivisen kuntadonitsin sekä kehityskäyrät välittömästi selaimeen. | 0 € |

---

## 2. Vaihe 1: GitHub-tilin ja projektikansion (Repository) luominen tai kopiointi

Voit tehdä kaikki tämän oppaan vaiheet suoraan verkkoselaimessa asentamatta mitään omalle tietokoneellesi.

### Vaihtoehto A: Kopioi tämä valmis projekti omalle kunnallesi (Suositeltu)
1. Luo ilmainen käyttäjätunnus GitHub-palveluun ja kirjaudu sisään.
2. Klikkaa tämän sivun oikeasta yläkulmasta **Fork**-painiketta, jolloin saat kaikki alla olevat tiedostot suoraan omalle GitHub-tilillesi.
3. Siirry kohtaan **Vaihe 4 (kohta 1–2)** kytkeäksesi automaattirobotin kirjoitusoikeudet päälle, muokkaa kuntasi tiedot `config.yaml`- ja `manual_indicators.csv`-tiedostoihin, ja kytke verkkosivu päälle **Vaiheessa 5**.

### Vaihtoehto B: Luo projekti kokonaan alusta
1. Luo ilmainen käyttäjätunnus GitHub-palveluun ja kirjaudu sisään.
2. Klikkaa oikeasta yläkulmasta **+ (plus) -painiketta** ja valitse **New repository** (Uusi tietovarasto).
3. Anna projektille nimi kohtaan *Repository name*, esimerkiksi **kuntadonitsi**.
4. Valitse näkyvyydeksi **Public** (Julkinen). Tämä on tärkeää, jotta saat GitHub Actionsin automaattiset ajot ja GitHub Pages -verkkosivun täysin ilmaiseksi.
5. Laita rasti ruutuun **Add a README file** ja klikkaa vihreää **Create repository** -painiketta.

Projektikansioon tulee kuusi ydintiedostoa, joiden lisäksi robotti luo automaattisesti kaksi datatiedostoa (`doughnut_results.csv` ja `doughnut_history.csv`):

```text
kuntadonitsi/
├── config.yaml                         # Kunnan nimi, kuntakoodi ja raja-arvot
├── manual_indicators.csv               # Kerran vuodessa käsin päivitettävät luvut
├── requirements.txt                    # Tarvittavat ilmaiset Python-kirjastot
├── fetch_data.py                       # Robottiskripti, joka hakee datan ja tallentaa historian
├── index.html                          # Verkkosivu: kaksikehäinen donitsi ja aikasarjakaaviot
├── doughnut_results.csv                # (Syntyy automaattisesti) Viimeisin tilannekuva ja aikaleima
├── doughnut_history.csv                # (Syntyy automaattisesti) Vuosi- ja kuukausitason aikasarja
└── .github/workflows/update_data.yml   # GitHubin ajastin (ajaa haun automaattisesti)
```

---

## 3. Vaihe 2: Asetustiedostojen luominen ja muokkaaminen

### 3.1 Tiedosto 1: `requirements.txt`
Klikkaa GitHubissa **Add file -> Create new file**. Kirjoita tiedoston nimeksi `requirements.txt` ja liitä sisältöön seuraavat rivit. Ne kertovat GitHubille, mitkä ilmaiset Python-lisäosat tietojen hakuun ladataan:

```text
requests
pandas
pyyaml
```
Tallenna tiedosto klikkaamalla oikeasta yläkulmasta **Commit changes...**

### 3.2 Tiedosto 2: `config.yaml` (Kunnan valinta ja varmennetut Sotkanet-indikaattorit)
Luo tai muokkaa tiedostoa nimeltä `config.yaml`. Tässä tiedostossa määrität, minkä kunnan tiedot haetaan. Kun muutat kunnan nimen kohtaan `name` ja kuntanumeron kohtaan `sotkanet_code` (esim. Kouvola on `286`, Lohja `444`, Helsinki `091`, Tampere `837`), sekä datan haku että verkkosivun pääotsikko päivittyvät automaattisesti!

Kaikki sosiaalisen perustan mittarit haetaan suoraan THL:n Sotkanet-tietokannasta, joka sisältää valmiiksi sekä THL:n, Kelan että Tilastokeskuksen kuntakohtaiset avainluvut:

```yaml
municipality:
  name: "Kouvola"
  statfin_code: "KU286"
  sotkanet_code: "286"

indicators:
  - id: "sairastavuus"
    name: "Kansanterveys (THL sairastavuusindeksi)"
    domain: "Sosiaalinen perusta"
    source: "sotkanet"
    indicator_id: 244
    threshold: 100.0
    unit: "indeksi"
    direction: "lower_is_better"

  - id: "tyottomyys"
    name: "Työttömien osuus työvoimasta"
    domain: "Sosiaalinen perusta"
    source: "sotkanet"
    indicator_id: 181
    threshold: 8.0
    unit: "%"
    direction: "lower_is_better"

  - id: "toimeentulo"
    name: "Toimeentulotukea saaneet asukkaat"
    domain: "Sosiaalinen perusta"
    source: "sotkanet"
    indicator_id: 232
    threshold: 6.0
    unit: "%"
    direction: "lower_is_better"

  - id: "huoltosuhde"
    name: "Taloudellinen huoltosuhde"
    domain: "Sosiaalinen perusta"
    source: "sotkanet"
    indicator_id: 182
    threshold: 135.0
    unit: "indeksi"
    direction: "lower_is_better"
```

### 3.3 Tiedosto 3: `manual_indicators.csv` (Käsin päivitettävät mittarit)
Niille mittareille, joita ei vielä haeta suoralla rajapintakyselyllä (tai jotka päivittyvät kunnan vesilaitoksen ja SYKE:n raporteista kerran vuodessa), luodaan yksinkertainen pilkulla eroteltu tekstitiedosto `manual_indicators.csv`. Voit muokata tätä suoraan GitHubin selaimessa kerran vuodessa:

```csv
id,name,domain,source,value,threshold,unit,direction,year
hinku_paastot,Alueelliset KHK-paastot (SYKE Hinku),Ekologinen katto,SYKE Hinku,5.2,2.0,t CO2e/as.,lower_is_better,2024
kulutus_hiili,Kulutusperusteinen hiilijalanjalki,Ekologinen katto,SYKE ENVIMAT,8.6,2.5,t CO2e/as.,lower_is_better,2023
vesistot,Pintavesien ravinnekuormitus,Ekologinen katto,SYKE Hertta,130.0,100.0,% kuormitus,lower_is_better,2024
luonto_paine,Maankayttopaine vs. lahiluonto,Ekologinen katto,SYKE Liiteri,88.0,100.0,% kuormitus,lower_is_better,2024
```

---

## 4. Vaihe 3: Automaattisen tiedonhakijan ja historiatallentimen (`fetch_data.py`) luominen

Luo seuraavaksi tiedosto nimeltä `fetch_data.py`. Tämä vikasietoinen skripti:
1. Lukee `config.yaml`-asetuksesi ja etsii valitun kunnan sisäisen Sotkanet-tunnisteen.
2. Hakee tuoreimmat tilastot sekä vuosien 2018–2026 kehityshistorian THL:n Sotkanet-rajapinnasta.
3. Yhdistää tiedot `manual_indicators.csv`-taulukkoon ja laskee suhdeluvut kestäviin rajoihin (`100 % = raja`).
4. Tallentaa nykyhetken tilannekuvan ja päivitysaikaleiman tiedostoon `doughnut_results.csv` sekä päivittää kuukausittaisen ja vuosittaisen aikasarjan tiedostoon `doughnut_history.csv`.

```python
import os
import time
from datetime import datetime, timezone, timedelta
import yaml
import requests
import pandas as pd

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Kuntadonitsi/1.0)"}

def get_sotkanet_region_id(muni_code_str):
    """Etsii kunnan virallisella numerolla (esim. '286') Sotkanetin sisäisen region-ID:n."""
    url = "[https://sotkanet.fi/rest/1.1/regions](https://sotkanet.fi/rest/1.1/regions)"
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
    url = f"[https://sotkanet.fi/rest/1.1/json?indicator=](https://sotkanet.fi/rest/1.1/json?indicator=){indicator_id}&{years_query}&genders=total"
    
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

    # Suomen aikavyöhyke aikaleimaa varten
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
        combined_hist = combined_hist.drop_duplicates(subset=["period", "id", "record_type"], keep="last")
    else:
        combined_hist = new_hist_df

    combined_hist = combined_hist.sort_values(by=["id", "period"])
    combined_hist.to_csv("doughnut_history.csv", index=False)
    print(f"Data ja historiatiedosto päivitetty onnistuneesti ({timestamp_str})!")

if __name__ == "__main__":
    main()
```

---

## 5. Vaihe 4: Automaattisen ajastuksen kytkeminen (GitHub Actions)

Nyt valjastamme GitHubin oman automaattirobotin (GitHub Actions) ajamaan yllä olevan `fetch_data.py`-skriptin automaattisesti kolmella tavalla: 1) joka kuukauden 1. päivänä, 2) heti kun muokkaat asetustiedostoja (`config.yaml` tai `manual_indicators.csv`), tai 3) milloin tahansa yhdellä napin painalluksella.

1. Mene ensin GitHub-projektisi yläreunasta kohtaan **Settings** (Asetukset) -> vasemmasta reunasta **Actions -> General**.
2. Rullaa sivun alareunaan kohtaan *Workflow permissions* ja valitse **Read and write permissions** (Luku- ja kirjoitusoikeudet). Klikkaa **Save**. Tämä antaa robotille luvan tallentaa uudet tilastoluvut ja historiadatan takaisin kansioosi.
3. Palaa etusivulle (Code) ja klikkaa **Add file -> Create new file**.
4. Kirjoita tiedoston nimeksi tarkasti: `.github/workflows/update_data.yml` (GitHub luo alikansiot automaattisesti, kun kirjoitat kauttaviivat).
5. Liitä tiedostoon seuraava sisältö ja tallenna (Commit changes):

```yaml
name: Paivita Kuntadonitsin Data

on:
  schedule:
    # Ajetaan automaattisesti kuukauden 1. paivana klo 05:00 UTC
    - cron: '0 5 1 * *'
  workflow_dispatch: # Mahdollistaa ajon napista painamalla milloin vain
  push:
    branches: [ main ]
    paths:
      - 'config.yaml'
      - 'manual_indicators.csv'
      - 'fetch_data.py'

jobs:
  fetch-and-update:
    runs-on: ubuntu-latest
    steps:
      - name: Lataa projektin tiedostot
        uses: actions/checkout@v4

      - name: Asenna Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Asenna kirjastot
        run: pip install -r requirements.txt

      - name: Hae tuore data rajapinnoista
        run: python fetch_data.py

      - name: Tallenna paivitetty data GitHubiin
        run: |
          git config --global user.name "Kuntadonitsi-botti"
          git config --global user.email "actions@github.com"
          git add doughnut_results.csv doughnut_history.csv
          git diff --staged --quiet || git commit -m "Automaattinen datapaivitys"
          git push
```

**Testaa robottia heti:** Klikkaa GitHubin ylävalikosta **Actions**, valitse vasemmalta *Paivita Kuntadonitsin Data* ja klikkaa oikealta **Run workflow**. Muutamassa sekunnissa näet, kuinka robotti hakee luvut ja projektiisi ilmestyvät valmiit `doughnut_results.csv`- ja `doughnut_history.csv`-tiedostot!

---

## 6. Vaihe 5: Verkkosivun (`index.html`) luominen ja julkaisu GitHub Pagesilla

Viimeisenä luomme tiedoston `index.html`, joka:
* Lukee kunnan nimen suoraan `config.yaml`-tiedostosta sivun pääotsikkoon.
* Näyttää yläkulmassa tarkan päivitysaikaleiman (`updated_at`).
* Piirtää puhtaan, visuaalisen kaksikehäisen kuntadonitsin (sisäkehän sosiaaliset vajeet keskellä, sisärajan rengas, vihreä turvallinen tila, ulkorajan rengas ja ulkokehän ekologiset ylitykset ulkopuolella).
* Piirtää rinnakkaiset tarkastelukaaviot sekä interaktiivisen aikasarjakaavion (`doughnut_history.csv`).

1. Klikkaa GitHubissa **Add file -> Create new file**, anna nimeksi `index.html` ja liitä siihen seuraava koodi:

```html
<!DOCTYPE html>
<html lang="fi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Avoin Kuntadonitsi</title>
  <script src="[https://cdn.plot.ly/plotly-2.30.0.min.js](https://cdn.plot.ly/plotly-2.30.0.min.js)"></script>
  <script src="[https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.4.1/papaparse.min.js](https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.4.1/papaparse.min.js)"></script>
  <script src="[https://cdnjs.cloudflare.com/ajax/libs/js-yaml/4.1.0/js-yaml.min.js](https://cdnjs.cloudflare.com/ajax/libs/js-yaml/4.1.0/js-yaml.min.js)"></script>
  <style>
    body { font-family: Arial, sans-serif; max-width: 1180px; margin: 0 auto; padding: 20px; color: #1a202c; background: #f8fafc; }
    .header-row { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; margin-bottom: 6px; }
    h1 { color: #1a365d; margin: 0; }
    h2 { color: #1a365d; margin-top: 28px; margin-bottom: 12px; font-size: 20px; }
    .timestamp-badge { background: #e2e8f0; color: #2d3748; padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: bold; display: inline-flex; align-items: center; gap: 6px; }
    .subtitle { color: #4a5568; margin-bottom: 24px; }
    .cards { display: flex; gap: 20px; margin-bottom: 24px; flex-wrap: wrap; }
    .card { flex: 1; min-width: 240px; background: white; padding: 18px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
    .card.soc { border-left: 5px solid #dd6b20; }
    .card.safe { border-left: 5px solid #2e7d32; }
    .card.eco { border-left: 5px solid #c62828; }
    .card h3 { margin: 0 0 8px 0; font-size: 13px; color: #4a5568; text-transform: uppercase; letter-spacing: 0.5px; }
    .card .val { font-size: 26px; font-weight: bold; color: #1a202c; }
    .card .desc { font-size: 13px; color: #718096; margin-top: 4px; }
    .chart-box { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 24px; }
    .ring-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(480px, 1fr)); gap: 20px; margin-bottom: 24px; }
    .legend-bar { display: flex; gap: 24px; justify-content: center; flex-wrap: wrap; margin-bottom: 14px; font-size: 14px; background: #f1f5f9; padding: 12px 18px; border-radius: 8px; }
    .legend-item { display: flex; align-items: center; gap: 8px; }
    .dot { width: 16px; height: 16px; border-radius: 4px; display: inline-block; }
    .ring-line { width: 22px; height: 5px; border-radius: 2px; display: inline-block; }
    .controls-row { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; margin-bottom: 14px; background: #f1f5f9; padding: 12px 16px; border-radius: 8px; }
    select { padding: 8px 12px; border-radius: 6px; border: 1px solid #cbd5e0; font-size: 14px; background: white; color: #1a202c; font-weight: bold; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
    th, td { padding: 12px 14px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 14px; }
    th { background: #edf2f7; font-weight: bold; }
    .badge-ok { background: #c6f6d5; color: #22543d; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .badge-soc { background: #feebc8; color: #7b341e; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .badge-eco { background: #fed7d7; color: #742a2a; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
  </style>
</head>
<body>

  <div class="header-row">
    <h1 id="main-title">🍩 Kuntakohtainen Kuntadonitsi</h1>
    <div class="timestamp-badge" id="last-updated">🕒 Data päivitetty: Ladataan...</div>
  </div>
  <div class="subtitle">Automaattisesti avoimista rajapinnoista (THL Sotkanet & SYKE) päivittyvä tilannekuva: Sisäkehä (Sosiaalinen perusta) ja Ulkokehä (Ekologinen katto)</div>

  <div class="cards">
    <div class="card soc">
      <h3>Sisäkehä: Sosiaalinen perusta</h3>
      <div class="val" id="soc-metric">- / -</div>
      <div class="desc">Mittaria tavoitetasolla (ei sosiaalista vajetta)</div>
    </div>
    <div class="card safe">
      <h3>Donitsin vihreä kehä</h3>
      <div class="val" id="total-metric">- %</div>
      <div class="desc">Kaikista mittareista turvallisessa tilassa (≤ 100 %)</div>
    </div>
    <div class="card eco">
      <h3>Ulkokehä: Ekologinen katto</h3>
      <div class="val" id="eco-metric">- / -</div>
      <div class="desc">Mittaria luonnon kantokyvyn rajoissa</div>
    </div>
  </div>

  <!-- PÄÄKAAVIO: PUHDAS VISUAALINEN KAKSIKEHÄINEN DONITSI -->
  <div class="chart-box">
    <h2 style="margin-top:0; text-align:center;">Kuntadonitsin kokonaiskuva</h2>
    <div class="legend-bar">
      <div class="legend-item"><span class="dot" style="background:#dd6b20;"></span> <strong>Sosiaalinen vaje</strong> (Sisäkehän sisäpuoli)</div>
      <div class="legend-item"><span class="ring-line" style="background:#9c4221;"></span> <strong>Sisäraja</strong> (Sosiaalinen perusta)</div>
      <div class="legend-item"><span class="dot" style="background:#2e7d32; border: 2px solid #14532d;"></span> <strong>Turvallinen tila</strong> (Vihreä donitsikehä)</div>
      <div class="legend-item"><span class="ring-line" style="background:#7f1d1d;"></span> <strong>Ulkoraja</strong> (Ekologinen katto)</div>
      <div class="legend-item"><span class="dot" style="background:#c62828;"></span> <strong>Ekologinen ylitys</strong> (Ulkokehän ulkopuoli)</div>
    </div>
    <div id="doughnut-main"></div>
  </div>

  <!-- RINNAKKAISET KEHÄT: SISÄKEHÄ VS ULKOKEHÄ -->
  <div class="ring-grid">
    <div class="chart-box" style="margin-bottom:0;">
      <h2 style="margin-top:0;">1. Sisäkehän mittarit: Sosiaalinen perusta</h2>
      <div id="chart-social"></div>
    </div>
    <div class="chart-box" style="margin-bottom:0;">
      <h2 style="margin-top:0;">2. Ulkokehän mittarit: Ekologinen katto</h2>
      <div id="chart-eco"></div>
    </div>
  </div>

  <!-- AJALLINEN KEHITYS JA KUUKAUSISEURANTA -->
  <div class="chart-box">
    <h2 style="margin-top:0;">📈 Ajallinen kehitys ja kuukausiseuranta</h2>
    <div class="controls-row">
      <label for="history-select"><strong>Valitse tarkasteltava mittari:</strong></label>
      <select id="history-select"></select>
      <span style="font-size:13px; color:#4a5568;">(100 % katkoviiva = kestävä tavoiteraja. Kuukausittaiset ajot tallentuvat automaattisesti aikasarjaan.)</span>
    </div>
    <div id="chart-history"></div>
  </div>

  <h2>Lähdedata ja kynnysarvot (100 % = kestävä tavoiteraja)</h2>
  <table id="data-table">
    <thead>
      <tr>
        <th>Kehä / Ulottuvuus</th>
        <th>Mittari</th>
        <th>Kunnan arvo</th>
        <th>Kestävä raja</th>
        <th>Suhde rajaan</th>
        <th>Tila donitsissa</th>
        <th>Lähde (Vuosi)</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>

  <script>
    fetch("config.yaml")
      .then(response => response.text())
      .then(yamlText => {
        const config = jsyaml.load(yamlText);
        if (config && config.municipality && config.municipality.name) {
          const muniName = config.municipality.name;
          document.getElementById("main-title").innerText = `🍩 Kuntadonitsi: ${muniName}`; document.title = `Kuntadonitsi – ${muniName}`;
        }
      })
      .catch(err => console.warn("Kunnan nimeä ei voitu lukea config.yaml-tiedostosta:", err));

    function wrapLabel(str) {
      if (str.length <= 22) return str;
      const words = str.split(" ");
      const mid = Math.ceil(words.length / 2);
      return words.slice(0, mid).join(" ") + "<br>" + words.slice(mid).join(" ");
    }

    Papa.parse("doughnut_results.csv", {
      download: true,
      header: true,
      skipEmptyLines: true,
      complete: function(results) {
        const data = results.data;
        if (data.length > 0 && data[0].updated_at) {
          document.getElementById("last-updated").innerText = `🕒 Data päivitetty: ${data[0].updated_at}`;
        } else {
          document.getElementById("last-updated").innerText = `🕒 Data päivitetty: Automaattinen haku`;
        }

        const soc = data.filter(r => r.domain === "Sosiaalinen perusta");
        const eco = data.filter(r => r.domain === "Ekologinen katto");
        const socSafe = soc.filter(r => String(r.is_safe).toLowerCase() === "true").length;
        const ecoSafe = eco.filter(r => String(r.is_safe).toLowerCase() === "true").length;
        const totalSafePct = Math.round(((socSafe + ecoSafe) / data.length) * 100);

        document.getElementById("soc-metric").innerText = `${socSafe} / ${soc.length} kunnossa`; document.getElementById("eco-metric").innerText = `${ecoSafe} / ${eco.length} rajoissa`; document.getElementById("total-metric").innerText = `${totalSafePct} %`;

        const labels = data.map(r => wrapLabel(r.name));

        const innerBgTrace = {
          type: "barpolar",
          theta: labels,
          base: data.map(() => 25),
          r: data.map(() => 71),
          marker: { color: "#f8fafc", line: { color: "#e2e8f0", width: 1 } },
          hoverinfo: "skip"
        };

        const innerDeficitTrace = {
          type: "barpolar",
          name: "Sosiaalinen vaje",
          theta: labels,
          base: data.map(r => {
            const isSafe = String(r.is_safe).toLowerCase() === "true";
            if (r.domain === "Sosiaalinen perusta" && !isSafe) {
              const pct = parseFloat(r.ratio_pct) || 100;
              const depth = Math.min(71, Math.max(22, (pct - 100) * 0.45));
              return 96 - depth;
            }
            return 96;
          }),
          r: data.map(r => {
            const isSafe = String(r.is_safe).toLowerCase() === "true";
            if (r.domain === "Sosiaalinen perusta" && !isSafe) {
              const pct = parseFloat(r.ratio_pct) || 100;
              return Math.min(71, Math.max(22, (pct - 100) * 0.45));
            }
            return 0;
          }),
          marker: { color: "#dd6b20", line: { color: "#ffffff", width: 1.5 } },
          opacity: 0.92,
          hovertemplate: data.map(r =>
            `<b>[SISÄKEHÄ: SOSIAALINEN PERUSTA]</b><br><b>${r.name}</b><br>Arvo:${r.value} ${r.unit} (Tavoiteraja:${r.threshold} ${r.unit})<br>Suhde rajaan:${r.ratio_pct} %<extra></extra>`
          )
        };

        const innerRimTrace = {
          type: "barpolar",
          theta: labels,
          base: data.map(() => 96),
          r: data.map(() => 6),
          marker: { color: "#9c4221", line: { color: "#9c4221", width: 1 } },
          hovertemplate: data.map(() => `<b>Sisäraja: Sosiaalinen perusta (100 %)</b><extra></extra>`)
        };

        const safeDoughnutTrace = {
          type: "barpolar",
          name: "Turvallinen tila (Donitsi)",
          theta: labels,
          base: data.map(() => 102),
          r: data.map(() => 56),
          marker: {
            color: data.map(r => String(r.is_safe).toLowerCase() === "true" ? "#2e7d32" : "#86efac"),
            line: { color: "#ffffff", width: 2 }
          },
          opacity: 0.95,
          hovertemplate: data.map(r =>
            `<b>[TURVALLINEN TILA – DONITSIKEHÄ]</b><br><b>${r.name}</b><br>Tila:${String(r.is_safe).toLowerCase() === "true" ? "Tavoitteessa (Vihreä)" : "Raja rikottu"}<br>Suhde rajaan: ${r.ratio_pct} %<extra></extra>`
          )
        };

        const outerRimTrace = {
          type: "barpolar",
          theta: labels,
          base: data.map(() => 158),
          r: data.map(() => 6),
          marker: { color: "#7f1d1d", line: { color: "#7f1d1d", width: 1 } },
          hovertemplate: data.map(() => `<b>Ulkoraja: Ekologinen katto (100 %)</b><extra></extra>`)
        };

        const outerOvershootTrace = {
          type: "barpolar",
          name: "Ekologinen ylitys",
          theta: labels,
          base: data.map(() => 164),
          r: data.map(r => {
            const pct = parseFloat(r.ratio_pct) || 0;
            const isSafe = String(r.is_safe).toLowerCase() === "true";
            if (r.domain === "Ekologinen katto" && !isSafe && pct > 100) {
              return Math.min(180, (pct - 100) * 0.72);
            }
            return 0;
          }),
          marker: { color: "#c62828", line: { color: "#ffffff", width: 1.5 } },
          opacity: 0.92,
          hovertemplate: data.map(r =>
            `<b>[ULKOKEHÄ: EKOLOGINEN KATTO]</b><br><b>${r.name}</b><br>Arvo:${r.value} ${r.unit} (Kestävä raja: ${r.threshold} ${r.unit})<br>Suhde rajaan:${r.ratio_pct} % (Ylitys +${(parseFloat(r.ratio_pct)-100).toFixed(1)} \%)<extra></extra>` ) };  const mainLayout = { polar: { barmode: "overlay", bargap: 0.04, radialaxis: { visible: true, range: [0, 350], showticklabels: false, ticks: "", showline: false, gridcolor: "#e2e8f0", gridwidth: 1 }, angularaxis: { type: "category", tickfont: { size: 13, color: "#1a202c" }, direction: "clockwise", gridcolor: "#e2e8f0" } }, showlegend: false, height: 660, margin: { t: 50, b: 50, l: 110, r: 110 } };  Plotly.newPlot( "doughnut-main", [innerBgTrace, innerDeficitTrace, innerRimTrace, safeDoughnutTrace, outerRimTrace, outerOvershootTrace], mainLayout, { responsive: true } );  function renderBarChart(divId, subset, overColor) { const maxRatio = Math.max(360, ...subset.map(r => (parseFloat(r.ratio_pct) \vert{}\vert{} 0) * 1.15)); const barTrace = { type: "bar", orientation: "h", y: subset.map(r => wrapLabel(r.name)), x: subset.map(r => parseFloat(r.ratio_pct) \vert{}\vert{} 0), text: subset.map(r => `${r.value} ${r.unit} (${r.ratio_pct} %)`),
            textposition: "auto",
            marker: {
              color: subset.map(r => String(r.is_safe).toLowerCase() === "true" ? "#2e7d32" : overColor)
            },
            hovertemplate: subset.map(r =>
              `<b>${r.name}</b><br>Arvo:${r.value} ${r.unit}<br>Tavoiteraja:${r.threshold} ${r.unit} (100 \%)<br>Suhde rajaan:${r.ratio_pct} %<extra></extra>`
            )
          };

          const barLayout = {
            xaxis: { title: "Suhde kestävään tavoiterajaan (100 % = raja)", range: [0, maxRatio], ticksuffix: "%" },
            yaxis: { automargin: true },
            shapes: [{
              type: "line",
              x0: 100, x1: 100,
              y0: -0.5, y1: subset.length - 0.5,
              line: { color: "#1a202c", width: 2.5, dash: "dash" }
            }],
            height: 320,
            margin: { t: 10, b: 45, l: 10, r: 30 }
          };

          Plotly.newPlot(divId, [barTrace], barLayout, { responsive: true, displayModeBar: false });
        }

        renderBarChart("chart-social", soc, "#dd6b20");
        renderBarChart("chart-eco", eco, "#c62828");

        const tbody = document.querySelector("#data-table tbody");
        data.forEach(r => {
          const isSafe = String(r.is_safe).toLowerCase() === "true";
          const isSoc = r.domain === "Sosiaalinen perusta";
          const badgeClass = isSafe ? "badge-ok" : (isSoc ? "badge-soc" : "badge-eco");
          const badgeText = isSafe ? "Vihreällä kehällä (Kunnossa)" : (isSoc ? "Sisäkehän vaje" : "Ulkokehän ylitys");
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td><strong>${isSoc ? "Sisäkehä" : "Ulkokehä"}</strong> (${r.domain})</td>
            <td><strong>${r.name}</strong></td>
            <td>${r.value}${r.unit}</td>
            <td>${r.threshold}${r.unit}</td>
            <td>${r.ratio_pct} %</td>
            <td><span class="${badgeClass}">${badgeText}</span></td>
            <td>${r.source} (${r.year})</td>
          `;
          tbody.appendChild(tr);
        });
      }
    });

    Papa.parse("doughnut_history.csv", {
      download: true,
      header: true,
      skipEmptyLines: true,
      complete: function(histResults) {
        const histData = histResults.data;
        if (!histData || histData.length === 0) return;

        const selectEl = document.getElementById("history-select");
        const uniqueIds = [];
        const idToName = {};

        histData.forEach(r => {
          if (r.id && !idToName[r.id]) {
            uniqueIds.push(r.id);
            idToName[r.id] = r.name;
          }
        });

        const allOpt = document.createElement("option");
        allOpt.value = "ALL";
        allOpt.innerText = "Kaikki mittarit rinnakkain (Suhde rajaan %)";
        selectEl.appendChild(allOpt);

        uniqueIds.forEach(id => {
          const opt = document.createElement("option");
          opt.value = id;
          opt.innerText = idToName[id];
          selectEl.appendChild(opt);
        });

        function updateHistoryChart(selectedId) {
          let traces = [];
          let yTitle = "Suhde kestävään rajaan (%)";

          if (selectedId === "ALL") {
            uniqueIds.forEach(id => {
              const rows = histData.filter(r => r.id === id);
              traces.push({
                type: "scatter",
                mode: "lines+markers",
                name: idToName[id],
                x: rows.map(r => r.period),
                y: rows.map(r => parseFloat(r.ratio_pct) || 0),
                hovertemplate: rows.map(r =>
                  `<b>${r.name}</b> (${r.period})<br>Arvo: ${r.value}${r.unit} (Raja: ${r.threshold})<br>Suhde rajaan:${r.ratio_pct} %<extra></extra>`
                )
              });
            });
          } else {
            const rows = histData.filter(r => r.id === selectedId);
            const first = rows[0] || {};
            yTitle = `${first.name} (${first.unit || ""}) & Suhde rajaan (%)`;
            traces.push({
              type: "scatter",
              mode: "lines+markers",
              name: "Suhde kestävään rajaan (%)",
              x: rows.map(r => r.period),
              y: rows.map(r => parseFloat(r.ratio_pct) || 0),
              line: { width: 3, color: first.domain === "Sosiaalinen perusta" ? "#dd6b20" : "#c62828" },
              marker: { size: 9 },
              text: rows.map(r => `${r.value}${r.unit}`),
              hovertemplate: rows.map(r =>
                `<b>${r.name}</b><br>Ajanjakso:${r.period} (${r.record_type})<br>Kunnan arvo: <b>${r.value} ${r.unit}</b> (Tavoiteraja:${r.threshold} ${r.unit})<br>Suhde rajaan:${r.ratio_pct} %<extra></extra>`
              )
            });
          }

          const histLayout = {
            xaxis: { title: "Ajanjakso (Tilastovuodet & Kuukausiseuranta YYYY-MM)", type: "category" },
            yaxis: { title: yTitle, ticksuffix: "%", rangemode: "tozero" },
            shapes: [{
              type: "line",
              xref: "paper",
              x0: 0, x1: 1,
              y0: 100, y1: 100,
              line: { color: "#2e7d32", width: 2.5, dash: "dash" }
            }],
            legend: { orientation: "h", y: -0.25 },
            height: 400,
            margin: { t: 20, b: 80, l: 60, r: 30 }
          };

          Plotly.newPlot("chart-history", traces, histLayout, { responsive: true });
        }

        selectEl.addEventListener("change", e => updateHistoryChart(e.target.value));
        updateHistoryChart("ALL");
      }
    });
  </script>
</body>
</html>
```

### Julkaisu verkossa (GitHub Pages)
1. Mene GitHub-projektisi yläreunasta kohtaan **Settings** (Asetukset) -> vasemmasta reunasta **Pages**.
2. Valitse kohdasta *Build and deployment -> Branch* pudotusvalikosta **`main`** (ja kansioksi `/(root)`) ja klikkaa **Save**.
3. Noin 30 sekunnin kuluttua sivun yläreunaan ilmestyy julkinen verkko-osoite (muodossa `https://<käyttäjätunnus>.github.io/kuntadonitsi/`).

Sivusto aukeaa välittömästi ilman minkäänlaista latausviivettä, toimii tietokoneella ja puhelimella ja päivittyy automaattisesti aina, kun GitHub Actions -robotti päivittää datatiedostot!

---

## 7. Miten muokkaan mittaristoa omalle kunnalleni?

* **Uusien automaattisten mittareiden lisääminen (`config.yaml`):** Etsi haluamasi kuntatason indikaattori osoitteesta [sotkanet.fi](https://sotkanet.fi/sotkanet/fi/haku). Katso mittarin nimen perässä suluissa oleva ID-numero (esim. `244` = sairastavuusindeksi, `181` = työttömät %, `232` = toimeentulotuki %, `182` = taloudellinen huoltosuhde) ja lisää se uutena lohkona `config.yaml`-tiedostoon.
* **Ympäristömittareiden päivittäminen (`manual_indicators.csv`):** Kuntakohtaiset kasvihuonekaasupäästöt löydät suoraan [SYKE:n päästötietopalvelusta](https://paastot.hiilineutraalisuomi.fi/). Muokkaa luvut suoraan `manual_indicators.csv`-tiedostoon.
