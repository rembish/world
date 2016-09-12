#! /usr/bin/env python
from __future__ import print_function
from csv import reader
from requests import get
from sys import argv

GEONAMES_USER = argv[1]


class Country(object):
    def __init__(self, data):
        self.iso2 = data["countryCode"]
        self.geoname_id = data["geonameId"]
        self.continents = ()
        self.names = {}

        self.centroid = data["lat"], data["lng"]
        self.bounding_box = (
            data["bbox"]["west"], data["bbox"]["north"],
            data["bbox"]["east"], data["bbox"]["south"]
        )

countries = []
with open("../countries.csv") as fd:
    for row in reader(fd, delimiter=";"):
        if not row:
            continue

        geoname_id = row[2]
        if geoname_id == "-":
            geoname_id = None
        geoname_id = geoname_id or None

        if not geoname_id:
            result = get("http://api.geonames.org/countryInfoJSON", params={
                "username": GEONAMES_USER,
                "country": row[1].upper()
            }).json()
            geoname_id = result["geonames"][0]["geonameId"]

        result = get("http://api.geonames.org/getJSON", params={
            "username": GEONAMES_USER,
            "geonameId": geoname_id,
            "style": "full",
        }).json()["geoname"]

        country = Country(result)
        country.continents = row[0].split(",")
        country.names = {
            "en": row[3],
            "cs": row[4],
            "ru": row[5],
        }
        countries.append(country)

