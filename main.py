#!/usr/bin/env python3

import urllib3 as urllib
from bs4 import BeautifulSoup
import json


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

def loadData(user:str) -> list:
    html = util_requestData("https://youtube.com/@" + user + "/posts")
    if html == None: return []

    ytInitialData = util_extractYtInitialData(html)
    if ytInitialData == None: return []

    posts = util_extract_posts(ytInitialData)
    if posts == None: return []

    return posts

