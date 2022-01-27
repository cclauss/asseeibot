from __future__ import annotations
import logging
from typing import List, TYPE_CHECKING

import pywikibot
from pywikibot import Page

from asseeibot import config, wikidata
from asseeibot.models.identifiers.doi import Doi
from asseeibot.models.wikimedia.templates.enwp.cite_journal import CiteJournal
from asseeibot.models.wikimedia.wikipedia_page_reference import WikipediaPageReference

if TYPE_CHECKING:
    from asseeibot.models.wikimedia.wikimedia_event import WikimediaEvent


class WikipediaPage:
    """Models a WMF Wikipedia page"""
    number_of_dois: int = 0
    number_of_isbns: int = 0
    number_of_missing_dois: int = 0
    number_of_missing_isbns: int = 0
    page_id: int = None
    pywikibot_page: Page = None
    references: List[WikipediaPageReference] = None
    title: str = None
    wikimedia_event: WikimediaEvent = None
    missing_dois: List[Doi] = None
    dois: List[Doi] = None

    def __init__(
            self,
            wikimedia_event: WikimediaEvent = None
    ):
        """Get the page from Wikipedia"""
        logger = logging.getLogger(__name__)
        if wikimedia_event is None:
            raise ValueError("wikimedia_event was None")
        self.wikimedia_event = wikimedia_event
        self.title = self.wikimedia_event.page_title
        logger.info("Fetching the wikitext")
        self.pywikibot_page = pywikibot.Page(self.wikimedia_event.event_stream.pywikibot_site, self.title)
        self.page_id = int(self.pywikibot_page.pageid)
        self.__parse_templates__()
        self.__populate_missing_dois__()
        self.__calculate_statistics__()

    def __parse_templates__(self):
        """We parse all the templates into WikipediaPageReferences"""
        logger = logging.getLogger(__name__)
        logger.info("Parsing templates")
        raw = self.pywikibot_page.raw_extracted_templates
        self.references = []
        self.dois = []
        for template_name, content in raw:
            logger.debug(f"working on {template_name}")
            if template_name.lower() == "cite journal":
                logger.debug(f"content:{content}")
                cite_journal = CiteJournal(content)
                self.references.append(cite_journal)
                if cite_journal.doi is not None:
                    self.number_of_dois += 1
                    self.dois.append(cite_journal.doi)
                else:
                    # We ignore cultural magazines for now
                    if cite_journal.journal_title is not None and not "magazine" in cite_journal.journal_title:
                        logger.warning(f"An article titled {cite_journal.article_title} "
                                       f"in the journal_title {cite_journal.journal_title} "
                                       f"was found but no DOI. "
                                       f"(pmid:{cite_journal.pmid} jstor:{cite_journal.jstor})")
        # exit()

    def __populate_missing_dois__(self):
        # logger = logging.getLogger(__name__)
        self.missing_dois = []
        if self.dois is not None and len(self.dois) > 0:
            missing_dois = wikidata.lookup_dois(dois=self.dois)
            if missing_dois is not None and len(missing_dois) > 0:
                self.missing_dois.extend(missing_dois)

    def __calculate_statistics__(self):
        logger = logging.getLogger(__name__)
        self.number_of_dois = len(self.dois)
        self.number_of_missing_dois = len(self.missing_dois)
        print(f"Found {self.number_of_missing_dois}/{self.number_of_dois} missing DOIs on this page")
        # if len(missing_dois) > 0:
        #     input_output.save_to_wikipedia_list(missing_dois, language_code, title)
        # if config.import_mode:
        # answer = util.yes_no_question(
        #     f"{doi} is missing in WD. Do you"+
        #     " want to add it now?"
        # )
        # if answer:
        #     crossref.lookup_data(doi=doi, in_wikipedia=True)
        #     pass
        # else:
        #     pass
