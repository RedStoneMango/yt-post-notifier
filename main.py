#!/usr/bin/env python3

import signal
from typing import Any, Callable

import urllib3 as urllib
from bs4 import BeautifulSoup
import json
import sys
import re
import webbrowser
import asyncio
from pathlib import Path
from platformdirs import user_config_dir
from desktop_notifier import DesktopNotifier, Urgency, Button, Icon, DEFAULT_ICON, Sound, DEFAULT_SOUND

CONFIG_DIR = user_config_dir("yt-post-notifier")
CONFIG_PATH = CONFIG_DIR + "/config.json"
HISTORY_PATH = CONFIG_DIR + "/history.json"

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

    contents = None
    for tab in tabs:
        if util_find_element_or_else(tab, "", "tabRenderer", "endpoint", "commandMetadata", "webCommandMetadata", "url").endswith("posts"):
            e = util_find_element_or_else(tab, None, "tabRenderer", "content", "sectionListRenderer", "contents")
            if e != None and len(e) != 0:
                contents = e
                break

    if contents == None: return None
    
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

def util_verify_history(history:dict):
    if type(history) != dict:
        print("[ERROR]: History invalid: Not a dict!", file=sys.stderr)
        exit(1)

    for key in history:
        if type(key) != str:
            print("[ERROR]: History invalid: Key not a str!", file=sys.stderr)
            exit(1)
        if type(history[key]) != str:
            print("[ERROR]: History invalid: Value not a str!", file=sys.stderr)
            exit(1)

def util_verify_config(config:dict):
    if type(config) != dict:
        print("Invalid Config Structure: Config is no dict", file=sys.stderr)
        exit(1)

    config.setdefault("notification_timeout", 15)
    if type(config["notification_timeout"]) != int:
        print("Invalid Config Structure: Field 'notification_timeout' is not an int", file=sys.stderr)
        exit(1)
    config.setdefault("internal_post_display", True)
    if type(config["internal_post_display"]) != bool:
        print("Invalid Config Structure: Field 'internal_post_display' is not a bool", file=sys.stderr)
        exit(1)
    config.setdefault("users", [])
    if type(config["users"]) != list:
        print("Invalid Config Structure: Field 'users' is not a list", file=sys.stderr)
        exit(1)

    for entry in config["users"]:
        if type(entry) == str:
            config["users"].remove(entry)
            entry = {"user_name": entry}
            config["users"].append(entry)

        if type(entry) != dict:
            print("Invalid Config Structure: Userlist entry is no dict", file=sys.stderr)
            exit(1)

        if "user_name" not in entry: 
            print("Invalid Config Structure: User entry does not contain mandatory field 'user_name'", file=sys.stderr)
            exit(1)
        if type(entry["user_name"]) != str:
            print("Invalid Config Structure: User entry field 'user_name' is not of type string", file=sys.stderr)
            exit(1)
        entry.setdefault("display_name", entry["user_name"])
        if type(entry["display_name"]) != str:
            print("Invalid Config Structure: User entry field 'display_name' is not of type string", file=sys.stderr)
            exit(1)
        entry.setdefault("urgency", 0)
        if type(entry["urgency"]) != int:
            print("Invalid Config Structure: User entry field 'urgency' is not of type int", file=sys.stderr)
            exit(1)
        if entry["urgency"] < -1 or entry["urgency"] > 1:
            print("Invalid Config Structure: User entry field 'urgency' is not one of -1;0;1", file=sys.stderr)
            exit(1)
        entry.setdefault("title_text", "${NAME} posted!")
        if type(entry["title_text"]) != str:
            print("Invalid Config Structure: User entry field 'title_text' is not of type str", file=sys.stderr)
            exit(1)
        entry.setdefault("message_text", "${NAME} posted a new community post: ${POST;100}")
        if type(entry["message_text"]) != str:
            print("Invalid Config Structure: User entry field 'message_text' is not of type str", file=sys.stderr)
            exit(1)
        entry.setdefault("icon", DEFAULT_ICON.path.as_uri())
        if type(entry["icon"]) != str:
            print("Invalid Config Structure: User entry field 'icon' is not of type str", file=sys.stderr)
            exit(1)
        try:
            Icon(uri=entry["icon"])
        except:
            print("Invalid Config Structure: User entry field 'icon' is not a valid URI", file=sys.stderr)
            exit(1)
        if entry.get("sound") == None:
            entry["sound"] = DEFAULT_SOUND.name
        else:
            if type(entry["sound"]) != str:
                print("Invalid Config Structure: User entry field 'sound' is not of type str", file=sys.stderr)
                exit(1)
            try:
                Sound(uri=entry["sound"])
            except:
                print("Invalid Config Structure: User entry field 'sound' is not a valid URI", file=sys.stderr)
                exit(1)
        entry.setdefault("duration", 5)
        if type(entry["duration"]) != int:
            print("Invalid Config Structure: User entry field 'duration' is not of type int", file=sys.stderr)
            exit(1)

