from dotenv import load_dotenv
from datetime import datetime, timedelta
import string
import unicodedata
import os
import dateutil.parser
import pytz
import cfscrape

scraper = cfscrape.create_scraper()
load_dotenv()

DOWNLOAD_LOCATION = os.getenv("DOWNLOAD_LOCATION")

MIN_SCORE_EXPERT_PLUS = 0.75
MIN_NPS = 3
DAYS_TO_STABLE = 14
TRACKED_RUNS_LOCATION = "./data/download_runs.txt"

def run_downloader():
    if not os.path.exists(DOWNLOAD_LOCATION):
        os.makedirs(DOWNLOAD_LOCATION)

    next_page = 20
    now = datetime.now(pytz.utc)
    from_date = now - timedelta(days=DAYS_TO_STABLE)
    until_date = None

    f = open(TRACKED_RUNS_LOCATION, "r")
    if f.mode == "r":
        line_list = f.readlines()
        until_date = dateutil.parser.parse(line_list[-1])
    f.close()
    print("From Date: " + str(from_date))
    print("Until Date: " + str(until_date))

    while next_page is not None:
        next_page = download_from_page(next_page, from_date, until_date)

    f = open(TRACKED_RUNS_LOCATION, "a+")
    f.write("\n")
    f.write(str(from_date))
    f.close()


def contains(list, filter):
    for x in list:
        if filter(x):
            return True
    return False


def download_from_page(page_number, from_date, until_date):
    print("Page: " + str(page_number))
    r = scraper.get(
        "https://beatsaver.com/api/search/text/"
        + str(page_number)
        + "?sortOrder=Latest"
    )
    data = r.json()
    for doc in data.get("docs"):

        uploaded = dateutil.parser.parse(doc.get("uploaded"))
        if until_date is not None and uploaded < until_date:
            print("Until Date Reached")
            return None
        elif uploaded < from_date:
            metadata = doc.get("metadata")
            stats = doc.get("stats")

            for version in doc.get("versions"):
                difficulties = version.get("diffs")
                hasExpertPlus = contains(
                    difficulties, lambda x: x.get("difficulty") == "ExpertPlus"
                )
                if hasExpertPlus:
                    nps_expert_plus = None
                    for diff in difficulties:
                        if (
                            diff.get("difficulty")
                            and diff.get("difficulty") == "ExpertPlus"
                        ):
                            nps_expert_plus = diff.get("nps")
                            break

                    if (
                        (stats.get("score") >= MIN_SCORE_EXPERT_PLUS
                        and nps_expert_plus >= MIN_NPS)
                        or doc.get("ranked")
                    ):
                        filename = doc.get("id") + " - " + metadata.get("songName")
                        filename = remove_disallowed_filename_chars(filename)
                        try:
                            print(filename)
                            r_file = scraper.get(version.get("downloadURL"))
                            with open(DOWNLOAD_LOCATION + filename + ".zip", "wb") as f:
                                f.write(r_file.content)
                        except:
                            pass

    return page_number + 1


validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)

def remove_disallowed_filename_chars(filename):
    cleaned_filename = unicodedata.normalize("NFKD", filename).encode("ASCII", "ignore")
    return "".join(chr(c) for c in cleaned_filename if chr(c) in validFilenameChars)


run_downloader()
