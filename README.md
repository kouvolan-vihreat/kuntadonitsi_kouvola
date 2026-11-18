# 🍩 Avoin Kuntadonitsi – Käyttöönotto- ja muokkausopas

Tämä tietovarasto sisältää suomalaisille kunnille suunnatun, automaattisesti päivittyvän donitsitalousmallin eli Kuntadonitsin.

Ratkaisu toimii täysin **ilmaisilla, avoimen lähdekoodin työkaluilla** suoraan GitHubin sisällä (GitHub Actions & GitHub Pages) ilman omaa palvelinta, ulkoisia pilvipalveluita, maksullisia lisenssejä tai ohjelmointikokemusta.

*(Oletusasetuksissa esimerkkinä on Kouvolan kaupunki, kuntakoodi `286`. Minkä tahansa kunta voi ottaa mallin käyttöönsä vaihtamalla kunnan nimen ja kuntakoodin `config.yaml`-tiedostoon.)*

---

## 1. Miten järjestelmä toimii?

| Työkalu | Tehtävä tässä projektissa | Hinta |
| :--- | :--- | :--- |
| **GitHub-tietovarasto** | Säilyttää asetustiedostot, hakuskriptin, tilasto- ja historiadatan sekä verkkosivun lähdekoodin. | 0 € (Julkinen projekti) |
| **GitHub Actions** | Ajaa tiedonhaun automaattisesti kerran kuukaudessa (tai heti asetuksia muokattaessa) ja tallentaa uudet luvut sekä aikasarjan. | 0 € |
| **Python (`fetch_data.py`)** | Tunnistaa kunnan automaattisesti, hakee **sisäkehän** tiedot THL:n Sotkanet REST API:sta ja laskee **ulkokehän** aikasarjat (alkaen 2018) monimuuttujaisilla Yhdistelmä-API-malleilla (SYKE / Sotkanet, Tilastokeskus & JYU Lipas REST API). Hyödyntää `manual_indicators.csv`-tiedostoa vikasietoisena varajärjestelmänä ja normalisoi luvut kestäviin rajoihin (`100 % = 1.0x`). | 0 € |
| **GitHub Pages (`index.html`)** | Julkaisee interaktiivisen kuntadonitsin, rinnakkaiset kehäkaaviot, mittarikohtaiset perustelumodaalit ja aikasarjaseurannan suoraan verkkosivuna. | 0 € |

*(Oletusmittareiden tarkat laskentakaavat, painoarvot ja rajapintakomponentit on dokumentoitu suoraan `fetch_data.py`-skriptiin sekä verkkosivun **ℹ️ Perustelut** -modaaleihin.)*

---

## 2. Projektin tiedostot

```text
kuntadonitsi/
├── config.yaml                         # MUOKATTAVA: Kunnan nimi, kuntakoodit sekä rajapintamittarit
├── manual_indicators.csv               # MUOKATTAVA: Varajärjestelmä (fallback) ja omat paikalliset lisämittarit
├── doughnut_results.csv                # (Päivittyy automaattisesti) Viimeisin tilannekuva ja päivitysaikaleima
├── doughnut_history.csv                # (Päivittyy automaattisesti) Vuositilastot (2018–) ja kuukausiseuranta (YYYY-MM)
├── fetch_data.py                       # Tiedonhaku- ja laskentaskripti
├── index.html                          # Verkkosivun, Plotly-kaavioiden ja perustelumodaalien lähdekoodi
├── requirements.txt                    # Python-kirjastoriippuvuudet
└── .github/workflows/update_data.yml   # GitHub Actions -automaatioajastin
```

---

## 3. Näin otat mallin käyttöön omalle kunnallesi (4 vaihetta)

Voit tehdä kaikki käyttöönoton vaiheet suoraan verkkoselaimessa.

### Vaihe 1: Kopioi projekti omalle GitHub-tilillesi (Fork)
1. Kirjaudu sisään GitHubiin ja klikkaa sivun oikeasta yläkulmasta **Fork** -> **Create fork**.
2. Pidä tietovarasto julkisena (**Public**), jotta GitHub Actions ja GitHub Pages toimivat ilmaiseksi.

