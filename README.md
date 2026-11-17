# 🍩 Avoin Kuntadonitsi – toteutusopas ja dokumentaatio

Tämä tietovarasto ja vaiheittainen opas näyttävät, kuinka rakennat mille tahansa suomalaiselle kunnalle automaattisesti päivittyvän donitsitalousmallin (Kuntadonitsin) täysin **ilmaisilla, avoimen lähdekoodin työkaluilla**. 

Toteutus ei vaadi omaa palvelinta, ulkoisia pilvipalveluita, maksullisia ohjelmistolisenssejä eikä aiempaa syvällistä ohjelmointikokemusta – kaikki tiedostot, automaattinen tiedonhaku ja salamannopea julkinen verkkosivu pyörivät **100 % suoraan GitHubin sisällä** (GitHub Actions & GitHub Pages).

*(Oletusasetuksissa esimerkkinä on Kouvolan kaupunki, kuntakoodi `286`, mutta muiden kuntien edustajat voivat vaihtaa minkä tahansa Suomen 309 kunnasta muuttamalla kuntanumeron asetustiedostossa!)*

---

## 1. Mitä työkaluja käytämme ja miksi?

Ratkaisu koostuu neljästä ilmaisesta työkalusta, jotka toimivat suoraan GitHubissa:

| Työkalu | Mikä se on? | Mitä se tekee tässä projektissa? | Hinta |
| :--- | :--- | :--- | :--- |
| **GitHub-tietovarasto (Repository)** | Pilvipohjainen kansio koodille ja tiedostoille | Säilyttää projektin asetustiedostot, hakuskriptin, tilastodatan sekä verkkosivun. | 0 € (Julkinen projekti) |
| **GitHub Actions** | GitHubin sisäänrakennettu ajastin ja automaattirobotti | Herää automaattisesti kerran kuukaudessa (tai heti kun muokkaat asetuksia), hakee tuoreet kuntaluvut THL:n Sotkanet-rajapinnasta ja tallentaa ne GitHubiin. | 0 € (2000 min/kk ilmaista ajoaikaa) |
| **Python (Pandas ja Requests)** | Avoimen lähdekoodin ohjelmointikieli ja datakirjastot | Hakee datan rajapinnoista ja laskee suhdeluvut verrattuna kestäviin raja-arvoihin. | 0 € (Avoin lähdekoodi) |
| **GitHub Pages (HTML + Plotly.js)** | GitHubin oma, välitön verkkosivujen julkaisualusta | Lukee `doughnut_results.csv`-tiedoston ja piirtää interaktiivisen kuntadonitsin välittömästi selaimeen ilman palvelimen latausviiveitä. | 0 € |

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

Projektikansioon tulee kuusi ydintiedostoa (voit luoda uuden tiedoston klikkaamalla GitHubissa **Add file** ja **Create new file**):

```text
kuntadonitsi/
├── config.yaml                         # Kunnan nimi, kuntakoodi ja raja-arvot
├── manual_indicators.csv               # Kerran vuodessa käsin päivitettävät luvut
├── requirements.txt                    # Tarvittavat ilmaiset Python-kirjastot
├── fetch_data.py                       # Robottiskripti, joka hakee datan rajapinnoista
├── index.html                          # Verkkosivu, joka piirtää interaktiivisen donitsikaavion
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
Luo tai muokkaa tiedostoa nimeltä `config.yaml`. Tässä tiedostossa määrität, minkä kunnan tiedot haetaan. Jos haluat vaihtaa kuntaa (esimerkiksi Kouvolasta Lohjaan tai Tampereelle), muutat vain kuntanumeron kohtaan `sotkanet_code` (esim. Kouvola on `286`, Lohja `444`, Helsinki `091`, Tampere `837`).

Kaikki sosiaalisen perustan mittarit haetaan luotettavasti suoraan THL:n Sotkanet-tietokannasta, joka sisältää valmiiksi sekä THL:n, Kelan että Tilastokeskuksen kuntakohtaiset avainluvut:

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

  - id: "nuorisotyottomyys"
    name: "Nuorisotyöttömät (% 18-24-v. työvoimasta)"
    domain: "Sosiaalinen perusta"
    source: "sotkanet"
    indicator_id: 182
    threshold: 10.0
    unit: "%"
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

## 4. Vaihe 3: Automaattisen tiedonhakijan (`fetch_data.py`) luominen

Luo seuraavaksi tiedosto nimeltä `fetch_data.py`. Tämä vikasietoinen skripti lukee `config.yaml`-asetuksesi, etsii valitun kunnan sisäisen Sotkanet-tunnisteen, hakee tuoreimmat vahvistetut tilastovuodet THL:n Sotkanet-rajapinnasta (pienen tauon ja automaattisen uudelleenyrityksen kera, jotta yhteys ei koskaan katkea), yhdistää ne `manual_indicators.csv`-taulukkoon, laskee suhdeluvut kestäviin rajoihin ja tallentaa valmiin tuloksen tiedostoon `doughnut_results.csv`.

```python
import time
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

