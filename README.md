# 🍩 Avoin Kuntadonitsi – Käyttöönotto- ja muokkausopas

Tämä tietovarasto sisältää suomalaisille kunnille suunnatun, automaattisesti päivittyvän donitsitalousmallin (Kuntadonitsin). 

Ratkaisu toimii täysin **ilmaisilla, avoimen lähdekoodin työkaluilla** suoraan GitHubin sisällä (GitHub Actions & GitHub Pages). Se ei vaadi omaa palvelinta, ulkoisia pilvipalveluita, maksullisia lisenssejä eikä ohjelmointikokemusta.

*(Oletusasetuksissa esimerkkinä on Kouvolan kaupunki, kuntakoodi `286`, mutta minkä tahansa Suomen kunnan edustaja voi ottaa mallin käyttöönsä muuttamalla kuntanumeron asetustiedostossa.)*

---

## 1. Miten järjestelmä toimii?

| Työkalu | Tehtävä tässä projektissa | Hinta |
| :--- | :--- | :--- |
| **GitHub-tietovarasto** | Säilyttää asetustiedostot, hakuskriptin, tilasto- ja historiadatan sekä verkkosivun lähdekoodin. | 0 € (Julkinen projekti) |
| **GitHub Actions** | Ajaa tiedonhaun automaattisesti kerran kuukaudessa (tai heti kun muokkaat asetuksia) ja tallentaa uudet luvut sekä aikasarjan. | 0 € |
| **Python (`fetch_data.py`)** | Hakee kuntakohtaisen datan THL:n Sotkanet-rajapinnasta, yhdistää sen ympäristömittareihin ja laskee suhdeluvut kestäviin rajoihin (`100 % = raja`). | 0 € |
| **GitHub Pages (`index.html`)** | Julkaisee interaktiivisen kuntadonitsin ja aikasarjakaaviot suoraan verkkosivuna ilman latausviiveitä. | 0 € |

---

## 2. Projektin tiedostot

Kaikki järjestelmän koodi on valmiina tämän tietovaraston tiedostoissa:

```text
kuntadonitsi/
├── config.yaml                         # MUOKATTAVA: Kunnan nimi, kuntakoodi ja Sotkanet-mittarit
├── manual_indicators.csv               # MUOKATTAVA: Kerran vuodessa päivitettävät ympäristöluvut
├── doughnut_results.csv                # (Päivittyy automaattisesti) Viimeisin tilannekuva ja aikaleima
├── doughnut_history.csv                # (Päivittyy automaattisesti) Vuosi- ja kuukausitason aikasarja
├── fetch_data.py                       # Robottiskripti, joka hakee datan ja tallentaa historian
├── index.html                          # Verkkosivun ja kaavioiden lähdekoodi
├── requirements.txt                    # Python-kirjastoriippuvuudet
└── .github/workflows/update_data.yml   # GitHub Actions -automaatioajastin
```

---

## 3. Näin otat mallin käyttöön omalle kunnallesi (4 vaihetta)

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
Avaa tiedosto `config.yaml`, klikkaa kynäkuvaketta (*Edit*) ja vaihda kuntasi nimi sekä virallinen kuntanumero (esim. Kouvola `286`, Lohja `444`, Helsinki `091`, Tampere `837`, Jyväskylä `179`):

```yaml
municipality:
  name: "Kouvola"
  statfin_code: "KU286"
  sotkanet_code: "286"
```
Kun tallennat muutoksen (**Commit changes**), GitHub Actions käynnistyy taustalla automaattisesti, hakee kuntasi tuoreet tilastot ja päivittää verkkosivun pääotsikon.

#### B) Ekologisen katon mittarit (`manual_indicators.csv`)
Avaa tiedosto `manual_indicators.csv` ja päivitä siihen kuntasi tuoreimmat ympäristöluvut (pilkulla eroteltuna). Kuntakohtaiset kasvihuonekaasupäästöt löydät suoraan [SYKE:n päästötietopalvelusta](https://paastot.hiilineutraalisuomi.fi/).

```csv
id,name,domain,source,value,threshold,unit,direction,year
hinku_paastot,Alueelliset KHK-paastot (SYKE Hinku),Ekologinen katto,SYKE Hinku,5.2,2.0,t CO2e/as.,lower_is_better,2024
```

### Vaihe 4: Julkaise verkkosivu (GitHub Pages)
1. Mene kohtaan **Settings** -> **Pages**.
2. Valitse kohdasta *Branch* pudotusvalikosta **`main`** (ja kansioksi `/(root)`) ja klikkaa **Save**.
3. Noin 30 sekunnin kuluttua sivu on julkisesti käytettävissä osoitteessa `https://<käyttäjätunnus>.github.io/kuntadonitsi/`.

---

## 4. Mittariston ja raja-arvojen muokkaaminen

### Uuden automaattisen Sotkanet-mittarin lisääminen (`config.yaml`)
THL:n Sotkanetissa on yli 3 000 kuntatason indikaattoria:
1. Etsi haluamasi kuntatason mittari osoitteesta [sotkanet.fi](https://sotkanet.fi/sotkanet/fi/haku).
2. Katso mittarin nimen perässä suluissa oleva ID-numero (esim. `244` = sairastavuusindeksi, `181` = työttömät %, `232` = toimeentulotuki %, `182` = taloudellinen huoltosuhde).
3. Lisää uusi mittari `config.yaml`-tiedoston `indicators:`-listan jatkoksi seuraavassa muodossa:

```yaml
  - id: "huoltosuhde"
    name: "Taloudellinen huoltosuhde"
    domain: "Sosiaalinen perusta"
    source: "sotkanet"
    indicator_id: 182
    threshold: 135.0
    unit: "indeksi"
    direction: "lower_is_better"
```
* **Huom:** Kohdan `direction` arvo on `"lower_is_better"` (jos pienempi arvo on parempi, esim. työttömyys tai päästöt) tai `"higher_is_better"` (jos suurempi arvo on parempi, esim. kierrätysaste tai äänestysaktiivisuus).

### Uuden manuaalisen mittarin lisääminen (`manual_indicators.csv`)
Voit lisätä uusia ekologisen katon tai paikallisen seurannan mittareita lisäämällä uuden rivin `manual_indicators.csv`-tiedostoon. Varmista, että sarakkeet on eroteltu pilkulla ja desimaalierottimena on piste (`.`).