### Vaihe 2: Kytke automaattirobotin oikeudet päälle
1. Mene kopioimasi projektin ylävalikosta kohtaan **Settings** -> **Actions** -> **General**.
2. Valitse sivun alareunasta kohdasta *Workflow permissions* vaihtoehto **Read and write permissions** ja klikkaa **Save**.
3. Avaa ylävalikosta **Actions**-välilehti ja klikkaa vihreää painiketta **I understand my workflows, go ahead and enable them**.

### Vaihe 3: Vaihda oman kuntasi tiedot (`config.yaml` ja `manual_indicators.csv`)

#### A) Kunnan nimi, kuntakoodi ja rajapintamittarit (`config.yaml`)
Avaa `config.yaml`, klikkaa kynäkuvaketta (*Edit*) ja vaihda kuntasi nimi sekä 3-numeroinen virallinen kuntakoodi (esim. Kouvola `286`, Lohja `444`, Helsinki `091`, Tampere `837`, Jyväskylä `179`). Hakuskripti selvittää vastaavan Sotkanet-alue-ID:n automaattisesti:

```yaml
municipality:
  name: "Kouvola"
  statfin_code: "KU286"
  sotkanet_code: "286"
```

Kun tallennat muutoksen (**Commit changes**), GitHub Actions käynnistyy automaattisesti, hakee kuntasi tilastot (4 Sotkanet-mittaria + 4 Yhdistelmä-API-mittaria) ja päivittää verkkosivun.

#### B) Varajärjestelmä ja omat paikalliset lisämittarit (`manual_indicators.csv`)
Tiedostolla `manual_indicators.csv` on kaksi tehtävää:
1. **Automaattinen varajärjestelmä (Fallback):** Jos jonkin `config.yaml`-mittarin rajapinta ei vastaa, `fetch_data.py` hakee arvon samalla `id`:llä tästä tiedostosta ja merkitsee verkkosivun lähdesarakkeeseen tunnisteen `(CSV)`.
2. **Omat paikalliset lisämittarit:** Jos lisäät tiedostoon uusia rivejä (joiden `id` ei ole `config.yaml`-tiedostossa), ne nousevat automaattisesti mukaan donitsikaavioihin ja saavat yleisen perusteluikkunan lähdedatataulukkoon.

Sarakkeiden muoto (`direction` on joko `lower_is_better` tai `higher_is_better`):

```csv
id,name,domain,source,value,threshold,unit,direction,year
```

### Vaihe 4: Julkaise verkkosivu (GitHub Pages)
1. Mene kohtaan **Settings** -> **Pages**.
2. Valitse kohdasta *Branch* pudotusvalikosta **`main`** (kansio `/(root)`) ja klikkaa **Save**.
3. Noin 30 sekunnin kuluttua sivu on julkisesti käytettävissä osoitteessa `https://<käyttäjätunnus>.github.io/kuntadonitsi/`.

---

## 4. Upottaminen verkkosivuille (`<iframe>`)

Voit upottaa Kuntadonitsi-näkymän osaksi mitä tahansa julkaisujärjestelmää (esim. WordPress, Drupal, SharePoint).

Parametri **`?embed=true`** piilottaa sivun oman pääotsikon, alaotsikon ja alatunnisteen sekä muuttaa taustan läpinäkyväksi:

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

Oletuksena käytössä olevat 8 mittaria (`config.yaml`) muodostavat **kansallisen peruspaketin**, joka toimii automaattisesti kaikille Suomen kunnille. Alla olevasta taulukosta näet, miten eri kuntatyyppien kannattaa täydentää mittaristoaan **Sotkanet-rajapinnan** (`config.yaml`) ja **paikallisten mittareiden** (`manual_indicators.csv`) avulla:

