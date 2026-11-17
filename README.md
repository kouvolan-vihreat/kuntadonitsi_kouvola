# 🍩 Avoin Kuntadonitsi – Käyttöönotto- ja muokkausopas

Tämä tietovarasto sisältää suomalaisille kunnille suunnatun, automaattisesti avoimista viranomaisrajapinnoista päivittyvän donitsitalousmallin (Kuntadonitsin). 

Ratkaisu toimii täysin **ilmaisilla, avoimen lähdekoodin työkaluilla** suoraan GitHubin sisällä (GitHub Actions & GitHub Pages) ja hakee kaiken datan suoraan **THL:n Sotkanet-rajapinnasta**, **SYKE:n PxWeb-rajapinnasta** ja **Tilastokeskuksen StatFin-rajapinnasta** ilman manuaalisia datatiedostoja.

*(Oletusasetuksissa esimerkkinä on Kouvolan kaupunki, kuntakoodi `286`, mutta minkä tahansa Suomen kunnan edustaja voi ottaa mallin käyttöönsä muuttamalla kuntanumeron `config.yaml`-asetustiedostossa.)*

---

## 1. Miten järjestelmä toimii?

| Työkalu | Tehtävä tässä projektissa | Hinta |
| :--- | :--- | :--- |
| **GitHub-tietovarasto** | Säilyttää asetustiedoston (`config.yaml`), hakuskriptin, tilasto- ja historiadatan sekä verkkosivun lähdekoodin. | 0 € (Julkinen projekti) |
| **GitHub Actions** | Ajaa tiedonhaun automaattisesti kerran kuukaudessa (tai heti kun muokkaat asetuksia) ja tallentaa uudet luvut sekä aikasarjan. | 0 € |
| **Python (`fetch_data.py`)** | Hakee kuntakohtaisen datan automaattisesti **THL:n Sotkanet-rajapinnasta** (sosiaalinen perusta & ympäristöterveys), **SYKE:n PxWeb-rajapinnasta** (KHK- ja kulutuspäästöt) sekä **Tilastokeskuksen StatFin-rajapinnasta** (liikenteen käyttövoimat). Jos jokin rajapinta ei vastaa, mittari merkitään arvolla `0` (`no_data`), mikä näkyy kaavioissa harmaana sektorina (*"Ei dataa saatavilla"*). | 0 € |
| **GitHub Pages (`index.html`)** | Julkaisee interaktiivisen kuntadonitsin, perustelumodaalin ja aikasarjakaaviot suoraan verkkosivuna ilman latausviiveitä. | 0 € |

---

## 2. Projektin tiedostot

Kaikki järjestelmän koodi on valmiina tämän tietovaraston tiedostoissa:

