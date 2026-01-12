# -*- coding: utf-8 -*-
import logging
import re
import time
import xml.etree.ElementTree as ET

import requests


class PubMedClient:
    def __init__(self, email):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.email = email
        self.logger = logging.getLogger("PubMedClient")

    def search_similar(self, pmid, max_results=3):
        """Find articles similar to a given PMID."""
        if not self.email or "example.com" in self.email:
            return []
        try:
            link_url = f"{self.base_url}/elink.fcgi"
            params = {
                "dbfrom": "pubmed",
                "id": pmid,
                "linkname": "pubmed_pubmed",
                "email": self.email,
                "retmode": "json",
            }
            resp = requests.get(link_url, params=params)
            if resp.status_code != 200:
                return []

            data = resp.json()
            # Extract similar IDs
            linksets = data.get("linksets", [])
            if not linksets:
                return []

            id_list = []
            for linkset in linksets:
                for linksetdb in linkset.get("linksetdbs", []):
                    if linksetdb.get("linkname") == "pubmed_pubmed":
                        id_list.extend([l.get("id") for l in linksetdb.get("links", [])])

            if not id_list:
                return []

            # Fetch details for the first few similar IDs (excluding the original)
            similar_ids = [i for i in id_list if i != str(pmid)][:max_results]
            return self.fetch_details_by_ids(similar_ids)
        except Exception as e:
            self.logger.error(f"PubMed similar search error: {e}")
            return []

    def fetch_details_by_ids(self, id_list):
        """Fetch full details for a list of PMIDs."""
        if not id_list:
            return []
        try:
            fetch_url = f"{self.base_url}/efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "xml",
                "email": self.email,
            }
            fetch_resp = requests.get(fetch_url, params=fetch_params)
            if fetch_resp.status_code != 200:
                return []
            return self._parse_pubmed_xml(fetch_resp.content)
        except Exception as e:
            self.logger.error(f"PubMed fetch error: {e}")
            return []

    def search_details(self, query, max_results=3):
        """
        Search PubMed and return structured details (Title, Abstract, Journal, Year, Authors)
        for top matches.
        """
        if not self.email or "example.com" in self.email:
            self.logger.warning("PubMed email not configured.")
            return []

        # Enhance query with Title/Abstract tag if no tags are present
        if "[" not in query and "AND" not in query and "OR" not in query:
            query = f"({query})[Title/Abstract]"
            self.logger.debug(f"Enhanced PubMed query: {query}")

        try:
            # 1. ESearch
            search_url = f"{self.base_url}/esearch.fcgi"
            params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "email": self.email,
                "retmode": "json",
            }
            resp = requests.get(search_url, params=params)
            if resp.status_code != 200:
                return []

            data = resp.json()
            id_list = data.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                return []

            return self.fetch_details_by_ids(id_list)

        except Exception as e:
            self.logger.error(f"PubMed search error: {e}")
            return []

    def _parse_pubmed_xml(self, xml_content):
        """Common parser for PubMed XML response."""
        try:
            root = ET.fromstring(xml_content)
            results = []

            for article in root.findall(".//PubmedArticle"):
                pmid = article.findtext(".//PMID")
                title = article.findtext(".//ArticleTitle")

                abstract_texts = []
                for abstract_text in article.findall(".//AbstractText"):
                    if abstract_text.text:
                        label = abstract_text.get("Label")
                        text = abstract_text.text
                        if label:
                            abstract_texts.append(f"{label}: {text}")
                        else:
                            abstract_texts.append(text)
                abstract = "\n".join(abstract_texts) if abstract_texts else "No Abstract Found"

                journal = article.findtext(".//Journal/Title") or article.findtext(
                    ".//Journal/ISOAbbreviation"
                )

                year = article.findtext(".//JournalIssue/PubDate/Year")
                if not year:
                    medline_date = article.findtext(".//JournalIssue/PubDate/MedlineDate")
                    if medline_date:
                        year_match = re.search(r"\b(19|20)\d{2}\b", medline_date)
                        if year_match:
                            year = year_match.group(0)

                authors = []
                for author in article.findall(".//Author"):
                    last_name = author.findtext("LastName")
                    fore_name = author.findtext("ForeName")
                    if last_name:
                        authors.append(f"{last_name} {fore_name or ''}".strip())

                doi = None
                for article_id in article.findall(".//ArticleId"):
                    if article_id.get("IdType") == "doi":
                        doi = article_id.text
                        break

                results.append(
                    {
                        "pmid": pmid,
                        "title": title,
                        "abstract": abstract,
                        "journal": journal,
                        "year": year,
                        "authors": authors,
                        "doi": doi,
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                    }
                )
            return results
        except Exception as e:
            self.logger.error(f"PubMed XML parse error: {e}")
            return []

    def search_abstract(self, query):
        """Legacy wrapper for backward compatibility."""
        results = self.search_details(query, max_results=1)
        if results:
            return results[0]["abstract"]
        return None