| Kuntaprofiili ja esimerkkikunnat | Tyypilliset kestävyyspiirteet | Suositellut täydennykset (`config.yaml` & `manual_indicators.csv`) |
| :--- | :--- | :--- |
| **1. Seutukaupungit ja teollisuuspaikkakunnat**<br>*(Kouvola, Lohja, Kotka, Pori, Rauma, Hämeenlinna, Mikkeli, Kemi)* | Rakenteellinen työttömyys, väestön ikääntyminen ja kansansairaudet haastavat sosiaalista perustaa; laaja pinta-ala, tieliikenne ja teollisuus vaikuttavat ympäristöön. | **Sosiaalinen (`config.yaml`):** Peruspaketti + *Nuorisotyöttömät (`ID 189`)* ja *Koulutuksen ulkopuolella olevat 17–24-v. (`ID 3199`)*.<br>**Ekologinen (`manual_indicators.csv`):** *Yhdyskuntajätteen kierrätysaste* ja *Tieliikenteen päästöosuus*. |
| **2. Suuret kasvukeskukset ja yliopistokaupungit**<br>*(Helsinki, Tampere, Turku, Oulu, Jyväskylä, Kuopio, Vaasa)* | Opiskelijamäärä nostaa toimeentulotuen saajia, mutta keskeinen sosiaalinen vaje syntyy asumisen kalleudesta ja pitkäaikaistyöttömyydestä. Täydennysrakentaminen kuormittaa kaupunkiluontoa. | **Sosiaalinen (`config.yaml`):** Vaihda huoltosuhde -> *Asumismenojen rasittamat asuntokunnat (`ID 3219`)* ja lisää *Pitkäaikaistyöttömien osuus (`ID 304`)*.<br>**Ekologinen (`config.yaml` / `CSV`):** *Joukkoliikennevyöhykkeellä asuvien osuus (`ID 3218`)* ja *Kaupunkiluonnon suojeluosuus*. |
| **3. Varakkaat kehyskunnat ja pendelöintikunnat**<br>*(Espoo, Kauniainen, Kirkkonummi, Pirkkala, Lempäälä, Kempele, Naantali, Sipoo)* | Työllisyys ja tulotaso ovat korkeita, mutta haasteina ovat nuorten henkinen kuormitus, autoiluvaltaisuus, pientalorakentamisen maankäyttö ja korkea kulutuksen hiilijalanjälki. | **Sosiaalinen (`config.yaml`):** Lisää *Nuorten kokema kohtalainen tai vaikea ahdistuneisuus (`ID 4111`)* ja *Kuntavaalien äänestysaktiivisuus (`ID 111`)*.<br>**Ekologinen (`manual_indicators.csv`):** *Henkilöautojen ajosuorite asukasta kohti*. |
| **4. Maatalous- ja alkutuotantovaltaiset maaseutukunnat**<br>*(Kurikka, Kauhajoki, Nivala, Kiuruvesi, Huittinen, Loimaa, Närpiö)* | Yrittäjävetoinen työllisyys on hyvää, mutta alueelliset KHK-päästöt asukasta kohden sekä vesistöjen ravinnekuormitus nousevat korkeiksi valtakunnallisen ruoantuotannon vuoksi. | **Sosiaalinen (`config.yaml`):** Peruspaketti + *Työkyvyttömyyseläkettä saavat 25–64-v. (`ID 313`)*.<br>**Ekologinen (`config.yaml` / `CSV`):** *KHK-päästöt yhteensä (`ID 4007`)* sekä paikallinen *Uusiutuvan energian tuotanto-osuus*. |
| **5. Pienet, ikääntyvät maaseutu- ja järvikunnat**<br>*(Puumala, Ilomantsi, Kuhmo, Viitasaari, Kangasniemi, Parikkala)* | Korkea eläkeläisosuus nostaa taloudellisen huoltosuhteen pysyvästi yli 200:n, vaikka työttömyys olisi matala. Keskeistä on ikäihmisten toimintakyky sekä metsä- ja järviluonnon tila. | **Sosiaalinen (`config.yaml`):** Vaihda huoltosuhde (`182`) -> *Kotona asuvat 75 vuotta täyttäneet (`ID 1568`)* ja lisää *Pienituloisuusaste (`ID 192`)*.<br>**Ekologinen (`manual_indicators.csv`):** *Suojelualueiden osuus* ja *Metsien hakkuiden suhde kasvuun*. |
| **6. Matkailu- ja luontovetoiset kunnat**<br>*(Inari, Kittilä, Kolari, Kuusamo, Sotkamo, Hanko)* | Kausivaihtelu työllisyydessä on suurta, ja matkailijat sekä vapaa-ajan asukkaat moninkertaistavat kausittaisen vesi-, jäte- ja liikennekulutuksen vakituiseen väestöön nähden. | **Sosiaalinen (`config.yaml`):** Peruspaketti + *Pienituloisuusaste (`ID 192`)*.<br>**Ekologinen (`manual_indicators.csv`):** *Ominaisvedenkulutus*, *Suojelualueiden osuus* ja *Matkailupainotettu jätemäärä*. |

---

