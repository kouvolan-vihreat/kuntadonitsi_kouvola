# 🍩 Avoin Kuntadonitsi – käyttöönotto- ja muokkausopas

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
| **GitHub Pages (`index.html`)** | Julkaisee interaktiivisen kuntadonitsin, perustelumodaalin ja aikasarjakaaviot suoraan verkkosivuna ilman latausviiveitä. | 0 € |

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
├── index.html                          # Verkkosivun, perustelumodaalin ja kaavioiden lähdekoodi
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

## 4. Upottaminen kunnan omille verkkosivuille (`<iframe>`)

Voit upottaa Kuntadonitsi-näkymän suoraan osaksi mitä tahansa verkkosivustoa (esim. WordPress, Drupal, SharePoint tai muu julkaisujärjestelmä).

Sivussa on sisäänrakennettu **upotustila (`?embed=true`)**, joka piilottaa sivun oman pääotsikon ja tekee taustasta läpinäkyvän, jotta näkymä sulautuu saumattomasti kunnan oman sivuston ulkoasuun:

```html
<iframe 
  src="https://<käyttäjätunnus>.github.io/kuntadonitsi/?embed=true" 
  width="100%" 
  height="1850" 
  style="border: none; border-radius: 12px; overflow: hidden;" 
  loading="lazy"
  title="Kuntadonitsi">
</iframe>
```
*(Jos haluat näyttää upotuksessa myös sivun oman pääotsikon ja taustavärin, jätä `?embed=true` pois osoitteen lopusta.)*

---

## 5. Kuntatyypit ja niille suositellut mittaripaketit

Oletuksena käytössä olevat 8 mittaria muodostavat **kansallisen peruspaketin**, joka on saatavilla kaikille Suomen 309 kunnalle. Suomen kunnat ovat kuitenkin elinkeinorakenteeltaan, väestöltään ja ympäristöhaasteiltaan hyvin erilaisia. 

Alla olevasta taulukosta näet, miten eri kuntatyyppien kannattaa täydentää tai painottaa mittaristoaan:

