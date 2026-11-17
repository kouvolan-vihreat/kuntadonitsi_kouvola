# 🍩 Avoin Kuntadonitsi – Kuntakohtainen donitsitalouden tilannekuva

Tämä projekti on avoimen lähdekoodin työkalu, joka tuottaa automaattisesti päivittyvän **donitsitalousmalliin (Doughnut Economics)** perustuvan tilannekuvan mille tahansa suomalaiselle kunnalle. 

Järjestelmä yhdistää **sosiaalisen perustan** (asukkaiden hyvinvoinnin vähimmäistaso) ja **ekologisen katon** (luonnon kantokyvyn rajat) yhteen selkeään verkkonäkymään. Malli pyörii täysin ilmaiseksi **GitHub Actionsin** ja **Streamlit Community Cloudin** varassa ilman omaa palvelinta tai ohjelmistolisenssikuluja (0 €/v).

*(Oletusasetuksissa esimerkkinä on Kouvolan kaupunki, kuntakoodi `286`, mutta voit vaihtaa minkä tahansa Suomen 309 kunnasta muuttamalla yhden rivin asetustiedostossa!)*

---

## ⚙️ Miten järjestelmä toimii?

1. **Automaattinen rajapintahaku (`fetch_data.py`):** 
   GitHubin sisäänrakennettu automaattirobotti (**GitHub Actions**) hakee kunnan tuoreimmat sosiaalisen perustan tilastot suoraan **THL:n avoimesta Sotkanet REST API -rajapinnasta** (joka sisältää THL:n, Tilastokeskuksen ja Kelan kuntakohtaiset avainluvut).
2. **Täydentävät ympäristömittarit (`manual_indicators.csv`):** 
   Harvemmin päivittyvät ekologisen katon mittarit (kuten SYKE:n Hinku-päästölaskenta, kulutusperusteinen hiilijalanjälki, vesistökuormitus ja maankäyttöpaine) luetaan kevyestä CSV-tiedostosta, jota on helppo päivittää suoraan selaimessa kerran vuodessa.
3. **Skaalaus ja raja-arvot (`config.yaml`):** 
   Järjestelmä muuntaa eri mittayksiköt (prosentit, indeksit, hiilitonnit) yhteismitalliselle asteikolle suhteessa kestävään tavoiterajaan (**100 % = turvallisen ja oikeudenmukaisen tilan raja**).
4. **Julkinen verkkonäkymä (`app.py`):** 
   **Streamlit** ja **Plotly** piirtävät valmiista datasta (`doughnut_results.csv`) interaktiivisen kuntadonitsin ja lähdedatataulukon, joka toimii tietokoneella ja mobiililaitteilla.

---

## 📁 Projektin tiedostorakenne

```text
kuntadonitsi/
├── config.yaml                         # Kunnan nimi, kuntakoodi sekä Sotkanet-mittarit ja raja-arvot
├── manual_indicators.csv               # Kerran vuodessa päivitettävät ympäristö- ja päästömittarit
├── doughnut_results.csv                # Robottiskriptin automaattisesti koostama tulosdata
├── fetch_data.py                       # Python-skripti, joka hakee datan rajapinnoista
├── app.py                              # Streamlit-verkkosovellus ja donitsikaavion visualisointi
├── requirements.txt                    # Tarvittavat avoimen lähdekoodin Python-kirjastot
└── .github/workflows/update_data.yml   # GitHub Actions -ajastin (päivittää datan 1 krt/kk ja muokattaessa)
