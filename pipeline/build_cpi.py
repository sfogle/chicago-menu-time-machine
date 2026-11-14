#!/usr/bin/env python3
"""Rebuild frontend/public/data/cpi_chicago.json.

Index values are the BLS CPI-U, U.S. city average, annual averages
(1982-84 = 100). Years before 1913 predate the official CPI and use the
Federal Reserve Bank of Minneapolis historical estimates, rebased to the same
scale. BLS did not publish a separate Chicago index until 1914, and the two
track closely, so the national series is used throughout.

BASE_CPI is the one number to update: set it to the latest published
annual-average CPI-U and re-run this script.

    python build_cpi.py
"""
from __future__ import annotations

import json
from pathlib import Path

BASE_YEAR = 2026
# 2026 annual-average CPI-U is not final until January 2027. This is an
# estimate (2024 actual = 313.7, plus roughly 2.6% a year).
BASE_CPI = 330.0

CPI = {
    # Minneapolis Fed estimates (pre-BLS), rebased to 1982-84 = 100
    1890: 9.0, 1891: 9.0, 1892: 9.0, 1893: 9.0, 1894: 8.7,
    1895: 8.4, 1896: 8.4, 1897: 8.4, 1898: 8.4, 1899: 8.4,
    1900: 8.4, 1901: 8.4, 1902: 8.7, 1903: 9.0, 1904: 9.0,
    1905: 9.0, 1906: 9.0, 1907: 9.4, 1908: 9.0, 1909: 9.0,
    1910: 9.4, 1911: 9.4, 1912: 9.7,
    # BLS CPI-U annual averages
    1913: 9.9, 1914: 10.0, 1915: 10.1, 1916: 10.9, 1917: 12.8,
    1918: 15.1, 1919: 17.3, 1920: 20.0, 1921: 17.9, 1922: 16.8,
    1923: 17.1, 1924: 17.1, 1925: 17.5, 1926: 17.7, 1927: 17.4,
    1928: 17.1, 1929: 17.1, 1930: 16.7, 1931: 15.2, 1932: 13.7,
    1933: 13.0, 1934: 13.4, 1935: 13.7, 1936: 13.9, 1937: 14.4,
    1938: 14.1, 1939: 13.9, 1940: 14.0, 1941: 14.7, 1942: 16.3,
    1943: 17.3, 1944: 17.6, 1945: 18.0, 1946: 19.5, 1947: 22.3,
    1948: 24.1, 1949: 23.8, 1950: 24.1, 1951: 26.0, 1952: 26.5,
    1953: 26.7, 1954: 26.9, 1955: 26.8, 1956: 27.2, 1957: 28.1,
    1958: 28.9, 1959: 29.1, 1960: 29.6, 1961: 29.9, 1962: 30.2,
    1963: 30.6, 1964: 31.0, 1965: 31.5, 1966: 32.4, 1967: 33.4,
    1968: 34.8, 1969: 36.7, 1970: 38.8, 1971: 40.5, 1972: 41.8,
    1973: 44.4, 1974: 49.3, 1975: 53.8, 1976: 56.9, 1977: 60.6,
    1978: 65.2, 1979: 72.6, 1980: 82.4, 1981: 90.9, 1982: 96.5,
    1983: 99.6, 1984: 103.9, 1985: 107.6,
}

OUT = Path(__file__).resolve().parent.parent / "frontend" / "public" / "data" / "cpi_chicago.json"


def main() -> None:
    doc = {
        "base_year": BASE_YEAR,
        "base_cpi": BASE_CPI,
        "base_cpi_is_estimate": True,
        "series": "BLS CPI-U, U.S. city average, annual average, 1982-84=100",
        "note": (
            "multiplier = base_cpi / cpi. Multiply a historical price by the "
            "multiplier to get 2026 dollars. 1890-1912 are Minneapolis Fed "
            "estimates; the 2026 base is an estimate until BLS publishes the "
            "annual average. Regenerate with pipeline/build_cpi.py."
        ),
        "years": {
            str(year): {"cpi": cpi, "multiplier": round(BASE_CPI / cpi, 2)}
            for year, cpi in sorted(CPI.items())
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {OUT} ({len(CPI)} years, base {BASE_YEAR} = {BASE_CPI})")


if __name__ == "__main__":
    main()