def get_sotkanet_indicator_title(indicator_id):
    """Hakee indikaattorin virallisen suomenkielisen nimen suoraan Sotkanetista."""
    try:
        url = f"[https://sotkanet.fi/rest/1.1/indicators/](https://sotkanet.fi/rest/1.1/indicators/){indicator_id}"
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
    url = f"[https://sotkanet.fi/rest/1.1/json?indicator=](https://sotkanet.fi/rest/1.1/json?indicator=){indicator_id}&{years_query}&genders=total"
    
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
```

---

## 5. Vaihe 4: Automaattisen ajastuksen kytkeminen (GitHub Actions)

Nyt valjastamme GitHubin oman automaattirobotin (GitHub Actions) ajamaan yllä olevan `fetch_data.py`-skriptin automaattisesti kolmella tavalla: 1) joka kuukauden 1. päivänä, 2) heti kun muokkaat asetustiedostoja (`config.yaml` tai `manual_indicators.csv`), tai 3) milloin tahansa yhdellä napin painalluksella.

1. Mene ensin GitHub-projektisi yläreunasta kohtaan **Settings** (Asetukset) -> vasemmasta reunasta **Actions -> General**.
2. Rullaa sivun alareunaan kohtaan *Workflow permissions* ja valitse **Read and write permissions** (Luku- ja kirjoitusoikeudet). Klikkaa **Save**. Tämä antaa robotille luvan tallentaa uudet tilastoluvut takaisin kansioosi.
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
          git add doughnut_results.csv
          git diff --staged --quiet || git commit -m "Automaattinen datapaivitys"
          git push
```

**Testaa robottia heti:** Klikkaa GitHubin ylävalikosta **Actions**, valitse vasemmalta *Paivita Kuntadonitsin Data* ja klikkaa oikealta **Run workflow**. Muutamassa sekunnissa näet, kuinka robotti hakee luvut ja projektiisi ilmestyy valmis `doughnut_results.csv`-tiedosto!

---

## 6. Vaihe 5: Verkkosivun (`index.html`) luominen ja julkaisu GitHub Pagesilla