def util_load_config() -> dict:
    file = Path(CONFIG_PATH)
    if not file.exists():
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch()
        file.write_text("{\n    \"users\":[\n        \n    ]\n}\n\n")
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

def util_load_history() -> dict:
    file = Path(HISTORY_PATH)
    if not file.exists():
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch()
        file.write_text("{}")
        print("No history file exists. Creating empty one at " + HISTORY_PATH)
        return {}

    content = file.read_text()
    try:
        data = json.loads(content)
    except:
        print("Invalid History Structure: Incorrect JSON", file=sys.stderr)
        exit(1)

    return data

def util_find_user_config(config:list, user:str) -> dict:
    for user_conf in config["users"]:
        if user_conf.get("user_name") == user:
            return user_conf

def util_create_urgency(config:dict) -> Urgency:
    val = config["urgency"]
    return Urgency.Low if val == -1 else (Urgency.Normal if val == 0 else Urgency.Critical)

def util_create_icon(config:dict) -> Icon:
    return Icon(uri=config["icon"])

def util_create_sound(config:dict) -> Sound:
    return Sound(uri=config["sound"]) if config["sound"] != DEFAULT_SOUND.name else DEFAULT_SOUND
        
async def util_send_notification(title:str, message:str, icon:Icon, sound:Sound, urgency:Urgency, duration:int, timeout:int, action:Callable[[], Any]):
    notifier = DesktopNotifier(app_name="Yt-Post-Notifier", app_icon=icon)

    done_event = asyncio.Event()

    def wrapped_action():
        try:
            action()
        finally:
            done_event.set()

    def on_dismissed():
        done_event.set()

    async def timeout_task():
        await asyncio.sleep(timeout)
        try:
            notifier.close()
        except Exception:
            pass
        done_event.set()
    asyncio.create_task(timeout_task())

    await notifier.send(
        title=title,
        message=message,
        urgency=urgency,
        buttons=[
            Button(
                title="Open Posts",
                on_pressed=wrapped_action,
            )
        ],
        on_clicked=wrapped_action,
        on_dismissed=on_dismissed,
        sound=sound,
        timeout=duration
    )

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, done_event.set)
    loop.add_signal_handler(signal.SIGTERM, done_event.set)

    await done_event.wait()

def util_format_text(format:str, name:str, post:str) -> str:
    named = format.replace("${NAME}", name)
    matches = re.finditer("\\${POST(?:;(\\d+))?\\}", named)
    if matches == None: return named

    offset = 0
    for match in matches:
        size = match.group(1)
        exp = match.group(0)
        start = match.start()
        end = match.end()

        if size == None:
            tr_post = post
        else:
            maxChars = int(size)
            tr_post = (post[:maxChars] + '...') if len(post) > maxChars else post

        named = named[:start + offset] + tr_post + named[end + offset:]
        offset -= len(exp) - len(tr_post)
        
    return named