| Kuntaprofiili ja esimerkkikunnat | Tyypilliset kestävyyspiirteet | Suositeltava mittaripaketti (Peruspaketin lisäykset/vaihdot) |
| :--- | :--- | :--- |
| **1. Seutukaupungit ja teollisuuspaikkakunnat**<br>*(Kouvola, Lohja, Kotka, Pori, Rauma, Hämeenlinna, Mikkeli, Kemi)* | Rakenteellinen työttömyys, väestön ikääntyminen ja kansansairaudet haastavat sosiaalista perustaa; suuri taajama-aste ja liikenne vaikuttavat päästöihin. | **Sosiaalinen:** Peruspaketti (`244`, `181`, `232`, `182`) + *Nuorisotyöttömät (`ID 189`)* ja *Koulutuksen ulkopuolella olevat 17–24-v. (`ID 3199`)*.<br>**Ekologinen:** Peruspaketti + *Yhdyskuntajätteen kierrätysaste*. |
| **2. Suuret kasvukeskukset ja yliopistokaupungit**<br>*(Helsinki, Tampere, Turku, Oulu, Jyväskylä, Kuopio, Vaasa)* | Suuri opiskelijamäärä nostaa näennäisesti toimeentulotuen saajia, mutta todellinen sosiaalinen vaje syntyy asumisen kalleudesta, asunnottomuudesta ja alueellisesta eriytymisestä. Täydennysrakentaminen luo painetta lähiluonnolle. | **Sosiaalinen:** Vaihda huoltosuhde -> *Asumismenojen rasittamat asuntokunnat (`ID 3219`)* ja lisää *Pitkäaikaistyöttömien osuus (`ID 304`)* sekä *Pienituloisuusaste (`ID 192`)*.<br>**Ekologinen:** Painota *Kulutusperusteista hiilijalanjälkeä* ja *Viheralueiden riittävyyttä / maankäyttöpainetta*. |
| **3. Varakkaat kehyskunnat ja pendelöintikunnat**<br>*(Espoo, Kauniainen, Kirkkonummi, Pirkkala, Lempäälä, Kempele, Naantali, Sipoo)* | Työllisyys ja tulotaso ovat huippuluokkaa, jolloin perinteiset köyhyysmittarit näyttävät vihreää. Haasteina ovat nuorten henkinen kuormitus, autoiluvaltaisuus, pientalorakentamisen maankäyttö ja korkea kulutuksen hiilijalanjälki. | **Sosiaalinen:** Lisää *Nuorten kokema kohtalainen tai vaikea ahdistuneisuus (`ID 4111`)* ja *Kunnallisvaalien äänestysaktiivisuus (`ID 111`)*.<br>**Ekologinen:** Lisää `manual_indicators.csv`-tiedostoon *Henkilöautojen ajosuorite (km/as.)*. |
| **4. Maatalous- ja alkutuotantovaltaiset maaseutukunnat**<br>*(Kurikka, Kauhajoki, Nivala, Kiuruvesi, Huittinen, Loimaa, Närpiö)* | Yrittäjävetoinen työllisyys on usein hyvää, mutta alueelliset KHK-päästöt asukasta kohden sekä vesistöjen ravinnekuormitus nousevat korkeiksi valtakunnallisen ruoantuotannon vuoksi. | **Sosiaalinen:** Peruspaketti + *Työkyvyttömyyseläkettä saavat 25–64-v. (`ID 313`)*.<br>**Ekologinen:** Tarkastele Hinku-päästöjen rinnalla *Maatalouden ravinnetasetta / Pintavesien ekologista tilaa* sekä *Uusiutuvan bioenergian osuutta*. |
| **5. Pienet, ikääntyvät maaseutu- ja järvikunnat**<br>*(Puumala, Ilomantsi, Kuhmo, Viitasaari, Kangasniemi, Parikkala)* | Korkea eläkeläisosuus nostaa taloudellisen huoltosuhteen pysyvästi yli 200:n, vaikka työttömyys olisi matala. Keskeistä on ikäihmisten toimintakyky, palvelujen saavutettavuus ja metsä-/järviluonnon tila. | **Sosiaalinen:** Vaihda huoltosuhde (`182`) -> *Kotona asuvat 75 vuotta täyttäneet (`ID 1568`)* ja lisää *Yksinäiseksi itsensä tuntevat (`ID 4261`)*.<br>**Ekologinen:** *Pintavesien ravinnekuormitus* ja *Metsien hakkuiden suhde kasvuun*. |
| **6. Matkailu- ja luontovetoiset kunnat**<br>*(Inari, Kittilä, Kolari, Kuusamo, Sotkamo, Hanko)* | Kausivaihtelu työllisyydessä on suurta, ja vapaa-ajan asukkaiden sekä matkailijoiden määrä moninkertaistaa kausittaisen jäte-, vesi- ja liikennekulutuksen vakituiseen väestöön nähden. | **Sosiaalinen:** Peruspaketti + *Asumisen ahtaus / kausiasuntojen saatavuus*.<br>**Ekologinen:** Lisää `manual_indicators.csv`-tiedostoon *Matkailupainotettu jäte- ja vedenkulutus* sekä *Suojelualueiden ja reitistöjen kulumispaine*. |

---

## 6. Valmiiden lisämittareiden pankki (`config.yaml` & `manual_indicators.csv`)

Voit laajentaa kuntasi donitsia (esim. 8 mittarista 10–12 mittariin) tai vaihtaa nykyisiä mittareita kopioimalla alla olevia valmiita lohkoja suoraan `config.yaml`- tai `manual_indicators.csv`-tiedostoosi.

