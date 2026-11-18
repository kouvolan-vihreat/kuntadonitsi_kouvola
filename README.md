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

* **`config.yaml`** – *Muokattava:* Kunnan nimi, kuntakoodi sekä sisä- ja ulkokehän mittareiden asetukset.
* **`manual_indicators.csv`** – *Muokattava:* Vikasietoinen varajärjestelmä (`(CSV)`-tunnisteella) sekä käyttäjän omat paikalliset lisämittarit.
* **`doughnut_results.csv`** – *Päivittyy automaattisesti:* Viimeisin tilannekuva, suhdeluvut, tietolähteet ja päivitysaikaleima.
* **`doughnut_history.csv`** – *Päivittyy automaattisesti:* Vuosi- ja kuukausitason aikasarjadata.
* **`fetch_data.py`** – Robottiskripti, joka hakee rajapintadatan, laskee yhdistelmäindeksit ja päivittää tulostiedostot.
* **`index.html`** – Verkkosivun, kaavioiden ja mittarikohtaisten perustelumodaalien lähdekoodi.
* **`requirements.txt`** – Python-kirjastoriippuvuudet.
* **`.github/workflows/update_data.yml`** – GitHub Actions -automaatioajastin ja päällekkäisten ajojen esto.

---

## 3. Arkkitehtuurin ja visualisoinnin keskeiset ominaisuudet

1. **Tasapainotetut kehäsuhteet (`120 / 120` sädeyksikköä):**
   * Sisäkehän sosiaalisille vajeille ja ulkokehän ekologisille ylityksille on varattu täsmälleen yhtä suuri säteittäinen tila (`120` yksikköä) ja identtinen skaalauskerroin (`0.60` / %) vihreän turvallisen tilan kehän molemmin puolin. Näin sosiaalinen perusta ja ekologinen katto saavat yhtä suuren visuaalisen painoarvon.
2. **Monimuuttujaiset Yhdistelmä-APIt ulkokehällä:**
   * Koska kaikkia kuntatason ekologisia mittareita ei julkaista yhdessä yksittäisessä rajapinnassa, `fetch_data.py` muodostaa ulkokehän mittareille painotetut yhdistelmäindeksit useasta viranomaisrajapinnasta (THL Sotkanet, SYKE, Tilastokeskus StatFin ja Jyväskylän yliopiston Lipas REST API).
3. **100 % läpinäkyvät lähdemerkinnät ja mittarikohtaiset `ℹ️ Perustelut` -ikkunat:**
   * Alataulukossa on oma **`Perustelut`**-sarakkeensa, jonka painikkeista avautuu jokaiselle mittarille (sekä sisä- että ulkokehällä) yksilöllinen modaali-ikkuna. Ikkuna näyttää reaaliaikaisen arvon, kynnysarvon, suhdeluvun sekä tarkan laskentakaavan ja osa-alueet.
   * Jos jokin rajapinta ei vastaa ja arvo luetaan `manual_indicators.csv`-varatiedostosta, lähdesarakkeeseen merkitään automaattisesti **`(CSV)`** (esim. `SYKE Hinku (CSV)`).
4. **Automaattisesti suodattuva aikasarjakaavio:**
   * Aikasarjakaavio suodattaa `doughnut_history.csv`-tiedoston rivit automaattisesti `doughnut_results.csv`-tiedostossa olevien aktiivisten mittareiden perusteella. Jos poistat tai vaihdat mittarin asetuksista, se poistuu heti valikosta ilman, että historiatiedostoa tarvitsee tyhjentää käsin.

---

## 4. Mittariston tietolähteet ja Yhdistelmä-API-laskentakaavat

Kaikki mittarit on normalisoitu siten, että **`100 % (1.0x)`** vastaa kestävää tavoiterajaa. Arvot **`≤ 100 % (≤ 1.0x)`** ovat tavoitetilassa vihreällä kehällä.

### A) Sisäkehä: Sosiaalinen perusta (Suora THL Sotkanet REST API)

| Mittari (`id`) | Rajapintalähde | Laskentaperuste ja kuvaus | Kestävä raja (`100 % = 1.0x`) |
| :--- | :--- | :--- | :--- |
| **Kansanterveys (THL sairastavuusindeksi)** (`sairastavuus`) | `SOTKANET API (ID 244)` | Ikävakioitu kokonaisindeksi, joka yhdistää 7 vakavaa kansansairausryhmää (syövät, sepelvaltimotauti, aivoverisuonisairaudet, tuki- ja liikuntaelinsairaudet, mielenterveys, tapaturmat ja muistisairaudet). | **`100.0 indeksi`**<br>*(Koko maan keskiarvo = 100)* |
| **Työttömien osuus työvoimasta** (`tyottomyys`) | `SOTKANET API (ID 181)` | TEM:n työnvälitystilaston mukainen työttömien työnhakijoiden osuus työvoimasta (%). Kuvaa elinvoimaa ja taloudellista osallisuutta. | **`8.0 %`**<br>*(Kestävän työllisyyden viiteraja)* |
| **Toimeentulotukea saaneet asukkaat** (`toimeentulotuki`) | `SOTKANET API (ID 232)` | Kelan ja THL:n rekisterin mukainen varsinaista tai ehkäisevää toimeentulotukea vuoden aikana saaneiden henkilöiden osuus asukkaista (%). | **`6.0 %`**<br>*(Perusturvan riittävyyden raja)* |
| **Taloudellinen huoltosuhde** (`huoltosuhde`) | `SOTKANET API (ID 182)` | Tilastokeskuksen työssäkäyntitilasto: ei-työllisten asukkaiden määrä 100 työssäkäyvää kohden (`((Väkiluku − Työlliset) / Työlliset) × 100`). | **`135.0 indeksi`**<br>*(Kestävä veropohja ja huoltosuhde)* |

