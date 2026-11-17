# Avoin Kuntadonitsi – Ohjeet GitHub Copilotille

Tämä tietovarasto on **Avoin Kuntadonitsi** (kuntakohtainen donitsitalousmalli), joka toimii automaattisesti GitHub Actionsin ja GitHub Pagesin päällä.

## 1. Tekijänoikeus ja lisenssi
- Kaikki oikeudet, konsepti, arkkitehtuuri ja mittaristo: **© 2026 Mika Lammi** (`SPDX-License-Identifier: MIT`).
- Säilytä aina Mika Lammin tekijänoikeusmerkinnät kaikissa koodi-, konfiguraatio- ja HTML-tiedostoissa.

## 2. Arkkitehtuuri ja tiedostot (Älä riko tätä rakennetta)
- `config.yaml`: Sisältää kunnan nimen ja kuntakoodin (esim. Kouvola `286`) sekä THL Sotkanet REST API:sta haettavat sosiaalisen perustan mittarit.
- `manual_indicators.csv`: Sisältää ekologisen katon tarkistetut SYKE-mittarit (ja mahdolliset paikalliset lisämittarit).
- `fetch_data.py`: Python-skripti, joka hakee Sotkanet-datan (käyttäen selain-User-Agentia ja `/regions`-tunnistusta), yhdistää sen `manual_indicators.csv`-tietoihin ja kirjoittaa tiedostot `doughnut_results.csv` (viimeisin tilannekuva) ja `doughnut_history.csv` (aikasarja).
- `index.html`: Yksisivuinen, kevyt verkkosivu (Plotly.js). Sisältää kaksikehäisen kokonaisdonitsin, vaaka- ja aikasarjakaaviot, perustelumodaalin (`#info-modal`), lähdedatataulukon sekä `?embed=true`-upotustilan.
- `.github/workflows/update_data.yml`: GitHub Actions -työnkulku, joka ajaa `fetch_data.py`-skriptin kuukausittain ja muutosten yhteydessä sekä commitoi päivittyneet CSV-tiedostot takaisin tietovarastoon.

## 3. Tärkeät säännöt muokkauksiin
1. **Toimintavarmuus:** Älä poista `manual_indicators.csv`-tukea äläkä vaihda olemassa olevien CSV-sarakkeiden nimiä (`id,name,domain,source,value,threshold,unit,direction,year,ratio_pct,is_safe,updated_at`), jotta `index.html` ei mene rikki.
2. **Suhdelukujen laskenta (`100 % = kestävä tavoiteraja`):** Sekä sosiaalisessa perustassa että ekologisessa katossa `100 %` on kestävä raja. Arvot `<= 100 %` ovat turvallisella vihreällä kehällä (`is_safe = True`).
3. **Pidä `index.html` tiiviinä ja selkeänä:** Pidä JavaScript-koodi toimintavarmana ilman ulkoisia build-työkaluja (ei React/Webpack-riippuvuuksia), jotta sivu toimii suoraan GitHub Pagesissa.
