🍩 Avoin Kuntadonitsi – Käyttöönotto- ja muokkausopas
Tämä tietovarasto sisältää suomalaisille kunnille suunnatun, automaattisesti päivittyvän donitsitalousmallin (Kuntadonitsin).
Ratkaisu toimii täysin ilmaisilla, avoimen lähdekoodin työkaluilla suoraan GitHubin sisällä (GitHub Actions & GitHub Pages). Se ei vaadi omaa palvelinta, ulkoisia pilvipalveluita, maksullisia lisenssejä eikä ohjelmointikokemusta.
(Oletusasetuksissa esimerkkinä on Kouvolan kaupunki, kuntakoodi `286`, mutta minkä tahansa Suomen kunnan edustaja voi ottaa mallin käyttöönsä muuttamalla kuntanumeron asetustiedostossa.)
1. Miten järjestelmä toimii?
Työkalu	Tehtävä tässä projektissa	Hinta
GitHub-tietovarasto	Säilyttää asetustiedostot, hakuskriptin, tilasto- ja historiadatan sekä verkkosivun lähdekoodin.	0 € (Julkinen projekti)
GitHub Actions	Ajaa tiedonhaun automaattisesti kerran kuukaudessa (tai heti kun muokkaat asetuksia), estää päällekkäiset ajot (`concurrency`) ja tallentaa uudet luvut sekä aikasarjan.	0 €
Python (`fetch_data.py`)	Hakee kuntakohtaisen datan automaattisesti THL:n Sotkanet-rajapinnasta (sosiaalinen perusta) ja monimuuttujaisista Yhdistelmä-API-rajapinnoista (ekologinen katto: SYKE, Tilastokeskus StatFin & JYU Lipas), hyödyntää `manual_indicators.csv`-tiedostoa varajärjestelmänä (fallback) selkeällä `(CSV)`-lähdetunnisteella ja laskee suhdeluvut kestäviin rajoihin (`100 % = 1.0x raja`).	0 €
GitHub Pages (`index.html`)	Julkaisee interaktiivisen kuntadonitsin (tasapainotetulla `120 / 120` -kehäsuhteella), yleisen perustelumodaalin, jokaisen mittarin oman ℹ️ Perustelut -laskentamodaalin sekä aktiivisten mittareiden mukaan suodattuvan aikasarjakaavion suoraan verkkosivuna ilman latausviiveitä.	0 €
2. Projektin tiedostot
Kaikki järjestelmän koodi on valmiina tämän tietovaraston tiedostoissa:
```
kuntadonitsi/
├── config.yaml                         # MUOKATTAVA: Kunnan nimi, kuntakoodi sekä Sotkanet- ja Yhdistelmä-API-mittarit
├── manual_indicators.csv               # MUOKATTAVA: Vikasietoinen varajärjestelmä (CSV-tunnisteella) ja omat lisämittarit
├── doughnut_results.csv                # (Päivittyy automaattisesti) Viimeisin tilannekuva, lähteet ja aikaleima
├── doughnut_history.csv                # (Päivittyy automaattisesti) Vuosi- ja kuukausitason aikasarja
├── fetch_data.py                       # Robottiskripti, joka hakee rajapintadatan, laskee yhdistelmäindeksit ja tallentaa historian
├── index.html                          # Verkkosivun, mittarikohtaisten perustelumodaalien ja kaavioiden lähdekoodi
├── requirements.txt                    # Python-kirjastoriippuvuudet
└── .github/workflows/update_data.yml   # GitHub Actions -automaatioajastin (sisältää concurrency-suojauksen)

```
3. Arkkitehtuurin ja visualisoinnin keskeiset ominaisuudet
Tasapainotetut kehäsuhteet (`120 / 120` sädeyksikköä):
Sisäkehän sosiaalisille vajeille ja ulkokehän ekologisille ylityksille on varattu täsmälleen yhtä suuri säteittäinen liikkumatila (`120` yksikköä) ja identtinen skaalauskerroin (`0.60` / %) vihreän turvallisen tilan kehän molemmin puolin. Näin sosiaalinen perusta ja ekologinen katto saavat yhtä suuren visuaalisen painoarvon.
Monimuuttujaiset Yhdistelmä-APIt ulkokehällä:
Koska kaikkia kuntatason ekologisia mittareita ei julkaista yhdessä yksittäisessä rajapinnassa, `fetch_data.py` muodostaa ulkokehän mittareille painotetut yhdistelmäindeksit useasta avoimesta viranomaisrajapinnasta (THL Sotkanet, SYKE, Tilastokeskus StatFin ja Jyväskylän yliopiston Lipas REST API).
100 % läpinäkyvät lähdemerkinnät ja mittarikohtaiset `ℹ️ Perustelut` -modaali-ikkunat:
Alataulukon oikeassa laidassa on oma `Perustelut`-sarakkeensa, josta avautuu jokaiselle mittarille (sekä sisä- että ulkokehällä) oma modaali-ikkuna. Ikkuna näyttää mittarin reaaliaikaisen arvon, kestävyysrajan, suhdeluvun sekä tarkan laskentakaavan ja tietolähteet.
Jos jokin ulkoinen rajapinta ei vastaa ja arvo luetaan `manual_indicators.csv`-varatiedostosta, lähdesarakkeeseen merkitään automaattisesti `(CSV)` (esim. `SYKE Hinku (CSV)`).
Automaattisesti suodattuva aikasarjakaavio:
Aikasarjakaavio suodattaa `doughnut_history.csv`-tiedoston rivit automaattisesti `doughnut_results.csv`-tiedostossa olevien aktiivisten mittareiden perusteella. Jos poistat tai vaihdat mittarin asetuksista, vanhat mittarit eivät jää kummittelemaan aikasarjavalikkoon.
4. Mittariston tietolähteet ja Yhdistelmä-API-laskentakaavat
Kaikki mittarit on normalisoitu siten, että `100 % (1.0x)` vastaa kestävää tavoiterajaa. Arvot `≤ 100 % (≤ 1.0x)` ovat tavoitetilassa vihreällä kehällä.
A) Sisäkehä: Sosiaalinen perusta (Suora THL Sotkanet REST API)
Mittari (`id`)	Rajapintalähde	Laskentaperuste ja kuvaus	Kestävä raja (`100 % = 1.0x`)
Kansanterveys (THL sairastavuusindeksi) (`sairastavuus`)	`SOTKANET API (ID 244)`	Ikävakioitu kokonaisindeksi, joka yhdistää 7 vakavaa kansansairausryhmää (syövät, sepelvaltimotauti, aivoverisuonisairaudet, tuki- ja liikuntaelinsairaudet, mielenterveys, tapaturmat ja muistisairaudet).	`100.0 indeksi`
(Koko maan keskiarvo = 100) |
| Työttömien osuus työvoimasta (`tyottomyys`) | `SOTKANET API (ID 181)` | TEM:n työnvälitystilaston mukainen työttömien työnhakijoiden osuus työvoimasta (%). Kuvaa elinvoimaa ja taloudellista osallisuutta. | `8.0 %`
(Kestävän työllisyyden viiteraja) |
| Toimeentulotukea saaneet asukkaat (`toimeentulotuki`) | `SOTKANET API (ID 232)` | Kelan ja THL:n rekisterin mukainen varsinaista tai ehkäisevää toimeentulotukea vuoden aikana saaneiden henkilöiden osuus asukkaista (%). | `6.0 %`
(Perusturvan riittävyyden raja) |
| Taloudellinen huoltosuhde (`huoltosuhde`) | `SOTKANET API (ID 182)` | Tilastokeskuksen työssäkäyntitilasto: ei-työllisten asukkaiden määrä 100 työssäkäyvää kohden (`((Väkiluku − Työlliset) / Työlliset) × 100`). | `135.0 indeksi`
(Kestävä veropohja ja huoltosuhde) |
B) Ulkokehä: Ekologinen katto (Monimuuttujaiset Yhdistelmä-APIt & SYKE CSV-varajärjestelmä)
Mittari (`id`)	Ensisijainen Yhdistelmä-API & Varalähde	Monimuuttujainen laskentakaava ja painokertoimet	Kestävä raja (`100 % = 1.0x`)
Alueelliset KHK-päästöt (`hinku_paastot`)	1. `SYKE / Sotkanet API (ID 4007)`		
`Yhdistelmä-API (ID 3218 + 3560 + 184)`
Varalla: `SYKE Hinku (CSV)` | Jos suora `ID 4007` ei vastaa, lasketaan 3 osa-indikaattorista:
• 45 % Liikenne ja yhdyskuntarakenne (`ID 3218`): `3.2 + ((100 − J_osuus) / 100) × 3.0`
• 35 % Paikallinen lämmitys ja poltto (`ID 3560`): `(PM2.5 / 5.0) × 4.6`
• 20 % Aluelaajuus ja maatalous (`ID 184`/`182`): `5.4 − (Tiheys / 200) × 1.5` | `2.0 t CO2e/as.`
(Hinku-kuntien -80 % tavoitetaso) |
| Kulutusperusteinen hiilijalanjälki (`kulutus_hiili`) | 1. `Yhdistelmä-API (ID 181 + 3218 + 182)`
Varalla: `SYKE Kulutus (CSV)` | ENVIMAT-mallin mukainen painotettu yhdistelmä:
• 40 % Ostovoima ja yksityinen kulutus (`ID 181`): `9.4 − (Työttömyys_% × 0.09)`
• 35 % Liikkumistarve ja etäisyydet (`ID 3218`): `6.8 + ((100 − J_osuus) / 100) × 2.6`
• 25 % Asumisväljyys ja palvelurakenne (`ID 182`): `7.4 + ((Huoltosuhde − 135) / 100) × 2.2` | `2.5 t CO2e/as.`
(Pariisin 1,5 °C globaali budjetti) |
| Vesistö- ja ravinnekuormitus (`vesistot`) | 1. `Yhdistelmä-API (ID 3218 + 3560 + 182)`
Varalla: `SYKE Vesikartta (CSV)` | Valuma-alueen ja pintavesien kuormitusindeksi:
• 45 % Hajakuormitus ja peltovalumat (`ID 3218`): `95.0 + (100 − J_osuus) × 0.52`
• 30 % Ympäristö- ja laskeumakuormitus (`ID 3560`): `(PM2.5 / 4.2) × 100`
• 25 % Alueellinen vesistörakenne (`ID 182`): `110.0 + ((Huoltosuhde − 135) / 100) × 32.0` | `100.0 % kuormitus`
(EU:n vesipuitedirektiivin hyvä tila) |
| Maankäyttöpaine vs. lähiluonto (`luonto_paine`) | 1. `Yhdistelmä-API (ID 676 + 3218 + 3560 + Lipas API)`
Varalla: `SYKE Liiteri (CSV)` | Rakennetun ympäristön ja lähiluonnon suhde:
• 40 % Taajama-aste (`ID 676` / StatFin `11ra`): `(Taajama_aste / 80.0) × 100`
• 25 % Yhdyskuntarakenteen hajautuminen (`ID 3218`): `60.0 + (100 − J_osuus) × 0.55`
• 20 % Lähiympäristön hiukkaskuormitus (`ID 3560`): `(PM2.5 / 5.5) × 100`
• 15 % Virkistys- ja luontokohteet (`JYU Lipas API`): `(75.0 / max(30, N_kohteet)) × 100` | `100.0 % kuormitus`
(Lähiluonnon kantokykyraja) |
5. Näin otat mallin käyttöön omalle kunnallesi (4 vaihetta)
Voit tehdä kaikki käyttöönoton vaiheet suoraan verkkoselaimessa.
Vaihe 1: Kopioi projekti omalle GitHub-tilillesi (Fork)
Kirjaudu sisään GitHubiin ja klikkaa tämän sivun oikeasta yläkulmasta Fork -> Create fork.
Pidä tietovarasto julkisena (Public), jotta GitHub Actions ja GitHub Pages toimivat ilmaiseksi.
Vaihe 2: Kytke automaattirobotin oikeudet päälle
Mene kopioimasi projektin ylävalikosta kohtaan Settings -> Actions -> General.
Valitse sivun alareunasta kohdasta Workflow permissions vaihtoehto Read and write permissions ja klikkaa Save.
Avaa ylävalikosta Actions-välilehti ja klikkaa vihreää painiketta I understand my workflows, go ahead and enable them.
Vaihe 3: Vaihda oman kuntasi tiedot (`config.yaml` ja `manual_indicators.csv`)
A) Kunnan nimi, numero ja ydinmittarit (`config.yaml`)
Avaa tiedosto `config.yaml`, klikkaa kynäkuvaketta (Edit) ja vaihda kuntasi nimi sekä virallinen kuntanumero (esim. Kouvola `286`, Lohja `444`, Helsinki `091`, Tampere `837`, Jyväskylä `179`):
```
municipality:
  name: "Kouvola"
  statfin_code: "KU286"
  sotkanet_code: "286"

```
Kun tallennat muutoksen (Commit changes), GitHub Actions käynnistyy taustalla automaattisesti, hakee kuntasi tuoreet tilastot sekä THL:n Sotkanetista että ulkokehän Yhdistelmä-API-rajapinnoista (`syke_khk`, `syke_kulutus`, `syke_vesistot`, `syke_maankaytto`) ja päivittää verkkosivun.
B) Varajärjestelmä ja paikalliset lisämittarit (`manual_indicators.csv`)
Tiedosto `manual_indicators.csv` toimii kahdessa roolissa:
Automaattinen varajärjestelmä (Fallback): Jos jokin ulkoisista rajapinnoista on tilapäisesti huollossa, `fetch_data.py` lukee tarkistetun arvon automaattisesti tästä tiedostosta ja lisää lähteen nimeen tunnisteen `(CSV)`, jolloin sivu toimii 100 % varmuudella ja täysin läpinäkyvästi.
Omat paikalliset lisämittarit: Jos lisäät tiedostoon uusia rivejä (joiden `id` ei ole `config.yaml`-tiedostossa), skripti nostaa ne automaattisesti mukaan Kuntadonitsiin ja luo niille oman perustelumodaalin.
```
id,name,domain,source,value,threshold,unit,direction,year
hinku_paastot,Alueelliset KHK-päästöt (SYKE Hinku),Ekologinen katto,SYKE Hinku,4.9,2.0,t CO2e/as.,lower_is_better,2024
kulutus_hiili,Kulutusperusteinen hiilijalanjälki,Ekologinen katto,SYKE Kulutus,8.2,2.5,t CO2e/as.,lower_is_better,2023
vesistot,Vesistö- ja ravinnekuormitus,Ekologinen katto,SYKE Vesikartta,122.0,100.0,% kuormitus,lower_is_better,2024
luonto_paine,Maankäyttöpaine vs. lähiluonto,Ekologinen katto,SYKE Liiteri,81.2,100.0,% kuormitus,lower_is_better,2025

```
Vaihe 4: Julkaise verkkosivu (GitHub Pages)
Mene kohtaan Settings -> Pages.
Valitse kohdasta Branch pudotusvalikosta `main` (ja kansioksi `/(root)`) ja klikkaa Save.
Noin 30 sekunnin kuluttua sivu on julkisesti käytettävissä osoitteessa `https://<käyttäjätunnus>.github.io/kuntadonitsi/`.
6. Upottaminen verkkosivuille (`<iframe>`)
Voit upottaa Kuntadonitsi-näkymän suoraan osaksi mitä tahansa verkkosivustoa (esim. WordPress, Drupal, SharePoint tai muu julkaisujärjestelmä).
Sivussa on sisäänrakennettu upotustila (`?embed=true`), joka piilottaa sivun oman pääotsikon ja alatunnisteen sekä tekee taustasta läpinäkyvän, jotta näkymä sulautuu saumattomasti kunnan oman sivuston ulkoasuun:
```
<iframe 
  src="https://<käyttäjätunnus>.github.io/kuntadonitsi/?embed=true" 
  width="100%" 
  height="1850" 
  style="border: none; border-radius: 12px; overflow: hidden;" 
  loading="lazy"
  title="Kuntadonitsi">
</iframe>

```
(Jos haluat näyttää upotuksessa myös sivun oman pääotsikon ja taustavärin, jätä `?embed=true` pois osoitteen lopusta.)
7. Kuntatyypit ja niille suositellut mittaripaketit (Sotkanet & Yhdistelmä-API)
Oletuksena käytössä olevat 8 mittaria (4 Sotkanet-mittaria ja 4 Yhdistelmä-API-mittaria) muodostavat kansallisen peruspaketin, joka on saatavilla kaikille Suomen 309 kunnalle. Suomen kunnat ovat kuitenkin elinkeinorakenteeltaan, väestöltään ja ympäristöhaasteiltaan hyvin erilaisia.
Alla olevasta taulukosta näet, miten eri kuntatyyppien kannattaa täydentää tai painottaa mittaristoaan sekä THL Sotkanetin että ulkokehän rajapintojen osalta:
Kuntaprofiili ja esimerkkikunnat	Tyypilliset kestävyyspiirteet	Suositeltava mittaripaketti (`config.yaml` / SYKE & Sotkanet API)
1. Seutukaupungit ja teollisuuspaikkakunnat		
(Kouvola, Lohja, Kotka, Pori, Rauma, Hämeenlinna, Mikkeli, Kemi) | Rakenteellinen työttömyys, väestön ikääntyminen ja kansansairaudet haastavat sosiaalista perustaa; suuri pinta-ala, tieliikenne ja teollisuus vaikuttavat ympäristöön. | Sosiaalinen (Sotkanet API): Peruspaketti (`244`, `181`, `232`, `182`) + Nuorisotyöttömät (`ID 189`) ja Koulutuksen ulkopuolella olevat 17–24-v. (`ID 3199`).
Ekologinen (Yhdistelmä-API): Peruspaketti (`syke_khk`, `syke_kulutus`, `syke_vesistot`, `syke_maankaytto`) + Tieliikenteen päästöt ja Yhdyskuntajätteen kierrätysaste. |
| 2. Suuret kasvukeskukset ja yliopistokaupungit
(Helsinki, Tampere, Turku, Oulu, Jyväskylä, Kuopio, Vaasa) | Suuri opiskelijamäärä nostaa näennäisesti toimeentulotuen saajia, mutta todellinen sosiaalinen vaje syntyy asumisen kalleudesta ja segregaatiosta. Täydennysrakentaminen luo painetta kaupunkiluonnolle. | Sosiaalinen (Sotkanet API): Vaihda huoltosuhde -> Asumismenojen rasittamat asuntokunnat (`ID 3219`) ja lisää Pitkäaikaistyöttömien osuus (`ID 304`).
Ekologinen (Yhdistelmä-API): Painota Kulutusperusteista hiilijalanjälkeä (`syke_kulutus`), Maankäyttöpainetta (`syke_maankaytto`) sekä SYKE/Liiteri-rajapinnan Joukkoliikenteen ja kävelyn/pyöräilyn kulkutapaosuutta. |
| 3. Varakkaat kehyskunnat ja pendelöintikunnat
(Espoo, Kauniainen, Kirkkonummi, Pirkkala, Lempäälä, Kempele, Naantali, Sipoo) | Työllisyys ja tulotaso ovat huippuluokkaa, jolloin perinteiset köyhyysmittarit näyttävät vihreää. Haasteina ovat nuorten henkinen kuormitus, autoiluvaltaisuus, pientalorakentamisen maankäyttö ja korkea kulutuksen hiilijalanjälki. | Sosiaalinen (Sotkanet API): Lisää Nuorten kokema kohtalainen tai vaikea ahdistuneisuus (`ID 4111`) ja Kunnallisvaalien äänestysaktiivisuus (`ID 111`).
Ekologinen (Yhdistelmä-API): Kulutusperusteinen hiilijalanjälki (`syke_kulutus`), Maankäyttöpaine (`syke_maankaytto`) ja Henkilöautoliikenteen päästöt/ajosuorite asukasta kohti. |
| 4. Maatalous- ja alkutuotantovaltaiset maaseutukunnat
(Kurikka, Kauhajoki, Nivala, Kiuruvesi, Huittinen, Loimaa, Närpiö) | Yrittäjävetoinen työllisyys on usein hyvää, mutta alueelliset KHK-päästöt asukasta kohden sekä vesistöjen ravinnekuormitus nousevat korkeiksi valtakunnallisen ruoantuotannon vuoksi. | Sosiaalinen (Sotkanet API): Peruspaketti + Työkyvyttömyyseläkettä saavat 25–64-v. (`ID 313`).
Ekologinen (Yhdistelmä-API): Tarkastele Vesistö- ja ravinnekuormitusta (`syke_vesistot`), Maatalouden päästöosuutta (`syke_khk`) sekä Tuulivoima- ja bioenergiatuotantoa. |
| 5. Pienet, ikääntyvät maaseutu- ja järvikunnat
(Puumala, Ilomantsi, Kuhmo, Viitasaari, Kangasniemi, Parikkala) | Korkea eläkeläisosuus nostaa taloudellisen huoltosuhteen pysyvästi yli 200:n, vaikka työttömyys olisi matala. Keskeistä on ikäihmisten toimintakyky, palvelujen saavutettavuus ja metsä-/järviluonnon tila. | Sosiaalinen (Sotkanet API): Vaihda huoltosuhde (`182`) -> Kotona asuvat 75 vuotta täyttäneet (`ID 1568`) ja lisää Yksinäiseksi itsensä tuntevat (`ID 4261`).
Ekologinen (Yhdistelmä-API): Vesistö- ja ravinnekuormitus (`syke_vesistot`), Suojelualueiden osuus ja Metsien hakkuiden suhde kasvuun. |
| 6. Matkailu- ja luontovetoiset kunnat
(Inari, Kittilä, Kolari, Kuusamo, Sotkamo, Hanko) | Kausivaihtelu työllisyydessä on suurta, ja vapaa-ajan asukkaiden sekä matkailijoiden määrä moninkertaistaa kausittaisen jäte-, vesi- ja liikennekulutuksen vakituiseen väestöön nähden. | Sosiaalinen (Sotkanet API): Peruspaketti + Asumisen ahtaus / kausiasuntojen saatavuus.
Ekologinen (Yhdistelmä-API): Pintavesien ja pohjavesien tila (`syke_vesistot`), Natura- ja luonnonsuojelualueiden kulumispaine (`syke_maankaytto`) sekä Matkailupainotettu jäte- ja energiankulutus. |
8. Valmiiden lisämittareiden pankki (`config.yaml` & `manual_indicators.csv`)
Voit laajentaa kuntasi donitsia (esim. 8 mittarista 10–12 mittariin) tai vaihtaa nykyisiä mittareita kopioimalla alla olevia valmiita lohkoja suoraan `config.yaml`- tai `manual_indicators.csv`-tiedostoosi.
A) Sosiaalisen perustan Sotkanet-lisämittarit (`config.yaml` -> `indicators:`-listaan)
(Huom: Kaikki muutkin THL:n yli 3 000 mittarista löydät osoitteesta sotkanet.fi – mittarin nimen perässä suluissa oleva numero on suoraan `indicator_id`.)
```
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
B) Ekologisen katon automaattiset Yhdistelmä-API-mittarit (`config.yaml` -> `indicators:`-listaan)
Nämä mittarit `fetch_data.py` laskee automaattisesti monimuuttujaisina yhdistelminä THL Sotkanetin, SYKE:n, Tilastokeskus StatFinin ja JYU Lipas API:n avoimista rajapinnoista:
```
  # --- EKOLOGISEN KATON MONIMUUTTUJAISET YHDISTELMÄ-APIT (OLETUSPAKETTI) ---
  - id: "hinku_paastot"
    name: "Alueelliset KHK-päästöt (SYKE / Hinku)"
    domain: "Ekologinen katto"
    source: "syke_khk"
    indicator_id: 4007
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
    name: "Vesistö- ja ravinnekuormitus"
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

  # --- VALINNAISET SUORAT SOTKANET-YMPÄRISTÖMITTARIT RAJAPINNASTA ---
  - id: "joukkoliikenne_vyohyke"
    name: "Kestävän liikkumisen vyöhykkeellä asuvat (SYKE Liiteri)"
    domain: "Ekologinen katto"
    source: "sotkanet"
    indicator_id: 3218
    threshold: 50.0
    unit: "%"
    direction: "higher_is_better"

  - id: "ilmanlaatu_altistus"
    name: "Pienhiukkasille altistuminen (SYKE / THL)"
    domain: "Ekologinen katto"
    source: "sotkanet"
    indicator_id: 3560
    threshold: 5.5
    unit: "ug/m3"
    direction: "lower_is_better"

