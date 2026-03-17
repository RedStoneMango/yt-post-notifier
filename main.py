#!/usr/bin/env python3

import urllib3 as urllib
from bs4 import BeautifulSoup
import json
import sys
from pathlib import Path
from platformdirs import user_config_dir

CONFIG_PATH = user_config_dir("yt-post-notifier") + "/config.json"

def util_requestData(url:str) -> str | None:
    response = urllib.request("GET", url)
    return response.data if response.status == 200 else None

def util_extractYtInitialData(html:str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all("script")

    for script in scripts:
        if len(script.contents) != 1:
            continue

        content = str(script.string)
        if content.startswith("var ytInitialData = "):
            info = content.removeprefix("var ytInitialData = ").removesuffix(";")
            return json.loads(info)
        
# Utility method to traverse a dict's structure without having to worry about possible TypeErrors because of NoneTypes
def util_find_element_or_else(dict:dict, default:any, *paths:str) -> any:
    currElement = dict
    for path in paths:
        currElement = currElement.get(path)
        if currElement == None: return default
    return currElement

def util_extract_posts(ytInitialData:dict) -> dict | None:
    tabs = util_find_element_or_else(ytInitialData, [], "contents", "twoColumnBrowseResultsRenderer", "tabs")
    if len(tabs) == 0: return None

    for tab in tabs:
        if util_find_element_or_else(tab, "", "tabRenderer", "endpoint", "commandMetadata", "webCommandMetadata", "url").endswith("posts"):
            e = util_find_element_or_else(tab, None, "tabRenderer", "content", "sectionListRenderer", "contents")
            if e != None and len(e) != 0:
                contents = e
                break
    
    allResults = []
    postsData = util_find_element_or_else(contents[0], [], "itemSectionRenderer", "contents")
    if len(postsData) == 0: return []
    for postData in postsData:
        postResult = {
            "id": "Err Unknown",
            "content": ""
        }
        info = util_find_element_or_else(postData, {}, "backstagePostThreadRenderer", "post", "backstagePostRenderer")

        id = util_find_element_or_else(info, None, "postId")
        if id == None: continue
        postResult["id"] = id

        textRuns = util_find_element_or_else(info, [], "contentText", "runs")
        for textRun in textRuns:
            postResult["content"] += util_find_element_or_else(textRun, "", "text")

        allResults.append(postResult)

    return allResults

def util_verify_config(config:list):
    if type(config) != list: print("Invalid Config Structure: Config is no list", file=sys.stderr)

    for entry in config:
        if type(entry) == str:
            config.remove(entry)
            config.append({
                "user_name": entry,
                "display_name": entry,
                "urgency": 0
            })
            continue

        if type(entry) != dict:
            print("Invalid Config Structure: List entry is no dict", file=sys.stderr)
            exit(1)

        if "user_name" not in entry: 
            print("Invalid Config Structure: Entry does not contain required field 'user_name'", file=sys.stderr)
            exit(1)
        if type(entry["user_name"]) != str:
            print("Invalid Config Structure: Entry field 'user_name' is not of type string", file=sys.stderr)
            exit(1)
        if "display_name" not in entry:
            print("Invalid Config Structure: Entry does not contain required field 'display_name'", file=sys.stderr)
            exit(1)
        if type(entry["display_name"]) != str:
            print("Invalid Config Structure: Entry field 'display_name' is not of type string", file=sys.stderr)
            exit(1)
        if "urgency" not in entry:
            print("Invalid Config Structure: Entry does not contain required field 'urgency'", file=sys.stderr)
            exit(1)
        if type(entry["urgency"]) != int:
            print("Invalid Config Structure: Entry field 'urgency' is not of type int", file=sys.stderr)
            exit(1)
        if entry["urgency"] < -1 or entry["urgency"] > 1:
            print("Invalid Config Structure: Entry field 'urgency' is not one of -1;0;1", file=sys.stderr)
            exit(1)

def util_load_config() -> list:
    file = Path(CONFIG_PATH)
    if not file.exists():
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch()
        file.write_text("[\n    \n]\n\n")
        print("No config file exists. Creating new one at " + CONFIG_PATH)
        print("Exiting to allow the user to set up configuration")
        exit()

    content = file.read_text()
    try:
        data = json.loads(content)
    except:
        print("Invalid Config Structure: Incorrect JSON", file=sys.stderr)
        exit(1)

    return data

def load_posts_from_user(user:str) -> list:
    html = util_requestData("https://youtube.com/@" + user + "/posts")
    if html == None: return []

    ytInitialData = util_extractYtInitialData(html)
    if ytInitialData == None: return []

    posts = util_extract_posts(ytInitialData)
    if posts == None: return []

    return posts

def read_config() -> list:
    config = util_load_config()
    util_verify_config(config)
    return config

def usage():
    print("Usage:", sys.argv[0], file=sys.stderr)
    print("      ", sys.argv[0], "test scrape <USER_NAME>", file=sys.stderr)
    print("      ", sys.argv[0], "test notify <USER_NAME>", file=sys.stderr)
    print("      ", sys.argv[0], "test display <USER_NAME>", file=sys.stderr)
    print("      ", sys.argv[0], "test dump_config", file=sys.stderr)
    exit(1)

def run_test(type:str, arg:str):
    match type:
        case "scrape":
            print(json.dumps(load_posts_from_user(arg), indent=4))
        case "notify":
            pass
        case "display":
            pass
        case "dump_config":
            print(json.dumps(read_config(), indent=4))

def main():
    if len(sys.argv) == 1:
        print("Not yet implemented", file=sys.stderr)
    elif sys.argv[1] != "test" or len(sys.argv) < 3:
        usage()
    else:
        if sys.argv[2] not in ["scrape", "notify", "display", "dump_config"]: usage()
        if sys.argv[2] == "dump_config":
            if len(sys.argv) != 3: usage()
            run_test("dump_config", None)
        else:
            if len(sys.argv) != 4: usage()
            run_test(sys.argv[2], sys.argv[3])

    

main()
