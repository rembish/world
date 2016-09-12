#! /usr/bin/env python
from __future__ import print_function
from csv import reader, DictWriter
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
            data["bbox"]["north"], data["bbox"]["east"],
            data["bbox"]["south"], data["bbox"]["west"],
        )

    def get_row(self):
        return (
            ",".join(self.continents), self.iso2, self.geoname_id,
            self.centroid[0], self.centroid[1],
            self.bounding_box[0], self.bounding_box[1], self.bounding_box[2], self.bounding_box[3],
            self.names["en"], self.names["cs"], self.names["ru"],
        )


class Capital(object):
    def __init__(self, data):
        self.geoname_id = data["geonameId"]
        self.country_code = data["countryCode"]
        self.names = {}

        self.centroid = data["lat"], data["lng"]
        self.bounding_box = (
            data["bbox"]["north"], data["bbox"]["east"],
            data["bbox"]["south"], data["bbox"]["west"],
        )

        for lang in ("en", "cs", "ru"):
            best = None
            for row in data["alternateNames"]:
                if row["lang"] == lang:
                    if row.get("isPreferredName"):
                        best = row["name"]
                    elif not best:
                        best = row["name"]
            self.names[lang] = (best or "").encode("utf-8")

    def get_row(self):
        return (
            self.country_code, self.geoname_id,
            self.centroid[0], self.centroid[1],
            self.bounding_box[0], self.bounding_box[1], self.bounding_box[2],
            self.bounding_box[3],
            self.names["en"], self.names["cs"], self.names["ru"],
        )


countries = []
capitals = []

with open("../countries.csv") as fd:
    for row in reader(fd, delimiter=";"):
        if not row:
            continue
        if len(row[1]) != 2:
            continue  # header

        geoname_id = row[2]
        if geoname_id == "-":
            geoname_id = None
        geoname_id = geoname_id or None

        print("Getting data for {}".format(row[-3]))

        result = get("http://api.geonames.org/countryInfoJSON", params={
            "username": GEONAMES_USER,
            "country": row[1].upper()
        }).json()
        if not geoname_id:
            geoname_id = result["geonames"][0]["geonameId"]
        capital = result["geonames"][0]["capital"]

        result = get("http://api.geonames.org/getJSON", params={
            "username": GEONAMES_USER,
            "geonameId": geoname_id,
            "style": "full",
        }).json()

        country = Country(result)
        country.continents = row[0].split(",")
        country.iso2 = row[1].upper()
        country.names = {
            "en": row[-3],
            "cs": row[-2],
            "ru": row[-1],
        }
        countries.append(country)

        codes = {"IL": "PPLA", "PS": "PPLX"}

        result = get("http://api.geonames.org/searchJSON", params={
            "username": GEONAMES_USER,
            "name_exact": capital,
            "featureCode": codes.get(country.iso2, "PPLC"),
            "style": "full",
            "maxRows": 1,
            "country": country.iso2,
        }).json()["geonames"][0]

        capital = Capital(result)
        capital.country_code = country.iso2
        capitals.append(capital)

with open('../countries.csv', "wt") as fd:
    writer = DictWriter(fd, [
        "continents", "iso2", "geoname_id",
        "latitude", "longitude",
        "north", "east", "south", "west",
        "en", "cs", "ru"
    ], delimiter=";")
    writer.writeheader()

    for country in countries:
        writer.writer.writerow(country.get_row())

with open('../capitals.csv', "wt") as fd:
    writer = DictWriter(fd, [
        "country", "geoname_id",
        "latitude", "longitude",
        "north", "east", "south", "west",
        "en", "cs", "ru"
    ], delimiter=";")
    writer.writeheader()

    for capital in capitals:
        row = capital.get_row()
        writer.writer.writerow(row)
