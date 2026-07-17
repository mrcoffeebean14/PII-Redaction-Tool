import re
import spacy
from presidio_analyzer import AnalyzerEngine

class PIIDetector:
    def __init__(self):
        # Load spacy and Presidio engines
        self.nlp = spacy.load("en_core_web_lg")
        self.analyzer = AnalyzerEngine()
        
        # Corporate suffix matching for company detection
        self.company_suffixes = [
            r"\blimited\b", r"\bltd\b", r"\bprivate\b", r"\bpvt\b", 
            r"\bcorporation\b", r"\bcorp\b", r"\bincorporated\b", r"\binc\b", 
            r"\bcompany\b", r"\bco\b", r"\bllp\b", r"\bpartnership\b",
            r"\bindustries\b", r"\bsolutions\b", r"\benterprises\b", r"\bholdings\b",
            r"\bassociation\b", r"\bbank\b", r"\binsurance\b", r"\btrust\b", 
            r"\bventures\b", r"\bventure\b"
        ]
        self.company_suffix_pattern = re.compile("|".join(self.company_suffixes), re.IGNORECASE)
        self.known_companies = ["ksh international", "bhandary metal extrusion"]
        
        # Regex patterns for direct PII matches
        self.email_regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
        self.phone_regex = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,5}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b")
        self.ssn_regex = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
        self.pan_regex = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)
        self.aadhaar_regex = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b")
        self.cc_regex = re.compile(r"\b(?:\d{4}[\s-]?){3}\d{4}\b|\b\d{13,19}\b")
        self.ipv4_regex = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
        self.ipv6_regex = re.compile(
            r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|"
            r"\b(?:[0-9a-fA-F]{1,4}:){1,7}:[0-9a-fA-F]{1,7}\b"
        )
        self.date_regex = re.compile(
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|"
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2},?\s\d{4}\b|"
            r"\b\d{1,2}\s(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}\b|"
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{1,2},?\s\d{4}\b"
        )
        
        self.dob_keywords = ["born", "birth", "dob", "d.o.b.", "age", "yeardate"]
        self.name_title_regex = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b")
        self.name_caps_regex = re.compile(r"\b[A-Z]{3,}(?:\s+[A-Z]{3,}){1,2}\b")

    def _is_dob_context(self, text, start, end):
        # Checks if birth-related keywords exist in the containing sentence
        left_text = text[:start]
        sentence_start_idx = 0
        for m in re.finditer(r"[.!?]\s+", left_text):
            sentence_start_idx = m.end()
            
        right_text = text[end:]
        sentence_end_idx = len(text)
        for m in re.finditer(r"[.!?](?:\s+|$)", right_text):
            sentence_end_idx = end + m.start()
            break
            
        sentence = text[sentence_start_idx:sentence_end_idx].lower()
        return any(keyword in sentence for keyword in self.dob_keywords)

    def _is_company(self, entity_text):
        # Verifies if ORG text aligns with corporate suffix structures
        entity_text = entity_text.strip()
        if not entity_text or len(entity_text) < 4:
            return False
        if any(c in entity_text.lower() for c in self.known_companies):
            return True
        if self.company_suffix_pattern.search(entity_text):
            if "act" in entity_text.lower():
                return False
            return True
        return False

    def _is_valid_name(self, name_str):
        # Validates candidate name by filtering out digits, punctuation, and common terms
        name_str = name_str.strip()
        if not name_str:
            return False
        if len(name_str) < 3 or len(name_str) > 50:
            return False
        if any(c in name_str for c in [':', ';', '/', '\\', '|', '=', '+', '<', '>', '*', '?', '!', '%', '$', '@', '#', '(', ')', '[', ']', '{', '}']):
            return False
        if not any(c.isupper() for c in name_str):
            return False
            
        lower_name = name_str.lower()
        exclude_name_words = {
            "the", "our", "their", "his", "her", "your", "my", "its", "this", "that", "these", "those", "and", "or",
            "contact", "person", "website", "email", "telephone", "phone",
            "meeting", "date", "dates", "document", "office", "registered", "corporate", "centre", "center",
            "business", "village", "taluka", "district", "state", "country", "city", "town", "street", "road",
            "building", "house", "flat", "plot", "area", "zone", "park", "industrial", "estate", "facility",
            "designated", "running", "lead", "book", "process", "price", "cap", "act", "law", "section", "page",
            "chapter", "annexure", "schedule", "appendix", "prospectus", "offer", "bid", "cagr", "pat", "margin",
            "ebitda", "net", "worth", "profit", "loss", "revenue", "income", "tax", "auditor", "auditors", "secretary", "compliance",
            "officer", "officers", "manager", "managers", "director", "directors", "promoter", "promoters", "share", "shares", "equity", "capital",
            "indian", "india", "american", "us", "usa", "sebi", "rbi", "bse", "nse", "registrar", "companies", "company",
            "member", "syndicate", "sponsor", "rta", "escrow", "bank", "financial", "securities", "wealth", "management",
            "limited", "private", "ltd", "pvt", "inc", "corp", "co", "llp", "insurance", "trust", "mutual", "fund",
            "board", "panel", "committee", "commission", "authority", "regulator", "regulatory", "government",
            "court", "tribunal", "high", "supreme", "bench", "legal", "counsel", "adviser", "advocate", "solicitor",
            "underwriter", "closing", "opening", "date", "time", "hour", "minute", "day", "week", "month", "year", "off", "farms",
            "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december",
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
            "general", "terms", "term", "related", "certain", "conventions", "convention", "forward", "looking",
            "statements", "statement", "risk", "factors", "factor", "information", "use", "financial", "market",
            "data", "currency", "presentation", "summary", "introduction", "definitions", "definition",
            "abbreviations", "abbreviation", "history", "industry", "overview", "business", "auditor", "auditors",
            "statutory", "audit", "committee", "bonus", "issue", "table", "contents", "content", "offer", "document",
            "key", "performance", "indicators", "index", "annexure", "schedule", "appendix", "other", "litigation",
            "material", "developments", "approvals", "rights", "restrictions", "valuation", "sources", "objects",
            "constitution", "structure", "dividend", "policy", "discussion", "analysis", "audited", "position",
            "cash", "flows", "flow", "description", "proceeds", "basis", "outstanding", "litigations", "government",
            "regulatory", "declarations", "declaration", "exhibits", "exhibit", "signing", "signatory", "signatories",
            "disclosure", "disclosures", "requirement", "requirements", "qualified", "institutional", "buyer", "buyers",
            "retail", "individual", "investor", "investors"
        }
        
        words = re.findall(r'\b[a-z]+\b', lower_name)
        if any(w in exclude_name_words for w in words):
            return False
                 
        if re.search(r'\d', name_str):
            return False
            
        # Parse lowercase in SpaCy to filter out generic adjectives, verbs, or common nouns (e.g. FOR SALE)
        doc = self.nlp(lower_name)
        if not any(token.pos_ == "PROPN" for token in doc):
            return False
            
        return True

    def _is_valid_company(self, entity_text):
        # Excludes known administrative roles and agencies from being redacted as companies
        entity_text = entity_text.strip()
        if not entity_text or len(entity_text) < 4:
            return False
            
        lower_text = entity_text.lower()
        exclude_keywords = [
            "government", "parliament", "sabha", "regulatory", "authority", "board", "commission", 
            "court", "department", "ministry", "tribunal", "committee", "council", "act", "law",
            "escrow", "public offer", "refund bank", "sponsor", "rta", "syndicate", "lead manager", 
            "running", "monitoring", "auditor", "registrar", "stock exchange", "clearing", "reserve bank",
            "sebi", "rbi", "promoter group", "underwriter", "collection bank", "bids", "closing", 
            "counsel", "adviser", "advocate", "solicitor", "member", "broker", "investor", "shareholder",
            "companies act", "memorandum", "association", "articles", "constitution", "building", "process", 
            "price", "cap", "facility", "regulations", "system", "scheme", "policy", "code", "index"
        ]
        
        words = lower_text.split()
        if any(w in exclude_keywords for w in words) or any(phrase in lower_text for phrase in ["collection bank", "escrow bank", "lead manager", "stock exchange", "monitoring agency", "companies act"]):
            return False
            
        if self._is_company(entity_text):
            clean_text = entity_text
            for suffix in self.company_suffixes:
                clean_text = re.sub(suffix, "", clean_text, flags=re.IGNORECASE)
            clean_text = clean_text.strip().strip(",.- ")
            if len(clean_text) < 3:
                return False
            return True
            
        return False

    def _is_valid_address(self, entity_text):
        # Excludes standard country names and generic facilities from being classified as addresses
        entity_text = entity_text.strip()
        if not entity_text or len(entity_text) < 3:
            return False
            
        lower_text = entity_text.lower()
        exclude_locations = {
            "india", "republic of india", "united states", "united states of america", "us", "usa", "u.s.", "u.s.a.",
            "united kingdom", "uk", "u.k.", "singapore", "germany", "france", "japan", "sweden", "uae", "u.a.e.",
            "maharashtra", "gujarat", "karnataka", "delhi", "goa", "pune", "mumbai", "bombay", "chennai", "kolkata",
            "bengaluru", "bangalore", "hyderabad", "new delhi", "gurugram", "noida", "haryana", "tamil nadu",
            "west bengal", "rajasthan", "punjab", "bihar", "uttar pradesh", "kerala", "andhra pradesh", "telangana",
            "facility", "supa facility", "chakan facility", "office", "registered office", "corporate office",
            "designated rta", "rta locations", "specified locations"
        }
        
        if lower_text in exclude_locations:
            return False
            
        words = entity_text.split()
        if len(words) == 1:
            return False
            
        invalid_addr_words = ["price", "cap", "process", "building", "meeting", "date", "act", "prospectus", "offer", "bid", "closing"]
        if any(w in words for w in invalid_addr_words):
            return False
            
        return True

    def detect(self, text, is_table_dob_column=False):
        # Main entry point for detecting all PII categories in a block of text
        if not text:
            return []
            
        matches = []
        
        for m in self.email_regex.finditer(text):
            matches.append({
                'start': m.start(),
                'end': m.end(),
                'type': 'EMAIL',
                'text': m.group()
            })
            
        for m in self.phone_regex.finditer(text):
            val = m.group().strip()
            digits = re.sub(r"\D", "", val)
            if len(digits) >= 7:
                matches.append({
                    'start': m.start(),
                    'end': m.end(),
                    'type': 'PHONE',
                    'text': val
                })
                
        for m in self.ssn_regex.finditer(text):
            matches.append({
                'start': m.start(),
                'end': m.end(),
                'type': 'SSN',
                'text': m.group()
            })
            
        for m in self.pan_regex.finditer(text):
            matches.append({
                'start': m.start(),
                'end': m.end(),
                'type': 'SSN',
                'text': m.group()
            })
            
        for m in self.aadhaar_regex.finditer(text):
            matches.append({
                'start': m.start(),
                'end': m.end(),
                'type': 'SSN',
                'text': m.group()
            })
            
        for m in self.cc_regex.finditer(text):
            val = m.group().strip()
            digits = re.sub(r"\D", "", val)
            if 13 <= len(digits) <= 19:
                matches.append({
                    'start': m.start(),
                    'end': m.end(),
                    'type': 'CREDIT_CARD',
                    'text': val
                })
                
        for m in self.ipv4_regex.finditer(text):
            parts = m.group().split('.')
            try:
                if all(0 <= int(p) <= 255 for p in parts):
                    matches.append({
                        'start': m.start(),
                        'end': m.end(),
                        'type': 'IP',
                        'text': m.group()
                    })
            except ValueError:
                pass
                
        for m in self.ipv6_regex.finditer(text):
            matches.append({
                'start': m.start(),
                'end': m.end(),
                'type': 'IP',
                'text': m.group()
            })
            
        for m in self.date_regex.finditer(text):
            start, end = m.start(), m.end()
            val = m.group()
            if is_table_dob_column or self._is_dob_context(text, start, end):
                matches.append({
                    'start': start,
                    'end': end,
                    'type': 'DOB',
                    'text': val
                })

        for m in self.name_title_regex.finditer(text):
            matches.append({
                'start': m.start(),
                'end': m.end(),
                'type': 'NAME',
                'text': m.group()
            })
        for m in self.name_caps_regex.finditer(text):
            matches.append({
                'start': m.start(),
                'end': m.end(),
                'type': 'NAME',
                'text': m.group()
            })

        spacy_doc = self.nlp(text)
        for ent in spacy_doc.ents:
            if ent.label_ == "PERSON":
                val = ent.text.strip()
                if len(val.split()) >= 2 or (val[0].isupper() and len(val) >= 3):
                    matches.append({
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'type': 'NAME',
                        'text': ent.text
                    })
            elif ent.label_ == "ORG":
                if self._is_company(ent.text):
                    matches.append({
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'type': 'COMPANY',
                        'text': ent.text
                    })
            elif ent.label_ in ["GPE", "LOC", "FAC"]:
                matches.append({
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'type': 'ADDRESS',
                    'text': ent.text
                })

        presidio_results = self.analyzer.analyze(text=text, language="en")
        for r in presidio_results:
            val = text[r.start:r.end]
            if r.entity_type == "PERSON" and r.score >= 0.7:
                matches.append({
                    'start': r.start,
                    'end': r.end,
                    'type': 'NAME',
                    'text': val
                })
            elif r.entity_type == "EMAIL_ADDRESS" and r.score >= 0.7:
                matches.append({
                    'start': r.start,
                    'end': r.end,
                    'type': 'EMAIL',
                    'text': val
                })
            elif r.entity_type == "PHONE_NUMBER" and r.score >= 0.7:
                matches.append({
                    'start': r.start,
                    'end': r.end,
                    'type': 'PHONE',
                    'text': val
                })
            elif r.entity_type == "LOCATION" and r.score >= 0.7:
                matches.append({
                    'start': r.start,
                    'end': r.end,
                    'type': 'ADDRESS',
                    'text': val
                })
            elif r.entity_type == "CREDIT_CARD" and r.score >= 0.7:
                matches.append({
                    'start': r.start,
                    'end': r.end,
                    'type': 'CREDIT_CARD',
                    'text': val
                })
            elif r.entity_type == "IP_ADDRESS" and r.score >= 0.7:
                matches.append({
                    'start': r.start,
                    'end': r.end,
                    'type': 'IP',
                    'text': val
                })
            elif r.entity_type == "US_SSN" and r.score >= 0.7:
                matches.append({
                    'start': r.start,
                    'end': r.end,
                    'type': 'SSN',
                    'text': val
                })

        merged_matches = self._merge_consecutive_addresses(text, matches)
        
        valid_matches = []
        for match in merged_matches:
            val = match['text']
            t = match['type']
            
            if t == 'NAME':
                if self._is_valid_name(val):
                    valid_matches.append(match)
            elif t == 'COMPANY':
                if self._is_valid_company(val):
                    valid_matches.append(match)
            elif t == 'ADDRESS':
                if self._is_valid_address(val):
                    valid_matches.append(match)
            else:
                valid_matches.append(match)
                
        final_matches = self._resolve_overlaps(valid_matches)
        return final_matches

    def _get_type_priority(self, entity_type):
        # Resolves type priority overlaps (e.g. Email is prioritized over phone number boundary)
        priorities = {
            'EMAIL': 1, 'CREDIT_CARD': 1, 'SSN': 1, 'IP': 1, 'DOB': 1,
            'NAME': 2,
            'COMPANY': 3, 'ADDRESS': 4, 'PHONE': 5
        }
        return priorities.get(entity_type, 6)

    def _resolve_overlaps(self, matches):
        # Merges and resolves overlapping ranges, preserving the longest and highest-priority matches
        sorted_matches = sorted(
            matches, 
            key=lambda x: (x['start'], -(x['end'] - x['start']), self._get_type_priority(x['type']))
        )
        
        resolved = []
        for match in sorted_matches:
            overlap = False
            for r in resolved:
                if max(match['start'], r['start']) < min(match['end'], r['end']):
                    overlap = True
                    break
            if not overlap:
                resolved.append(match)
                
        return sorted(resolved, key=lambda x: x['start'])

    def _merge_consecutive_addresses(self, text, matches):
        # Combines neighboring location matches if separated only by spacing or punctuation
        if not matches:
            return []
            
        merged = []
        current = None
        
        for match in matches:
            if match['type'] == 'ADDRESS':
                if current is None:
                    current = dict(match)
                else:
                    between = text[current['end']:match['start']]
                    if re.match(r"^[\s,;\-–—]*$", between):
                        current['end'] = match['end']
                        current['text'] = text[current['start']:match['end']]
                    else:
                        merged.append(current)
                        current = dict(match)
            else:
                if current is not None:
                    merged.append(current)
                    current = None
                merged.append(match)
                
        if current is not None:
            merged.append(current)
            
        return sorted(merged, key=lambda x: x['start'])