## 6. Valmiiden lisämittareiden pankki (`config.yaml` & `manual_indicators.csv`)

Voit laajentaa kuntasi donitsia (esim. 8 mittarista 10–12 mittariin) tai vaihtaa nykyisiä mittareita kopioimalla alla olevia lohkoja `config.yaml`- tai `manual_indicators.csv`-tiedostoosi.

### A) Sosiaalisen perustan Sotkanet-lisämittarit (`config.yaml` -> `indicators:`-listaan)

*(Kaikki muutkin THL:n yli 3 000 mittarista löydät osoitteesta [sotkanet.fi](https://sotkanet.fi/sotkanet/fi/haku) – mittarin nimen perässä suluissa oleva numero on suoraan `indicator_id`.)*

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

### B) Ekologisen katon valinnaiset rajapintamittarit (`config.yaml` -> `indicators:`-listaan)

Oletuksena käytössä olevat 4 ekologista mittaria (`hinku_paastot`, `kulutus_hiili`, `vesistot`, `luonto_paine`) ovat jo valmiiksi `config.yaml`-tiedostossa. Voit halutessasi täydentää niitä alla olevilla Sotkanet-rajapintaan peilatuilla SYKE:n ja Tilastokeskuksen ympäristöindikaattoreilla:

```yaml
  - id: "khk_kokonais"
    name: "Kasvihuonekaasupäästöt yhteensä (SYKE / Sotkanet)"
    domain: "Ekologinen katto"
    source: "sotkanet"
    indicator_id: 4007
    threshold: 2.0
    unit: "t CO2e/as."
    direction: "lower_is_better"

  - id: "ilmanlaatu_altistus"
    name: "Pienhiukkasille altistuminen (PM2.5)"
    domain: "Ekologinen katto"
    source: "sotkanet"
    indicator_id: 3560
    threshold: 5.0
    unit: "µg/m3"
    direction: "lower_is_better"

  - id: "joukkoliikennevyohyke"
    name: "Joukkoliikennevyöhykkeellä asuvien osuus"
    domain: "Ekologinen katto"
    source: "sotkanet"
    indicator_id: 3218
    threshold: 75.0
    unit: "%"
    direction: "higher_is_better"
```

### C) Paikalliset täydentävät ympäristömittarit (`manual_indicators.csv`-tiedostoon)

Kunnan omista tilastoista tai seudullisista lähteistä seurattavat mittarit voi lisätä suoraan `manual_indicators.csv`-tiedostoon:

```csv
kierratysaste,Yhdyskuntajätteen kierrätysaste,Ekologinen katto,Jäteyhtiö / SYKE,48.0,65.0,%,higher_is_better,2024
vedenkulutus,Ominaisvedenkulutus (l/as./vrk),Ekologinen katto,Kunnan vesilaitos,125.0,110.0,l/vrk,lower_is_better,2024
ajosuorite,Henkilöautojen ajosuorite asukasta kohti,Ekologinen katto,Traficom / SYKE Liiteri,6800.0,4500.0,km/as.,lower_is_better,2024
metsahakkuut,Metsien hakkuiden suhde vuotuiseen kasvuun,Ekologinen katto,Luke / SYKE,82.0,70.0,%,lower_is_better,2024
suojelualueet,Suojellun maa- ja vesipinta-alan osuus,Ekologinen katto,SYKE Suojelualueet,12.5,30.0,%,higher_is_better,2024
```

---

## 7. Tekijänoikeudet ja lisenssi

* **Tekijänoikeus:** © 2026 **Mika Lammi**. Konsepti, järjestelmäarkkitehtuuri ja mittaristomäärittely: Mika Lammi (tekninen toteutus tuotettu tekoälyavusteisesti).
* **Koodin lisenssi:** Julkaistu avoimella **MIT-lisenssillä** (`SPDX-License-Identifier: MIT`). Kuntien edustajat, tutkijat ja kehittäjät voivat vapaasti kopioida, muokata ja hyödyntää tätä tietovarastoa, kunhan alkuperäinen tekijänoikeusmerkintä (`© 2026 Mika Lammi`) säilytetään osana lähdekoodia ja dokumentaatiota.
* **Tilastolähteet:** THL Sotkanet REST API, Suomen ympäristökeskus (SYKE), Tilastokeskus StatFin ja Jyväskylän yliopiston Lipas REST API (CC BY 4.0).
