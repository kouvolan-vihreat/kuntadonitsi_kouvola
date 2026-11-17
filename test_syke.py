#!/usr/bin/env python3
"""Testaa SYKE:n Hinku- ja kulutusperusteisten päästöjen OData-haut.

Käyttö:
    python test_syke.py

Vaihda MUNICIPALITY_CODE tarvittaessa oman kuntasi kuntakoodiksi.
Riippuvuus: requests (asennus: python -m pip install requests)
"""

import sys

import requests

MUNICIPALITY_CODE = "286"  # Kouvola
HEADERS = {
    "User-Agent": "AvoinKuntadonitsi/1.0 (https://github.com/mikalammi/kuntadonitsi)",
    "Accept": "application/json",
}
TIMEOUT_SECONDS = 20

ENDPOINTS = {
    "Hinku-päästöt": "https://avoindata.syke.fi/odata/KHKPaastot",
    "Kulutusperusteiset päästöt": "https://avoindata.syke.fi/odata/KulutusPaastot",
}


def test_endpoint(name: str, url: str, municipality_code: str) -> bool:
    """Hae yhden SYKE-endpointin data ja tulosta vastauksen perustiedot."""
    code = municipality_code.zfill(3)
    params = {
        "$filter": f"Kuntakoodi eq '{code}'",
        "$format": "json",
    }

    print(f"\n{name}")
    print(f"  URL: {url}")
    print(f"  Kuntakoodi: {code}")

    try:
        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=TIMEOUT_SECONDS,
        )
        print(f"  HTTP-status: {response.status_code}")
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"  PYYNTÖ EPÄONNISTUI: {exc}")
        if getattr(exc, "response", None) is not None:
            print(f"  Vastaus: {exc.response.text[:500]}")
        return False

    try:
        payload = response.json()
    except ValueError:
        print("  VIRHE: vastaus ei ole kelvollista JSON-muotoa.")
        print(f"  Vastaus: {response.text[:500]}")
        return False

    rows = payload.get("value") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        print("  VIRHE: JSON-vastauksesta ei löytynyt OData-muotoista 'value'-listaa.")
        print(f"  JSON-rakenne: {str(payload)[:500]}")
        return False

    print(f"  Rivien määrä: {len(rows)}")
    if not rows:
        print("  Haku onnistui, mutta tällä kuntakoodilla ei löytynyt rivejä.")
        return False

    # Näytä kentät ja muutama vastausrivi, jotta rajapinnan todellinen rakenne näkyy.
    print(f"  Palautetut kentät: {', '.join(map(str, rows[0].keys()))}")
    for row in rows[:3]:
        print(f"  Rivi: {row}")

    year_field = "Vuosi"
    value_field = "PaastotPerAsukas"
    valid_rows = []
    for row in rows:
        try:
            valid_rows.append((int(row[year_field]), float(row[value_field])))
        except (KeyError, TypeError, ValueError):
            continue

    if valid_rows:
        latest_year, latest_value = max(valid_rows, key=lambda item: item[0])
        print(f"  Uusin arvo: vuosi {latest_year}, {latest_value} t CO2e/as.")
    else:
        print(f"  Huomio: riveistä ei löytynyt kelvollisia {year_field}/{value_field}-arvoja.")
        return False

    return True


def main() -> int:
    print(f"Testataan SYKE-rajapintoja kunnalle {MUNICIPALITY_CODE}.")
    results = [
        test_endpoint(name, url, MUNICIPALITY_CODE)
        for name, url in ENDPOINTS.items()
    ]

    passed = sum(results)
    print(f"\nYhteenveto: {passed}/{len(results)} hakua palautti käyttökelpoisia arvoja.")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
