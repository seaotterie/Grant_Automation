"""
NameNormalizer — strip credentials/honorifics/suffixes and produce stable person hashes.
"""

import re
import hashlib
import unicodedata


class NameNormalizer:
    CREDENTIALS = {
        "phd", "md", "jd", "cpa", "mba", "msw", "esq", "cfo", "ceo", "coo", "cto",
        "cfre", "mpa", "mph", "edd", "dmin", "lcsw", "lpc", "rn", "np", "pa",
        "facp", "fache", "shrm", "pmp", "cfp", "cfa", "mha", "drph",
    }
    HONORIFICS = {"dr", "mr", "mrs", "ms", "rev", "hon", "prof", "sir", "lady"}
    SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v", "2nd", "3rd"}

    def normalize(self, name: str) -> str:
        """Strip credentials/honorifics/suffixes, lowercase, collapse to 'first last'."""
        if not name:
            return ""

        # Unicode normalize
        name = unicodedata.normalize("NFKD", name)
        # Remove parenthetical content: "John Smith (Board Chair)" → "John Smith"
        name = re.sub(r"\(.*?\)", "", name)
        # Remove content after comma (often suffix): "Smith, Jr." handled below
        # Split on commas and take the first meaningful part
        parts = [p.strip() for p in name.split(",")]
        # Reassemble: if second part looks like a suffix keep it for processing
        name = " ".join(parts)

        # Remove punctuation except spaces and hyphens
        name = re.sub(r"[^\w\s\-]", " ", name)

        tokens = name.lower().split()
        filtered = []
        for token in tokens:
            token_clean = token.strip("-")
            if (
                token_clean in self.CREDENTIALS
                or token_clean in self.HONORIFICS
                or token_clean in self.SUFFIXES
            ):
                continue
            if not token_clean or not any(c.isalpha() for c in token_clean):
                continue
            filtered.append(token_clean)

        if not filtered:
            return name.lower().strip()

        # Collapse to first + last only if more than 2 tokens
        if len(filtered) >= 3:
            return f"{filtered[0]} {filtered[-1]}"
        return " ".join(filtered)

    def person_hash(self, name: str) -> str:
        """sha256(normalize(name))[:16]"""
        normalized = self.normalize(name)
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def membership_id(self, name: str, org_ein: str) -> str:
        """sha256(normalize(name) + org_ein)[:16]"""
        normalized = self.normalize(name)
        key = f"{normalized}|{org_ein or ''}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]
