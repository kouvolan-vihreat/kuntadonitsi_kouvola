# 🍩 Avoin Kuntadonitsi – Käyttöönotto- ja muokkausopas

Tämä tietovarasto sisältää suomalaisille kunnille suunnatun, automaattisesti avoimista rajapinnoista päivittyvän donitsitalousmallin (Kuntadonitsin). 

Ratkaisu toimii täysin **ilmaisilla, avoimen lähdekoodin työkaluilla** suoraan GitHubin sisällä (GitHub Actions & GitHub Pages) ja hakee kaiken datan suoraan **THL:n Sotkanet-rajapinnasta** ja **SYKE:n avoimista rajapinnoista** ilman manuaalisia datatiedostoja.

*(Oletusasetuksissa esimerkkinä on Kouvolan kaupunki, kuntakoodi `286`, mutta minkä tahansa Suomen kunnan edustaja voi ottaa mallin käyttöönsä muuttamalla kuntanumeron `config.yaml`-asetustiedostossa.)*

---

## 1. Miten järjestelmä toimii?

| Työkalu | Tehtävä tässä projektissa | Hinta |
| :--- | :--- | :--- |
| **GitHub-tietovarasto** | Säilyttää asetustiedoston (`config.yaml`), hakuskriptin, tilasto- ja historiadatan sekä verkkosivun lähdekoodin. | 0 € (Julkinen projekti) |
| **GitHub Actions** | Ajaa tiedonhaun automaattisesti kerran kuukaudessa (tai heti kun muokkaat asetuksia) ja tallentaa uudet luvut sekä aikasarjan. | 0 € |
| **Python (`fetch_data.py`)** | Hakee kuntakohtaisen datan automaattisesti **THL:n Sotkanet-rajapinnasta** (sosiaalinen perusta) ja **SYKE:n avoimista rajapinnoista** (ekologinen katto). Jos jokin rajapinta ei vastaa tai dataa ei ole saatavilla, mittari merkitään arvolla `0` (`no_data`), mikä näkyy kaavioissa harmaana sektorina (*"Ei dataa saatavilla"*). | 0 € |
| **GitHub Pages (`index.html`)** | Julkaisee interaktiivisen kuntadonitsin, perustelumodaalin ja aikasarjakaaviot suoraan verkkosivuna ilman latausviiveitä. | 0 € |

---

## 2. Projektin tiedostot

Kaikki järjestelmän koodi on valmiina tämän tietovaraston tiedostoissa:

```text
kuntadonitsi/
├── config.yaml                         # AINOA MUOKATTAVA TIEDOSTO: Kunnan nimi, kuntakoodi ja rajapintamittarit
├── doughnut_results.csv                # (Päivittyy automaattisesti) Viimeisin tilannekuva ja aikaleima
├── doughnut_history.csv                # (Päivittyy automaattisesti) Vuosi- ja kuukausitason aikasarja
├── fetch_data.py                       # Robottiskripti, joka hakee Sotkanet- ja SYKE-datan ja tallentaa historian
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

### Vaihe 3: Vaihda oman kuntasi tiedot (`config.yaml`)
Avaa tiedosto `config.yaml`, klikkaa kynäkuvaketta (*Edit*) ja vaihda kuntasi nimi sekä virallinen kuntanumero (esim. Kouvola `286`, Lohja `444`, Helsinki `091`, Tampere `837`, Jyväskylä `179`):

```yaml
municipality:
  name: "Kouvola"
  statfin_code: "KU286"
  sotkanet_code: "286"
```
Kun tallennat muutoksen (**Commit changes**), GitHub Actions käynnistyy taustalla automaattisesti, hakee kuntasi tuoreet tilastot sekä THL:n Sotkanetista että SYKE:n avoimista rajapinnoista ja päivittää verkkosivun. Jos jokin rajapinta ei tarjoa tietoa kyseiselle kunnalle, se merkitään kaavioon automaattisesti nollaksi ja harmaaksi (*"Ei dataa saatavilla"*).

### Vaihe 4: Julkaise verkkosivu (GitHub Pages)
1. Mene kohtaan **Settings** -> **Pages**.
2. Valitse kohdasta *Branch* pudotusvalikosta **`main`** (ja kansioksi `/(root)`) ja klikkaa **Save**.
3. Noin 30 sekunnin kuluttua sivu on julkisesti käytettävissä osoitteessa `https://<käyttäjätunnus>.github.io/kuntadonitsi/`.

---

## 4. Upottaminen kunnan omille verkkosivuille (`<iframe>`)

Voit upottaa Kuntadonitsi-näkymän suoraan osaksi mitä tahansa verkkosivustoa (esim. WordPress, Drupal, SharePoint tai muu julkaisujärjestelmä).

Sivussa on sisäänrakennettu **upotustila (`?embed=true`)**, joka piilottaa sivun oman pääotsikon ja alatunnisteen sekä tekee taustasta läpinäkyvän, jotta näkymä sulautuu saumattomasti kunnan oman sivuston ulkoasuun:

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

