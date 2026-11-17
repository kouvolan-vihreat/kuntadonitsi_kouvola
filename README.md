# 🍩 Avoin Kuntadonitsi – toteutusopas ja dokumentaatio

Tämä tietovarasto ja vaiheittainen opas näyttävät, kuinka rakennat mille tahansa suomalaiselle kunnalle automaattisesti päivittyvän donitsitalousmallin (Kuntadonitsin) täysin **ilmaisilla, avoimen lähdekoodin työkaluilla**. 

Toteutus ei vaadi omaa palvelinta, maksullisia ohjelmistolisenssejä eikä aiempaa syvällistä ohjelmointikokemusta – kaikki tiedostot, automaattinen tiedonhaku ja julkinen verkkosovellus pyörivät suoraan GitHubin ja Streamlitin ilmaisissa pilvipalveluissa.

*(Oletusasetuksissa esimerkkinä on Kouvolan kaupunki, kuntakoodi `286`, mutta muiden kuntien edustajat voivat vaihtaa minkä tahansa Suomen 309 kunnasta muuttamalla kuntanumeron asetustiedostossa)*

---

## 1. Mitä työkaluja käytämme ja miksi?

Ratkaisu koostuu neljästä ilmaisesta työkalusta, jotka keskustelevat keskenään automaattisesti:

| Työkalu | Mikä se on? | Mitä se tekee tässä projektissa? | Hinta |
| :--- | :--- | :--- | :--- |
| **GitHub-tietovarasto** | Pilvipohjainen kansio koodille ja tiedostoille | Säilyttää projektin asetustiedostot, hakuskriptin sekä haetun tilastodatan. | 0 € (Julkinen projekti) |
| **GitHub Actions** | GitHubin sisäänrakennettu ajastin ja automaattirobotti | Herää automaattisesti kerran kuukaudessa (tai heti kun muokkaat asetuksia), hakee tuoreet kuntaluvut THL:n Sotkanet-rajapinnasta ja tallentaa ne GitHubiin. | 0 € (2000 min/kk ilmaista ajoaikaa) |
| **Python (Pandas ja Plotly)** | Avoimen lähdekoodin ohjelmointikieli ja tilastokirjastot | Laskee suhdeluvut verrattuna kestäviin raja-arvoihin ja piirtää interaktiivisen kuntadonitsin. | 0 € (Avoin lähdekoodi) |
| **Streamlit Community Cloud** | Ilmainen julkaisualusta datanäkymille | Lukee GitHub-kansiosi ja julkaisee siitä valmiin verkkosivun, jota kuntalaiset ja päättäjät voivat selata tietokoneella tai puhelimella. | 0 € |

---

## 2. Vaihe 1: GitHub-tilin ja projektikansion luominen tai kopiointi

Voit tehdä kaikki tämän oppaan vaiheet suoraan verkkoselaimessa asentamatta mitään omalle tietokoneellesi.

### Vaihtoehto A: Kopioi tämä valmis projekti omalle kunnallesi (Suositeltu)
1. Luo ilmainen käyttäjätunnus GitHub-palveluun ja kirjaudu sisään.
2. Klikkaa tämän sivun oikeasta yläkulmasta **Fork**-painiketta, jolloin saat kaikki alla olevat tiedostot suoraan omalle GitHub-tilillesi.
3. Siirry suoraan kohtaan **Vaihe 4 (kohta 1–2)** kytkeäksesi automaattirobotin kirjoitusoikeudet päälle, ja muokkaa sen jälkeen kuntasi tiedot `config.yaml`- ja `manual_indicators.csv`-tiedostoihin.

### Vaihtoehto B: Luo projekti kokonaan alusta
1. Luo ilmainen käyttäjätunnus GitHub-palveluun ja kirjaudu sisään.
2. Klikkaa oikeasta yläkulmasta **+ (plus) -painiketta** ja valitse **New repository** (Uusi tietovarasto).
3. Anna projektille nimi kohtaan *Repository name*, esimerkiksi **kuntadonitsi**.
4. Valitse näkyvyydeksi **Public** (Julkinen). Tämä on tärkeää, jotta saat GitHub Actionsin automaattiset ajot ja Streamlit-julkaisun täysin ilmaiseksi.
5. Laita rasti ruutuun **Add a README file** ja klikkaa vihreää **Create repository** -painiketta.

Projektikansioon tulee kuusi ydintiedostoa (voit luoda uuden tiedoston klikkaamalla GitHubissa **Add file** ja **Create new file**):

```text
kuntadonitsi/
├── config.yaml                         # Kunnan nimi, kuntakoodi ja raja-arvot
├── manual_indicators.csv               # Kerran vuodessa käsin päivitettävät luvut
├── requirements.txt                    # Tarvittavat ilmaiset Python-kirjastot
├── fetch_data.py                       # Robottiskripti, joka hakee datan rajapinnoista
├── app.py                              # Verkkosivun ja donitsikaavion piirtävä koodi
└── .github/workflows/update_data.yml   # GitHubin ajastin (ajaa haun automaattisesti)
```

---

## 3. Vaihe 2: Asetustiedostojen luominen ja muokkaaminen

