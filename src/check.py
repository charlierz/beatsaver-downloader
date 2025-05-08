from dotenv import load_dotenv
import os
import csv
import cfscrape
import time

scraper = cfscrape.create_scraper()
load_dotenv()

CHECK_LOCATION = os.getenv("CHECK_LOCATION")

destination_file = CHECK_LOCATION + "check_results.csv"


def run_check():
    array = check_values()

    csv_columns = [
        "key",
        "name",
        "uploaded",
        "nps_expert",
        "nps_expert_plus",
        "upvotes",
        "downvotes",
        "score",
    ]
    try:
        with open(destination_file, "w", encoding="utf-8-sig") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=csv_columns, lineterminator="\n"
            )
            writer.writeheader()
            for data in array:
                writer.writerow(data)
    except IOError:
        print("I/O error")


def check_values():
    array = []

    for dirname, dirnames, filenames in os.walk(CHECK_LOCATION):
        for filename in filenames:
            time.sleep(0.1)
            filename_parts = filename.split(" - ", 1)
            key = filename_parts[0]

            r = scraper.get("https://beatsaver.com/api/maps/id/" + str(key))
            if r.status_code == 200:
                print(key)
                data = r.json()

                item = {
                    "key": str(key),
                    "name": data["name"],
                    "uploaded": data["updatedAt"],
                    "upvotes": data["stats"]["upvotes"],
                    "downvotes": data["stats"]["downvotes"],
                    "score": data["stats"]["score"],
                }

                for diff in data["versions"][0]["diffs"]:
                    if diff["difficulty"] and diff["difficulty"] == "Expert":
                        item["nps_expert"] = diff["nps"]
                    if diff["difficulty"] and diff["difficulty"] == "ExpertPlus":
                        item["nps_expert_plus"] = diff["nps"]

                array.append(item)
            else:
                print("Skipped " + str(key))

    return array


run_check()