def util_display_post_internally(user:str, display_name:str):
    import webview # Only import here in case the user doesnt want to use the webview and import the dependencies
    webview.create_window("Yt-Post-Notifier - " + display_name, "https://youtube.com/@" + user + "/posts")
    webview.start()

def util_display_post_externally(user:str):
    webbrowser.open("https://youtube.com/@" + user + "/posts")
    

def display_post(config:dict, user:str, display_name:str):
    if config["internal_post_display"]:
        util_display_post_internally(user, display_name)
    else:
        util_display_post_externally(user)

def load_posts_from_user(user:str) -> list:
    html = util_requestData("https://youtube.com/@" + user + "/posts")
    if html == None: return []

    ytInitialData = util_extractYtInitialData(html)
    if ytInitialData == None: return []

    posts = util_extract_posts(ytInitialData)
    if posts == None: return []

    return posts

def notify(configs:dict, user:str, post:str):
    config = util_find_user_config(configs, user)
    if config == None:
        print("[Warning]: Cannot find configuration for user " + user, file=sys.stderr)
        return

    display_name = config["display_name"]
    asyncio.run(util_send_notification(
        util_format_text(config["title_text"], display_name, post),
        util_format_text(config["message_text"], display_name, post),
        util_create_icon(config),
        util_create_sound(config),
        util_create_urgency(config),
        config["duration"],
        configs["notification_timeout"],
        lambda: display_post(configs, user, display_name)
    ))

def read_config() -> dict:
    config = util_load_config()
    util_verify_config(config)
    return config

def read_history() -> dict:
    history = util_load_history()
    util_verify_history(history)
    return history

def store_history(history:dict):
    hjson = json.dumps(history)
    Path(HISTORY_PATH).write_text(hjson)

def usage():
    print("Usage:", sys.argv[0], "                                # Runs the tool", file=sys.stderr)
    print("      ", sys.argv[0], "test scrape <USER_NAME>         # Prints the last posts of USER_NAME in a JSON format", file=sys.stderr)
    print("      ", sys.argv[0], "test notify <USER_NAME> <POST>  # Sends a test notification that USER_NAME posted a post with content POST, making use of the user's notification configuration", file=sys.stderr)
    print("      ", sys.argv[0], "test display <USER_NAME>        # Shows USER_NAME's posts using the display method specified in the config", file=sys.stderr)
    print("      ", sys.argv[0], "test dump_config                # Loads the tool configuration, initilizeses defaults where needed and prints the whole config object in a JSON format", file=sys.stderr)
    exit(1)

def run_test(type:str, arg:str, arg2:str):
    match type:
        case "scrape":
            print(json.dumps(load_posts_from_user(arg), indent=4))
        case "notify":
            notify(read_config(), arg, arg2)
        case "display":
            config = read_config()
            display_post(config, arg, util_find_user_config(config, arg)["display_name"])
        case "dump_config":
            print(json.dumps(read_config(), indent=4))

def run_workflow():
    config = read_config()
    history = read_history()

    any_match = 0

    for user in config["users"]:
        name = user["user_name"]
        posts = load_posts_from_user(name)
        if len(posts) != 0:
            post = posts[0]
            last_post = history.get(name)
            if last_post == None or post["id"] != last_post:
                notify(config, name, post["content"])
                history[name] = post["id"]
                any_match |= 1
    
    store_history(history)
    exit(0 if any_match == 1 else 1)

def main():
    if len(sys.argv) == 1:
        run_workflow()
    elif sys.argv[1] != "test" or len(sys.argv) < 3:
        usage()
    else:
        if sys.argv[2] not in ["scrape", "notify", "display", "dump_config"]: usage()
        if sys.argv[2] == "dump_config":
            if len(sys.argv) != 3: usage()
            run_test("dump_config", None, None)
        elif sys.argv[2] == "notify":
            if len(sys.argv) != 5: usage()
            run_test("notify", sys.argv[3], sys.argv[4])
        else:
            if len(sys.argv) != 4: usage()
            run_test(sys.argv[2], sys.argv[3], None)

main()