### 3.1 Tiedosto 1: `requirements.txt`
Klikkaa GitHubissa **Add file -> Create new file**. Kirjoita tiedoston nimeksi `requirements.txt` ja liitä sisältöön seuraavat rivit. Ne kertovat GitHubille, mitkä ilmaiset lisäosat sen tulee ladata:

```text
requests==2.31.0
pandas==2.2.0
pyyaml==6.0.1
streamlit==1.32.0
plotly==5.19.0
```
Tallenna tiedosto klikkaamalla oikeasta yläkulmasta **Commit changes...**

### 3.2 Tiedosto 2: `config.yaml` (Kunnan valinta ja varmennetut Sotkanet-indikaattorit)
Luo tai muokkaa tiedostoa nimeltä `config.yaml`. Tässä tiedostossa määrität, minkä kunnan tiedot haetaan. Jos haluat vaihtaa kuntaa (esimerkiksi Kouvolasta Lohjaan tai Tampereelle), muutat vain kuntanumeron kohtaan `sotkanet_code` (esim. Kouvola on `286`, Lohja `444`, Helsinki `091`).

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

## 6. Vaihe 5: Verkkosovelluksen (`app.py`) luominen ja julkaisu

Viimeisenä luomme tiedoston `app.py`, joka lukee valmiin datan ja piirtää interaktiivisen Kuntadonitsi-verkkosivun.

```python
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yaml

st.set_page_config(page_title="Kuntadonitsi", layout="wide")

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

muni_name = config["municipality"]["name"]
st.title(f"{muni_name}n kaupungin Kuntadonitsi")
st.markdown("Automaattisesti avoimista rajapinnoista (THL Sotkanet, SYKE) päivittyvä tilannekuva.")

df = pd.read_csv("doughnut_results.csv")

# Yhteenvetokortit
col1, col2 = st.columns(2)
soc_df = df[df["domain"] == "Sosiaalinen perusta"]
eco_df = df[df["domain"] == "Ekologinen katto"]

col1.metric("Sosiaalinen perusta tavoitteessa", f"{soc_df['is_safe'].sum()} / {len(soc_df)} mittaria")
col2.metric("Ekologinen katto rajoissa", f"{eco_df['is_safe'].sum()} / {len(eco_df)} mittaria")

# Piirretään ympyränmuotoinen kuntadonitsi (Plotly Barpolar)
fig = go.Figure()

colors = ["#2e7d32" if safe else "#c62828" for safe in df["is_safe"]]

fig.add_trace(go.Barpolar(
    r=df["ratio_pct"],
    theta=df["name"],
    marker_color=colors,
    marker_line_color="white",
    marker_line_width=2,
    opacity=0.85,
    customdata=df[["value", "unit", "threshold", "source", "year"]],
    hovertemplate=(
        "<b>%{theta}</b><br>"
        "Arvo: %{customdata[0]} %{customdata[1]} (Raja: %{customdata[2]})<br>"
        "Suhde kestävään rajaan: %{r} %<br>"
        "Lähde: %{customdata[3]} (%{customdata[4]})<extra></extra>"
    )
))

fig.update_layout(
    polar=dict(
        radialaxis=dict(visible=True, range=[0, 350], ticksuffix="%"),
        hole=0.35
    ),
    showlegend=False,
    height=650
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Lähdedata ja kynnysarvot")
st.dataframe(df[["domain", "name", "value", "unit", "threshold", "ratio_pct", "source", "year"]], use_container_width=True)
```

### Julkaisu verkossa (Streamlit Community Cloud)
1. Avaa selaimessa [Streamlit Community Cloud](https://share.streamlit.io/) ja kirjaudu sisään samalla GitHub-tunnuksellasi (*Sign in with GitHub*).
2. Klikkaa oikeasta yläkulmasta **Create app** (Luo sovellus).
3. Valitse listasta äsken luomasi **kuntadonitsi**-tietovarasto ja päähaara (`main`).
4. Valitse kohtaan *Main file path* tiedosto `app.py` ja klikkaa **Deploy!**

Noin minuutin kuluttua sinulla on valmis, julkinen verkkosivusto (esimerkiksi `kuntadonitsi.streamlit.app`), jonka voit jakaa päättäjille ja kuntalaisille tai upottaa suoraan kunnan omille verkkosivuille. Kun GitHub Actions -robotti päivittää datan kerran kuukaudessa, verkkosivu päivittyy automaattisesti ilman, että sinun tarvitsee koskea koodiin.

---

## 7. Miten muokkaan mittaristoa omalle kunnalleni?

* **Uusien automaattisten mittareiden lisääminen (`config.yaml`):** Etsi haluamasi kuntatason indikaattori osoitteesta [sotkanet.fi](https://sotkanet.fi/sotkanet/fi/haku). Katso mittarin nimen perässä suluissa oleva ID-numero (esim. `244`, `181`, `232`, `182` tai `175` = taloudellinen huoltosuhde) ja lisää se uutena lohkona `config.yaml`-tiedostoon.
* **Ympäristömittareiden päivittäminen (`manual_indicators.csv`):** Kuntakohtaiset kasvihuonekaasupäästöt löydät suoraan [SYKE:n päästötietopalvelusta](https://paastot.hiilineutraalisuomi.fi/)[cite: 1]. Muokkaa luvut suoraan `manual_indicators.csv`-tiedostoon.
