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

countries = []
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