```
C) Paikalliset täydentävät ympäristömittarit (`manual_indicators.csv`-tiedostoon)
Jos haluat seurata sellaisia paikallisia ympäristölukuja, joita ei vielä julkaista valtakunnallisissa rajapinnoissa (tai haluat asettaa varajärjestelmän arvot), voit lisätä ne suoraan `manual_indicators.csv`-tiedostoon. Järjestelmä merkitsee niiden lähteeksi automaattisesti `(CSV)` ja luo niille oman perusteluikkunan:
```
kierratysaste,Yhdyskuntajätteen kierrätysaste,Ekologinen katto,Jäteyhtiö / SYKE,48.0,65.0,%,higher_is_better,2024
vedenkulutus,Ominaisvedenkulutus (l/as./vrk),Ekologinen katto,Kunnan vesilaitos,125.0,110.0,l/vrk,lower_is_better,2024
ajosuorite,Henkilöautojen ajosuorite asukasta kohti,Ekologinen katto,Traficom / SYKE Liiteri,6800.0,4500.0,km/as.,lower_is_better,2024
metsahakkuut,Metsien hakkuiden suhde vuotuiseen kasvuun,Ekologinen katto,Luke / SYKE,82.0,70.0,%,lower_is_better,2024
suojelualueet,Suojellun maa- ja vesipinta-alan osuus,Ekologinen katto,SYKE Suojelualueet,12.5,30.0,%,higher_is_better,2024

```
9. Tekijänoikeudet ja lisenssi
Tekijänoikeus: © 2026 Mika Lammi. Konsepti, järjestelmäarkkitehtuuri ja mittaristomäärittely: Mika Lammi (tekninen toteutus tuotettu tekoälyavusteisesti).
Koodin lisenssi: Julkaistu avoimella MIT-lisenssillä (`SPDX-License-Identifier: MIT`). Kuntien edustajat, tutkijat ja kehittäjät voivat vapaasti kopioida, muokata ja hyödyntää tätä tietovarastoa, kunhan alkuperäinen tekijänoikeusmerkintä (`© 2026 Mika Lammi`) säilytetään osana lähdekoodia ja dokumentaatiota.
Tilastolähteet: THL Sotkanet REST API, Suomen ympäristökeskus (SYKE), Tilastokeskus StatFin & Jyväskylän yliopiston Lipas-tietokanta (avoin viranomaisdata, CC BY 4.0).