## 5. Kuntatyypit ja niille suositellut mittaripaketit (Sotkanet & SYKE API)

Oletuksena käytössä olevat 8 mittaria (4 Sotkanet-mittaria ja 4 SYKE-mittaria) muodostavat **kansallisen peruspaketin**. Suomen kunnat ovat kuitenkin elinkeinorakenteeltaan, väestöltään ja ympäristöhaasteiltaan hyvin erilaisia. 

Alla olevasta taulukosta näet, miten eri kuntatyyppien kannattaa täydentää tai painottaa mittaristoaan `config.yaml`-tiedostossa:

| Kuntaprofiili ja esimerkkikunnat | Tyypilliset kestävyyspiirteet | Suositeltava mittaripaketti (`config.yaml` / SYKE & Sotkanet API) |
| :--- | :--- | :--- |
| **1. Seutukaupungit ja teollisuuspaikkakunnat**<br>*(Kouvola, Lohja, Kotka, Pori, Rauma, Hämeenlinna, Mikkeli, Kemi)* | Rakenteellinen työttömyys, väestön ikääntyminen ja kansansairaudet haastavat sosiaalista perustaa; suuri pinta-ala, tieliikenne ja teollisuus vaikuttavat ympäristöön. | **Sosiaalinen (Sotkanet API):** Peruspaketti (`244`, `181`, `232`, `182`) + *Nuorisotyöttömät (`ID 189`)* ja *Koulutuksen ulkopuolella olevat 17–24-v. (`ID 3199`)*.<br>**Ekologinen (SYKE API):** Peruspaketti (`syke_khk`, `syke_kulutus`, `syke_vesistot`, `syke_maankaytto`). |
| **2. Suuret kasvukeskukset ja yliopistokaupungit**<br>*(Helsinki, Tampere, Turku, Oulu, Jyväskylä, Kuopio, Vaasa)* | Suuri opiskelijamäärä nostaa näennäisesti toimeentulotuen saajia, mutta todellinen sosiaalinen vaje syntyy asumisen kalleudesta ja segregaatiosta. Täydennysrakentaminen luo painetta kaupunkiluonnolle. | **Sosiaalinen (Sotkanet API):** Vaihda huoltosuhde -> *Asumismenojen rasittamat asuntokunnat (`ID 3219`)* ja lisää *Pitkäaikaistyöttömien osuus (`ID 304`)*.<br>**Ekologinen (SYKE API):** Painota *Kulutusperusteista hiilijalanjälkeä (`syke_kulutus`)*, *Maankäyttöpainetta (`syke_maankaytto`)* sekä *Pienhiukkasaltistusta (`ID 3560`)*. |
| **3. Varakkaat kehyskunnat ja pendelöintikunnat**<br>*(Espoo, Kauniainen, Kirkkonummi, Pirkkala, Lempäälä, Kempele, Naantali, Sipoo)* | Työllisyys ja tulotaso ovat huippuluokkaa, jolloin perinteiset köyhyysmittarit näyttävät vihreää. Haasteina ovat nuorten henkinen kuormitus, autoiluvaltaisuus, pientalorakentamisen maankäyttö ja korkea kulutuksen hiilijalanjälki. | **Sosiaalinen (Sotkanet API):** Lisää *Nuorten kokema kohtalainen tai vaikea ahdistuneisuus (`ID 4111`)* ja *Kunnallisvaalien äänestysaktiivisuus (`ID 111`)*.<br>**Ekologinen (SYKE API):** *Kulutusperusteinen hiilijalanjälki (`syke_kulutus`)*, *Maankäyttöpaine (`syke_maankaytto`)* ja *KHK-päästöt (`syke_khk`)*. |
| **4. Maatalous- ja alkutuotantovaltaiset maaseutukunnat**<br>*(Kurikka, Kauhajoki, Nivala, Kiuruvesi, Huittinen, Loimaa, Närpiö)* | Yrittäjävetoinen työllisyys on usein hyvää, mutta alueelliset KHK-päästöt asukasta kohden sekä vesistöjen ravinnekuormitus nousevat korkeiksi valtakunnallisen ruoantuotannon vuoksi. | **Sosiaalinen (Sotkanet API):** Peruspaketti + *Työkyvyttömyyseläkettä saavat 25–64-v. (`ID 313`)*.<br>**Ekologinen (SYKE API):** Tarkastele *Pintavesien ekologista tilaa (`syke_vesistot`)* sekä *Alueellisia KHK-päästöjä (`syke_khk`)*. |
| **5. Pienet, ikääntyvät maaseutu- ja järvikunnat**<br>*(Puumala, Ilomantsi, Kuhmo, Viitasaari, Kangasniemi, Parikkala)* | Korkea eläkeläisosuus nostaa taloudellisen huoltosuhteen pysyvästi yli 200:n, vaikka työttömyys olisi matala. Keskeistä on ikäihmisten toimintakyky, palvelujen saavutettavuus ja metsä-/järviluonnon tila. | **Sosiaalinen (Sotkanet API):** Vaihda huoltosuhde (`182`) -> *Kotona asuvat 75 vuotta täyttäneet (`ID 1568`)* ja lisää *Yksinäiseksi itsensä tuntevat (`ID 4261`)*.<br>**Ekologinen (SYKE API):** *Pintavesien ravinnekuormitus (`syke_vesistot`)* ja *Maankäyttöpaine (`syke_maankaytto`)*. |
| **6. Matkailu- ja luontovetoiset kunnat**<br>*(Inari, Kittilä, Kolari, Kuusamo, Sotkamo, Hanko)* | Kausivaihtelu työllisyydessä on suurta, ja vapaa-ajan asukkaiden sekä matkailijoiden määrä moninkertaistaa kausittaisen kulutuksen vakituiseen väestöön nähden. | **Sosiaalinen (Sotkanet API):** Peruspaketti + *Asumismenojen rasittamat asuntokunnat (`ID 3219`)*.<br>**Ekologinen (SYKE API):** *Pintavesien tila (`syke_vesistot`)* ja *Luonto- ja maankäyttöpaine (`syke_maankaytto`)*. |