```text
kuntadonitsi/
├── config.yaml                         # AINOA MUOKATTAVA TIEDOSTO: Kunnan nimi, kuntakoodi ja rajapintamittarit
├── doughnut_results.csv                # (Päivittyy automaattisesti) Viimeisin tilannekuva ja aikaleima
├── doughnut_history.csv                # (Päivittyy automaattisesti) Vuosi- ja kuukausitason aikasarja
├── fetch_data.py                       # Robottiskripti, joka hakee Sotkanet-, SYKE- ja StatFin-datan
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
Kun tallennat muutoksen (**Commit changes**), GitHub Actions käynnistyy taustalla automaattisesti, hakee kuntasi tuoreet tilastot kaikista avoimista rajapinnoista ja päivittää verkkosivun.

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

---

## 5. Kuntatyypit ja niille suositellut rajapintamittaripaketit

Oletuksena käytössä olevat 8 rajapintamittaria muodostavat **kansallisen peruspaketin**, joka on saatavilla automaattisesti kaikille Suomen 309 kunnalle:

| Kuntaprofiili ja esimerkkikunnat | Tyypilliset kestävyyspiirteet | Suositeltava mittaripaketti (`config.yaml`) |
| :--- | :--- | :--- |
| **1. Seutukaupungit ja teollisuuspaikkakunnat**<br>*(Kouvola, Lohja, Kotka, Pori, Rauma, Hämeenlinna, Mikkeli, Kemi)* | Rakenteellinen työttömyys, väestön ikääntyminen ja kansansairaudet haastavat sosiaalista perustaa; pitkät etäisyydet ja autokanta vaikuttavat päästöihin. | **Sosiaalinen:** Peruspaketti (`244`, `181`, `232`, `182`) + *Nuorisotyöttömät (`ID 189`)* ja *Koulutuksen ulkopuolella olevat 17–24-v. (`ID 3199`)*.<br>**Ekologinen:** Peruspaketti (`syke_khk`, `syke_kulutus`, `statfin_liikenne`, `sotkanet_ymparisto`). |
| **2. Suuret kasvukeskukset ja yliopistokaupungit**<br>*(Helsinki, Tampere, Turku, Oulu, Jyväskylä, Kuopio, Vaasa)* | Suuri opiskelijamäärä nostaa näennäisesti toimeentulotuen saajia, mutta todellinen sosiaalinen vaje syntyy asumisen kalleudesta ja segregaatiosta. | **Sosiaalinen:** Vaihda huoltosuhde -> *Asumismenojen rasittamat asuntokunnat (`ID 3219`)* ja lisää *Pitkäaikaistyöttömien osuus (`ID 304`)*.<br>**Ekologinen:** Painota *Kulutusperusteista hiilijalanjälkeä (`syke_kulutus`)* ja *Pienhiukkasaltistusta (`ID 3560`)*. |
| **3. Varakkaat kehyskunnat ja pendelöintikunnat**<br>*(Espoo, Kauniainen, Kirkkonummi, Pirkkala, Lempäälä, Kempele, Naantali, Sipoo)* | Työllisyys ja tulotaso ovat huippuluokkaa. Haasteina ovat nuorten henkinen kuormitus, autoiluvaltaisuus ja korkea kulutuksen hiilijalanjälki. | **Sosiaalinen:** Lisää *Nuorten kokema kohtalainen tai vaikea ahdistuneisuus (`ID 4111`)* ja *Kunnallisvaalien äänestysaktiivisuus (`ID 111`)*.<br>**Ekologinen:** *Kulutusperusteinen hiilijalanjälki (`syke_kulutus`)* ja *Fossiilikäyttöisten autojen osuus (`statfin_liikenne`)*. |
| **4. Maatalous- ja alkutuotantovaltaiset maaseutukunnat**<br>*(Kurikka, Kauhajoki, Nivala, Kiuruvesi, Huittinen, Loimaa, Närpiö)* | Yrittäjävetoinen työllisyys on usein hyvää, mutta alueelliset KHK-päästöt asukasta kohden nousevat korkeiksi alkutuotannon ja pitkien etäisyyksien vuoksi. | **Sosiaalinen:** Peruspaketti + *Työkyvyttömyyseläkettä saavat 25–64-v. (`ID 313`)*.<br>**Ekologinen:** *Alueelliset KHK-päästöt (`syke_khk`)*, *Fossiilikäyttöisten autojen osuus (`statfin_liikenne`)* ja *Talousveden laatu (`ID 3369`)*. |
| **5. Pienet, ikääntyvät maaseutu- ja järvikunnat**<br>*(Puumala, Ilomantsi, Kuhmo, Viitasaari, Kangasniemi, Parikkala)* | Korkea eläkeläisosuus nostaa taloudellisen huoltosuhteen pysyvästi yli 200:n, vaikka työttömyys olisi matala. Keskeistä on ikäihmisten toimintakyky. | **Sosiaalinen:** Vaihda huoltosuhde (`182`) -> *Kotona asuvat 75 vuotta täyttäneet (`ID 1568`)* ja lisää *Yksinäiseksi itsensä tuntevat (`ID 4261`)*.<br>**Ekologinen:** Peruspaketti (`syke_khk`, `syke_kulutus`, `statfin_liikenne`, `sotkanet_ymparisto`). |

---

## 6. Valmiiden lisämittareiden pankki (`config.yaml`)

Voit laajentaa kuntasi donitsia (esim. 8 mittarista 10–12 mittariin) tai vaihtaa nykyisiä mittareita kopioimalla alla olevia valmiita lohkoja suoraan `config.yaml`-tiedoston `indicators:`-listaan.

*(Huom: Kaikki muutkin THL:n yli 3 000 mittarista löydät osoitteesta [sotkanet.fi](https://sotkanet.fi/sotkanet/fi/haku) – mittarin nimen perässä suluissa oleva numero on suoraan `indicator_id`.)*

```yaml
  # --- SOSIAALISEN PERUSTAN LISÄMITTARIT (THL SOTKANET API) ---
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

  - id: "kotona_asuvat_75"
    name: "Kotona asuvat 75 vuotta täyttäneet"
    domain: "Sosiaalinen perusta"
    source: "sotkanet"
    indicator_id: 1568
    threshold: 92.0
    unit: "%"
    direction: "higher_is_better"

  # --- EKOLOGISEN KATON LISÄMITTARIT (SOTKANET / SYKE / STATFIN API) ---
  - id: "talousveden_laatu"
    name: "Talousveden laatuindeksi (vesihuoltolaitokset)"
    domain: "Ekologinen katto"
    source: "sotkanet"
    indicator_id: 3369
    threshold: 98.0
    unit: "%"
    direction: "higher_is_better"

  - id: "joukkoliikenne_asuminen"
    name: "Joukkoliikennevyöhykkeellä asuvien osuus (SYKE Liiteri)"
    domain: "Ekologinen katto"
    source: "sotkanet"
    indicator_id: 3218
    threshold: 50.0
    unit: "%"
    direction: "higher_is_better"
```

---

## 7. Tekijänoikeudet ja lisenssi

* **Tekijänoikeus:** © 2026 **Mika Lammi**. Konsepti, järjestelmäarkkitehtuuri ja mittaristomäärittely: Mika Lammi (tekninen toteutus tuotettu tekoälyavusteisesti).
* **Koodin lisenssi:** Julkaistu avoimella **MIT-lisenssillä** (`SPDX-License-Identifier: MIT`). Kuntien edustajat, tutkijat ja kehittäjät voivat vapaasti kopioida, muokata ja hyödyntää tätä tietovarastoa, kunhan alkuperäinen tekijänoikeusmerkintä (`© 2026 Mika Lammi`) säilytetään osana lähdekoodia ja dokumentaatiota.
* **Tilastolähteet:** THL Sotkanet REST API, Suomen ympäristökeskuksen (SYKE) PxWeb-rajapinnat ja Tilastokeskuksen StatFin-rajapinnat (avoin viranomaisdata, CC BY 4.0).
