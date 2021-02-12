#!/usr/bin/env python3
import asyncio
import json
from time import sleep
from urllib.parse import quote

import aiohttp
from aiosseclient import aiosseclient # type: ignore
from mediawikiapi import MediaWikiAPI, PageError # type: ignore
from rich import print
from typing import List, Union, Dict
#from wikibaseintegrator import wbi_core

import input_output
import wikidata

doi_prefix = "https://doi.org/"
excluded_wikis = ["ceb", "zh", "ja"]
mediawikiapi = MediaWikiAPI()
found_text = "[bold red]DOI link found:[/bold red] "
wd_prefix = "http://www.wikidata.org/entity/"
trust_url_file_endings = True

# debug
# input_output.save_to_wikipedia_list(["doi"], "en", "title")
# exit(0)

def search_isbn(page):
    content = page.content
    # TODO search for isbns
    #             found = True
    #             isbns.append(isbn)
    #             print(
    #                 f"{found_text}{doi}",
    #             )
    #     if found:
    #         lookup_isbn(isbns)
    #         sleep(1)
    # else:
    #     print("ISBN number not found")

        
def search_doi(page) -> Union[List[str],None]:
    links = page.references
    if links is not None:
        #print(f"References:{links}")
        found = False
        dois = []
        for link in links:
            if link.find(doi_prefix) != -1:
                found = True
                doi = link.replace(doi_prefix, '')
                dois.append(doi)
                print(
                    f"{found_text}{doi}",
                )
        if found:
            return dois
        else:
            print("External links not found")
            return None
    else:
        print("External links not found")
        return None

def download_page(
        language_code: str = None,
        title: str = None,
):
    print("Downloading wikitext")
    mediawikiapi.config.language = language_code
    #print(mediawikiapi.summary(title, sentences=1))
    page = False
    try:
        page = mediawikiapi.page(title)
        success = True
        if page is not None:
            print("Download finished")
            return page
        else:
            return None
    except PageError:
        print("Got page error, skipping")
        success = False
        return None
    #print(page.sections)
    #print("Looking for templates")

async def main():
    print("Running main")
    count = 0
    async for event in aiosseclient(
            'https://stream.wikimedia.org/v2/stream/recentchange',
    ):
        #print(event)
        data = json.loads(str(event))
        #print(data)
        meta = data["meta"]
        # what is the difference?
        server_name = data['server_name']
        namespace = int(data['namespace'])
        language_code = server_name.replace(".wikipedia.org", "")
        # for exclude in excluded_wikis:
            #if language_code == exclude:
        if language_code != "en":
            continue
        if server_name.find("wikipedia") != -1 and namespace == 0:
            title = data['title']
            if data['bot'] is True:
                bot = "(bot)"
            else:
                bot = "(!bot)"
            if data['type'] == "new":
                type = "(new)"
            elif data['type'] == "edit":
                type = "(edit)"
            else:
                type = None
            if type is not None:
                print(f"{type}\t{server_name}\t{bot}\t\"{title}\"")
                print(f"http://{server_name}/wiki/{quote(title)}")
                page = download_page(
                    language_code=language_code,
                    title=title,
                )
                if page is not None:
                    dois = search_doi(page)
                    if dois is not None:
                        input_output.save_to_wikipedia_list(dois, language_code, title)
                        wikidata.lookup_dois(dois=dois, in_wikipedia=True)
                    count += 1
    if count == 100:
        exit(0)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