Viimeisenä luomme tiedoston `index.html`, joka lukee suoraan `doughnut_results.csv`-tiedoston ja piirtää interaktiivisen Kuntadonitsi-verkkosivun selaimeen välittömästi ilman erillisiä palvelimia.

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
  <style>
    body { font-family: Arial, sans-serif; max-width: 1100px; margin: 0 auto; padding: 20px; color: #1a202c; background: #f8fafc; }
    h1 { color: #1a365d; margin-bottom: 5px; }
    .subtitle { color: #4a5568; margin-bottom: 24px; }
    .cards { display: flex; gap: 20px; margin-bottom: 24px; flex-wrap: wrap; }
    .card { flex: 1; min-width: 240px; background: white; padding: 18px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); border-left: 5px solid #2b6cb0; }
    .card h3 { margin: 0 0 8px 0; font-size: 14px; color: #4a5568; text-transform: uppercase; }
    .card .val { font-size: 28px; font-weight: bold; color: #1a202c; }
    #chart { background: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); margin-bottom: 24px; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
    th, td { padding: 12px 14px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 14px; }
    th { background: #edf2f7; font-weight: bold; }
    .badge-ok { background: #c6f6d5; color: #22543d; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-warn { background: #fed7d7; color: #742a2a; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
  </style>
</head>
<body>

  <h1>Kuntakohtainen Kuntadonitsi</h1>
  <div class="subtitle">Automaattisesti avoimista rajapinnoista (THL Sotkanet & SYKE) päivittyvä tilannekuva</div>

  <div class="cards">
    <div class="card">
      <h3>Sosiaalinen perusta tavoitteessa</h3>
      <div class="val" id="soc-metric">- / -</div>
    </div>
    <div class="card">
      <h3>Ekologinen katto rajoissa</h3>
      <div class="val" id="eco-metric">- / -</div>
    </div>
  </div>

  <div id="chart"></div>

  <h2>Lähdedata ja kynnysarvot</h2>
  <table id="data-table">
    <thead>
      <tr>
        <th>Ulottuvuus</th>
        <th>Mittari</th>
        <th>Arvo</th>
        <th>Kestävä raja</th>
        <th>Suhde rajaan</th>
        <th>Tila</th>
        <th>Lähde (Vuosi)</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>

  <script>
    Papa.parse("doughnut_results.csv", {
      download: true,
      header: true,
      skipEmptyLines: true,
      complete: function(results) {
        const data = results.data;
        const soc = data.filter(r => r.domain === "Sosiaalinen perusta");
        const eco = data.filter(r => r.domain === "Ekologinen katto");
        const socSafe = soc.filter(r => String(r.is_safe).toLowerCase() === "true").length;
        const ecoSafe = eco.filter(r => String(r.is_safe).toLowerCase() === "true").length;

        document.getElementById("soc-metric").innerText = `${socSafe} / ${soc.length} mittaria`; document.getElementById("eco-metric").innerText = `${ecoSafe} / ${eco.length} mittaria`;  const trace = { type: "barpolar", r: data.map(r => parseFloat(r.ratio_pct) \vert{}\vert{} 0), theta: data.map(r => r.name), marker: { color: data.map(r => String(r.is_safe).toLowerCase() === "true" ? "#2e7d32" : "#c62828"), line: { color: "white", width: 2 } }, opacity: 0.85, hovertemplate: data.map(r => `<b>${r.name}</b><br>Arvo: ${r.value}${r.unit} (Raja: ${r.threshold})<br>Suhde rajaan:${r.ratio_pct} %<br>Lähde: ${r.source} (${r.year})<extra></extra>`
          )
        };

        const layout = {
          polar: {
            radialaxis: { visible: true, range: [0, 350], ticksuffix: "%" },
            hole: 0.35
          },
          showlegend: false,
          height: 600,
          margin: { t: 40, b: 40, l: 60, r: 60 }
        };

        Plotly.newPlot("chart", [trace], layout, { responsive: true });

        const tbody = document.querySelector("#data-table tbody");
        data.forEach(r => {
          const isSafe = String(r.is_safe).toLowerCase() === "true";
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${r.domain}</td>
            <td><strong>${r.name}</strong></td>
            <td>${r.value}${r.unit}</td>
            <td>${r.threshold}${r.unit}</td>
            <td>${r.ratio_pct} %</td>
            <td><span class="${isSafe ? 'badge-ok' : 'badge-warn'}">${isSafe ? 'Rajoissa' : 'Ylitys / Vaje'}</span></td>
            <td>${r.source} (${r.year})</td>
          `;
          tbody.appendChild(tr);
        });
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

Sivusto aukeaa välittömästi ilman minkäänlaista latausviivettä, toimii tietokoneella ja puhelimella ja päivittyy automaattisesti aina, kun GitHub Actions -robotti päivittää `doughnut_results.csv`-tiedoston!

---

## 7. Miten muokkaan mittaristoa omalle kunnalleni?

* **Uusien automaattisten mittareiden lisääminen (`config.yaml`):** Etsi haluamasi kuntatason indikaattori osoitteesta [sotkanet.fi](https://sotkanet.fi/sotkanet/fi/haku). Katso mittarin nimen perässä suluissa oleva ID-numero (esim. `244`, `181`, `232`, `182` tai `175` = taloudellinen huoltosuhde) ja lisää se uutena lohkona `config.yaml`-tiedostoon.
* **Ympäristömittareiden päivittäminen (`manual_indicators.csv`):** Kuntakohtaiset kasvihuonekaasupäästöt löydät suoraan [SYKE:n päästötietopalvelusta](https://paastot.hiilineutraalisuomi.fi/). Muokkaa luvut suoraan `manual_indicators.csv`-tiedostoon.
