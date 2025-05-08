from dotenv import load_dotenv
import os
import shutil
import cfscrape
import time

scraper = cfscrape.create_scraper()
load_dotenv()

PRUNE_LOCATION = os.getenv("PRUNE_LOCATION")
DELETE_LOCATION = os.getenv("DELETE_LOCATION")

GREAT_LOCATION = PRUNE_LOCATION + "/_g"

min_nps = 2
max_nps = 9.5
min_score_expert_plus = 0.80
min_duration = 60

great_score = 0.9


def run_prune():
    if not os.path.exists(DELETE_LOCATION):
        os.makedirs(DELETE_LOCATION)

    if not os.path.exists(GREAT_LOCATION):
        os.makedirs(GREAT_LOCATION)

    for dirname, dirnames, filenames in os.walk(PRUNE_LOCATION, topdown=True):
        for filename in filenames:
            time.sleep(0.1)
            filename_parts = filename.split(" - ", 1)
            key = filename_parts[0]

            r = scraper.get("https://beatsaver.com/api/maps/id/" + str(key))
            if r.status_code == 200:
                print(key)
                data = r.json()

                if should_delete(data):
                    shutil.move(
                        os.path.join(dirname, filename),
                        os.path.join(DELETE_LOCATION, filename),
                    )
                elif should_move_great(data):
                    shutil.move(
                        os.path.join(dirname, filename),
                        os.path.join(GREAT_LOCATION, filename),
                    )

            else:
                print("Skipped " + str(key))


def contains(list, filter):
    for x in list:
        if filter(x):
            return True
    return False


def should_delete(data):
    if data.get("stats").get("score") < min_score_expert_plus:
        return True

    if data.get("metadata").get("duration") < min_duration:
        return True

    nps_expert_plus = None
    for diff in data["versions"][0]["diffs"]:
        if diff["difficulty"] and diff["difficulty"] == "ExpertPlus":
            nps_expert_plus = diff["nps"]
            break

    if nps_expert_plus and (nps_expert_plus < min_nps or nps_expert_plus > max_nps):
        return True


def should_move_great(data):
    if data.get("stats").get("score") > great_score:
        return True


run_prune()