*(Huom: Kaikki muutkin THL:n yli 3 000 mittarista löydät osoitteesta [sotkanet.fi](https://sotkanet.fi/sotkanet/fi/haku) – mittarin nimen perässä suluissa oleva numero on suoraan `indicator_id`.)*

### A) Valmiit Sotkanet-lisämittarit (`config.yaml` -> `indicators:`-listaan)

```yaml
  # --- NUORET, KOULUTUS JA MIELENTERVEYS ---
  - id: "nuorisotyottomyys"
    name: "Nuorisotyöttömät (% 18-24-v. työvoimasta)"
    domain: "Sosiaalinen perusta"
    source: "sotkanet"
    indicator_id: 189
    threshold: 10.0
    unit: "%"
    direction: "lower_is_better"

  - id: "koulutuksen_ulkopuolella"
    name: "Koulutuksen ulkopuolelle jääneet 17-24-vuotiaat"
    domain: "Sosiaalinen perusta"
    source: "sotkanet"
    indicator_id: 3199
    threshold: 6.5
    unit: "%"
    direction: "lower_is_better"

  - id: "nuorten_ahdistuneisuus"
    name: "Kohtalainen tai vaikea ahdistuneisuus (8.-9. lk)"
    domain: "Sosiaalinen perusta"
    source: "sotkanet"
    indicator_id: 4111
    threshold: 12.0
    unit: "%"
    direction: "lower_is_better"

  # --- ASUMINEN, TULOEROT JA PITKÄAIKAISTYÖTTÖMYYS (KASVUKESKUKSET) ---
  - id: "asumismenot"
    name: "Asumismenojen rasittamat asuntokunnat"
    domain: "Sosiaalinen perusta"
    source: "sotkanet"
    indicator_id: 3219
    threshold: 7.0
    unit: "%"
    direction: "lower_is_better"

  - id: "pitkaaikaistyottomyys"
    name: "Pitkäaikaistyöttömien osuus työttömistä"
    domain: "Sosiaalinen perusta"
    source: "sotkanet"
    indicator_id: 304
    threshold: 25.0
    unit: "%"
    direction: "lower_is_better"

  - id: "pienituloisuus"
    name: "Pienituloisuusaste (asuntoväestö)"
    domain: "Sosiaalinen perusta"
    source: "sotkanet"
    indicator_id: 192
    threshold: 11.0
    unit: "%"
    direction: "lower_is_better"

  # --- IKÄIHMISET, TYÖKYKY JA OSALLISUUS (MAASEUTU- JA SEUTUKUNNAT) ---
  - id: "kotona_asuvat_75"
    name: "Kotona asuvat 75 vuotta täyttäneet"
    domain: "Sosiaalinen perusta"
    source: "sotkanet"
    indicator_id: 1568
    threshold: 92.0
    unit: "%"
    direction: "higher_is_better"

  - id: "tyokyvyttomyyselake"
    name: "Työkyvyttömyyseläkettä saavat 25-64-vuotiaat"
    domain: "Sosiaalinen perusta"
    source: "sotkanet"
    indicator_id: 313
    threshold: 6.5
    unit: "%"
    direction: "lower_is_better"

  - id: "aanestysaktiivisuus"
    name: "Äänestysaktiivisuus kuntavaaleissa"
    domain: "Sosiaalinen perusta"
    source: "sotkanet"
    indicator_id: 111
    threshold: 60.0
    unit: "%"
    direction: "higher_is_better"
```

### B) Valmiit ekologiset lisämittarit (`manual_indicators.csv`-tiedostoon)

Voit lisätä esimerkiksi seuraavat paikalliset ympäristömittarit `manual_indicators.csv`-tiedostoon (muuta sarake `value` vastaamaan oman kuntasi arvoa):

```csv
kierratysaste,Yhdyskuntajatteen kierratysaste,Ekologinen katto,Jateyhtio / SYKE,48.0,65.0,%,higher_is_better,2024
vedenkulutus,Ominaisvedenkulutus (l/as./vrk),Ekologinen katto,Kunnan vesilaitos,125.0,110.0,l/vrk,lower_is_better,2024
ajosuorite,Henkiloautojen ajosuorite asukasta kohti,Ekologinen katto,Traficom / Liiteri,6800.0,4500.0,km/as.,lower_is_better,2024
metsahakkuut,Metsien hakkuiden suhde vuotuiseen kasvuun,Ekologinen katto,Luke,82.0,70.0,%,lower_is_better,2024
```