### B) Ulkokehä: Ekologinen katto (Monimuuttujaiset Yhdistelmä-APIt & SYKE CSV-varajärjestelmä)

| Mittari (`id`) | Ensisijainen Yhdistelmä-API & Varalähde | Monimuuttujainen laskentakaava ja painokertoimet | Kestävä raja (`100 % = 1.0x`) |
| :--- | :--- | :--- | :--- |
| **Alueelliset KHK-päästöt** (`hinku_paastot`) | 1. `SYKE / Sotkanet API (ID 4007)`<br>2. `Yhdistelmä-API (ID 3218 + 3560 + 184)`<br>3. *Varalla:* `SYKE Hinku (CSV)` | **Jos suora `ID 4007` ei vastaa, lasketaan 3 osa-indikaattorista:**<br>• **45 % Liikenne ja yhdyskuntarakenne (`ID 3218`):** `3.2 + ((100 − J_osuus) / 100) × 3.0`<br>• **35 % Paikallinen lämmitys ja poltto (`ID 3560`):** `(PM2.5 / 5.0) × 4.6`<br>• **20 % Aluelaajuus ja maatalous (`ID 184`/`182`):** `5.4 − (Tiheys / 200) × 1.5` | **`2.0 t CO2e/as.`**<br>*(Hinku-kuntien -80 % tavoitetaso)* |
| **Kulutusperusteinen hiilijalanjälki** (`kulutus_hiili`) | 1. `Yhdistelmä-API (ID 181 + 3218 + 182)`<br>2. *Varalla:* `SYKE Kulutus (CSV)` | **ENVIMAT-mallin mukainen painotettu yhdistelmä:**<br>• **40 % Ostovoima ja yksityinen kulutus (`ID 181`):** `9.4 − (Työttömyys_% × 0.09)`<br>• **35 % Liikkumistarve ja etäisyydet (`ID 3218`):** `6.8 + ((100 − J_osuus) / 100) × 2.6`<br>• **25 % Asumisväljyys ja palvelurakenne (`ID 182`):** `7.4 + ((Huoltosuhde − 135) / 100) × 2.2` | **`2.5 t CO2e/as.`**<br>*(Pariisin 1,5 °C globaali budjetti)* |
| **Vesistö- ja ravinnekuormitus** (`vesistot`) | 1. `Yhdistelmä-API (ID 3218 + 3560 + 182)`<br>2. *Varalla:* `SYKE Vesikartta (CSV)` | **Valuma-alueen ja pintavesien kuormitusindeksi:**<br>• **45 % Hajakuormitus ja peltovalumat (`ID 3218`):** `95.0 + (100 − J_osuus) × 0.52`<br>• **30 % Ympäristö- ja laskeumakuormitus (`ID 3560`):** `(PM2.5 / 4.2) × 100`<br>• **25 % Alueellinen vesistörakenne (`ID 182`):** `110.0 + ((Huoltosuhde − 135) / 100) × 32.0` | **`100.0 % kuormitus`**<br>*(EU:n vesipuitedirektiivin hyvä tila)* |
| **Maankäyttöpaine vs. lähiluonto** (`luonto_paine`) | 1. `Yhdistelmä-API (ID 676 + 3218 + 3560 + Lipas API)`<br>2. *Varalla:* `SYKE Liiteri (CSV)` | **Rakennetun ympäristön ja lähiluonnon suhde:**<br>• **40 % Taajama-aste (`ID 676` / StatFin `11ra`):** `(Taajama_aste / 80.0) × 100`<br>• **25 % Yhdyskuntarakenteen hajautuminen (`ID 3218`):** `60.0 + (100 − J_osuus) × 0.55`<br>• **20 % Lähiympäristön hiukkaskuormitus (`ID 3560`):** `(PM2.5 / 5.5) × 100`<br>• **15 % Virkistys- ja luontokohteet (`JYU Lipas API`):** `(75.0 / max(30, N_kohteet)) × 100` | **`100.0 % kuormitus`**<br>*(Lähiluonnon kantokykyraja)* |

---

## 5. Näin otat mallin käyttöön omalle kunnallesi (4 vaihetta)

Voit tehdä kaikki käyttöönoton vaiheet suoraan verkkoselaimessa.

### Vaihe 1: Kopioi projekti omalle GitHub-tilillesi (Fork)
1. Kirjaudu sisään GitHubiin ja klikkaa tämän sivun oikeasta yläkulmasta **Fork** -> **Create fork**.
2. Pidä tietovarasto julkisena (**Public**), jotta GitHub Actions ja GitHub Pages toimivat ilmaiseksi.

### Vaihe 2: Kytke automaattirobotin oikeudet päälle
1. Mene kopioimasi projektin ylävalikosta kohtaan **Settings** -> **Actions** -> **General**.
2. Valitse sivun alareunasta kohdasta *Workflow permissions* vaihtoehto **Read and write permissions** ja klikkaa **Save**.
3. Avaa ylävalikosta **Actions**-välilehti ja klikkaa vihreää painiketta **I understand my workflows, go ahead and enable them**.

### Vaihe 3: Vaihda oman kuntasi tiedot (`config.yaml` ja `manual_indicators.csv`)

#### A) Kunnan nimi ja numero (`config.yaml`)
Avaa tiedosto `config.yaml`, klikkaa kynäkuvaketta (*Edit*) ja vaihda kuntasi nimi sekä virallinen kuntanumero (esim. Kouvola `286`, Lohja `444`, Helsinki `091`, Tampere `837`, Jyväskylä `179`, Hamina `075`):

```yaml
municipality:
  name: "Kouvola"
  statfin_code: "KU286"
  sotkanet_code: "286"
