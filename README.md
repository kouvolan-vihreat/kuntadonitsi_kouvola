# 🍩 Avoin Kuntadonitsi – Käyttöönotto- ja muokkausopas

Tämä tietovarasto sisältää suomalaisille kunnille suunnatun, automaattisesti avoimista viranomaisrajapinnoista päivittyvän donitsitalousmallin (**Avoin Kuntadonitsi**). 

Ratkaisu toimii täysin **ilmaisilla, avoimen lähdekoodin työkaluilla** suoraan GitHubin sisällä (GitHub Actions & GitHub Pages). Se ei vaadi omaa palvelinta, ulkoisia pilvipalveluita, maksullisia lisenssejä eikä ohjelmointikokemusta.

*(Oletusasetuksissa esimerkkinä on Kouvolan kaupunki, kuntakoodi `286`, mutta minkä tahansa Suomen kunnan edustaja voi ottaa mallin käyttöönsä muuttamalla kuntanumeron asetustiedostossa.)*

---

## 1. Miten järjestelmä toimii?

| Työkalu | Tehtävä tässä projektissa | Hinta |
| :--- | :--- | :--- |
| **GitHub-tietovarasto** | Säilyttää asetustiedostot, hakuskriptin, tilasto- ja historiadatan sekä verkkosivun lähdekoodin. | 0 € (Julkinen projekti) |
| **GitHub Actions** | Ajaa tiedonhaun automaattisesti kerran kuukaudessa (tai heti kun muokkaat asetuksia), estää päällekkäiset ajot (`concurrency`) ja tallentaa uudet luvut sekä aikasarjan. | 0 € |
| **Python (`fetch_data.py`)** | Hakee kuntakohtaisen datan automaattisesti **THL:n Sotkanet-rajapinnasta** (sosiaalinen perusta) ja **monimuuttujaisista Yhdistelmä-API-rajapinnoista** (ekologinen katto: SYKE, Tilastokeskus StatFin & JYU Lipas). Hyödyntää `manual_indicators.csv`-tiedostoa vikasietoisena varajärjestelmänä selkeällä `(CSV)`-lähdemerkinnällä ja laskee suhdeluvut kestäviin rajoihin (`100 % = 1.0x raja`). | 0 € |
| **GitHub Pages (`index.html`)** | Julkaisee interaktiivisen kuntadonitsin (tasapainotetulla `120 / 120` -kehäsuhteella), yleisen perustelumodaalin, jokaisen mittarin oman **ℹ️ Perustelut** -laskentamodaalin sekä aktiivisten mittareiden mukaan suodattuvan aikasarjakaavion. | 0 € |

---

## 2. Projektin tiedostot

Kaikki järjestelmän koodi on valmiina tämän tietovaraston tiedostoissa:

```text
kuntadonitsi/
├── config.yaml                         # MUOKATTAVA: Kunnan nimi, kuntakoodi sekä Sotkanet- ja Yhdistelmä-API-mittarit
├── manual_indicators.csv               # MUOKATTAVA: Vikasietoinen varajärjestelmä (CSV-tunnisteella) ja omat lisämittarit
├── doughnut_results.csv                # (Päivittyy automaattisesti) Viimeisin tilannekuva, lähteet ja aikaleima
├── doughnut_history.csv                # (Päivittyy automaattisesti) Vuosi- ja kuukausitason aikasarja
├── fetch_data.py                       # Robottiskripti, joka hakee rajapintadatan, laskee yhdistelmäindeksit ja päivittää historian
├── index.html                          # Verkkosivun, kaavioiden ja mittarikohtaisten perustelumodaalien lähdekoodi
├── requirements.txt                    # Python-kirjastoriippuvuudet
└── .github/workflows/update_data.yml   # GitHub Actions -automaatioajastin (sisältää concurrency-suojauksen)