---

## 6. Valmiiden lisämittareiden pankki (`config.yaml`)

Voit laajentaa kuntasi donitsia (esim. 8 mittarista 10–12 mittariin) tai vaihtaa nykyisiä mittareita kopioimalla alla olevia valmiita lohkoja suoraan `config.yaml`-tiedoston `indicators:`-listaan.

*(Huom: Kaikki muutkin THL:n yli 3 000 mittarista löydät osoitteesta [sotkanet.fi](https://sotkanet.fi/sotkanet/fi/haku) – mittarin nimen perässä suluissa oleva numero on suoraan `indicator_id`.)*

### A) Sosiaalisen perustan Sotkanet-lisämittarit (`config.yaml`)

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

### B) Ekologisen katon automaattiset SYKE-rajapintamittarit (`config.yaml`)

```yaml
  # --- SYKE AVOIMET RAJAPINNAT (OLETUSPAKETTI) ---
  - id: "hinku_paastot"
    name: "Alueelliset KHK-päästöt (SYKE Hinku)"
    domain: "Ekologinen katto"
    source: "syke_khk"
    threshold: 2.0
    unit: "t CO2e/as."
    direction: "lower_is_better"

  - id: "kulutus_hiili"
    name: "Kulutusperusteinen hiilijalanjälki"
    domain: "Ekologinen katto"
    source: "syke_kulutus"
    threshold: 2.5
    unit: "t CO2e/as."
    direction: "lower_is_better"

  - id: "vesistot"
    name: "Pintavesien ravinnekuormitus"
    domain: "Ekologinen katto"
    source: "syke_vesistot"
    threshold: 100.0
    unit: "% kuormitus"
    direction: "lower_is_better"

  - id: "luonto_paine"
    name: "Maankäyttöpaine vs. lähiluonto"
    domain: "Ekologinen katto"
    source: "syke_maankaytto"
    threshold: 100.0
    unit: "% kuormitus"
    direction: "lower_is_better"

  # --- VALINNAISET SYKE-YMPÄRISTÖMITTARIT SOTKANET-RAJAPINNASTA ---
  - id: "khk_kokonais"
    name: "Kasvihuonekaasupäästöt yhteensä (SYKE / Sotkanet)"
    domain: "Ekologinen katto"
    source: "sotkanet"
    indicator_id: 4007
    threshold: 2.0
    unit: "t CO2e/as."
    direction: "lower_is_better"

  - id: "ilmanlaatu_altistus"
    name: "Pienhiukkasille altistuminen / yhdyskuntarakenne"
    domain: "Ekologinen katto"
    source: "sotkanet"
    indicator_id: 3560
    threshold: 100.0
    unit: "indeksi"
    direction: "lower_is_better"
```

---

## 7. Tekijänoikeudet ja lisenssi

* **Tekijänoikeus:** © 2026 **Mika Lammi**. Konsepti, järjestelmäarkkitehtuuri ja mittaristomäärittely: Mika Lammi (tekninen toteutus tuotettu tekoälyavusteisesti).
* **Koodin lisenssi:** Julkaistu avoimella **MIT-lisenssillä** (`SPDX-License-Identifier: MIT`). Kuntien edustajat, tutkijat ja kehittäjät voivat vapaasti kopioida, muokata ja hyödyntää tätä tietovarastoa, kunhan alkuperäinen tekijänoikeusmerkintä (`© 2026 Mika Lammi`) säilytetään osana lähdekoodia ja dokumentaatiota.
* **Tilastolähteet:** THL Sotkanet REST API ja Suomen ympäristökeskuksen (SYKE) avoimet rajapinnat (avoin viranomaisdata, CC BY 4.0).
