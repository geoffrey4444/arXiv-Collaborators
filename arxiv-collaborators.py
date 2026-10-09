#!/bin/env python

import csv
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime as dt
from enum import Enum

import feedparser as fp

remapped_names = {
    "Béla Szilágyi": "Bela Szilagyi",
    "Cristóbal Armaza": "Cristobal Armaza",
    "Daniel A. Hemberger": "Daniel Hemberger",
    "Francois Hebert": "François Hébert",
    "Gabriel S. Bonilla": "Marceline S. Bonilla",
    "Hannes Rüter": "Hannes R. Rüter",
    "Harald Pfeiffer": "Harald P. Pfeiffer",
    "Isabella Pretto": "Isabella G. Pretto",
    "Larry Kidder": "Lawrence E. Kidder",
    "Mark A Scheel": "Mark A. Scheel",
    "Matthew Duez": "Matthew D. Duez",
    "Nils Deppe": "Deppe_Nils",
    "Nils Fischer": "Nils L. Vu",
    "Nils L. Fischer": "Nils L. Vu",
    "Nils Vu": "Nils L. Vu",
    "Saul Teukolsky": "Saul A. Teukolsky",
    "Tom Wlodarczyk": "Tom Włodarczyk",
}

affiliations = {
    "Aaron B. Zimmerman": "UT Austin",
    "Abhishek Ravishankar": "University of Massachusetts Dartmouth",
    "Adam Pound": "University of Southampton",
    "Adhrit Ravichandran": "University of Massachusetts Dartmouth",
    "Alessandro Nagar": "INFN Sezione di Torino",
    "Alexander Carpenter": "Cal State Fullerton",
    "Alexander Chernoglazov": "University of Maryland",
    "Alexandra Macedo": "Cal State Fullerton",
    "Alyssa Garcia": "Cal State Fullerton",
    "Andrea Ceja": "Cal State Fullerton",
    "Andrew R. Frey": "University of Winnipeg",
    "Aniket Khairnar": "University of Mississippi",
    "Anıl Zenginoğlu": "University of Maryland",
    "Antoni Ramos-Buades": "University of the Balearic Islands",
    "Arnab Dhani": "Penn State University",
    "Azer Afram": "Cal State Fullerton",
    "Bela Szilagyi": "Caltech",
    "Brad Cownden": "Jagiellonian University",
    "C. Melize Ferrus": "King's College London:",
    "Charles J. Woodford": "University of Toronto",
    "Cristobal Armaza": "Cornell University",
    "Daniel Hemberger": "NASA JPL",
    "Daniel Tellez": "Cal State Fullerton",
    "Daniel Vieira": "Cornell University",
    "Dante A. B. Iozzo": "Cornell University",
    "David Maibach": "University of Heidelberg",
    "David Vartanyan": "University of Idaho",
    "Davide Gerosa": "Universitá degli Studi di Milano-Bicocca",
    "Denyz Melchor": "UCLA",
    "Dongjun Li": "University of Illinois Urbana-Champaign",
    "Dongze Sun": "Caltech",
    "Eamonn O'Shea": "Cornell University",
    "Elias R. Most": "Caltech",
    "Eric Thrane": "Monash University",
    "Evan Foley": "Cal State Fullerton",
    "Francois Foucart": "University of New Hampshire",
    "Frans Pretorius": "Princeton University",
    "François Hébert": "JCSDA",
    "Geoffrey Lovelace": "Cal State Fullerton",
    "Gregorio Carullo": "University of Birmingham",
    "Gregory B. Cook": "Wake Forest University",
    "Guillermo Lara": "Albert Einstein Institute",
    "Guido Da Re": "Caltech",
    "Halston Lim": "MIT",
    "Hannes R. Rüter": "University of Coimbra",
    "Harald P. Pfeiffer": "Albert Einstein Institute",
    "Haroon Khan": "Cal State Fullerton",
    "Harrison Siegel": "Columbia University & Flatiron Institute",
    "Heather Fong": "University of Tokyo",
    "Hengrui Zhu": "Princeton University",
    "Henri Inchauspé": "KU Leuven",
    "Himanshu Chaudhary": "Caltech",
    "Iago B. Mendes": "Oberlin College",
    "Ian Hinder": "Albert Einstein Institute",
    "Isaac Legred": "University of Illinois Urbana-Champaign",
    "Isabella G. Pretto": "Caltech",
    "Isha Anantpurkar": "UCSB",
    "Jason S. Guo": "Cornell University",
    "Jennifer Sanchez": "Cal State Fullerton",
    "Jiaxi Wu": "Caltech",
    "Jonathan Blackman": "Caltech",
    "Jooheon Yoo": "Cornell University",
    "Jordan Moxon": "Caltech",
    "Justin L. Ripley": "Johns Hopkins University",
    "Károly Zoltán Csukás": " Magyar Tudományos Akadémia Wigner Fizikai Kutatóközpont Részecske-és Magfizikai Intézet",
    "Katerina Chatziioannou": "Caltech",
    "Katie Rink": "UT Austin",
    "Keefe Mitman": "Caltech",
    "Ken Z. Jones": "Cal State Fullerton",
    "Kevin Barkett": "Caltech",
    "Kevin Kuper": "Cal State Fullerton",
    "Kuo-Chuan Pan": "National Tsing Hua University",
    "Kyle C. Nelli": "Caltech",
    "Kyle Pannone": "Cal State Fullerton",
    "Lam Hui": "Columbia University",
    "Lavinia Heisenberg": "University of Heidelberg",
    "Lawrence E. Kidder": "Cornell University",
    "Leda Gao": "Wake Forest University",
    "Leo C. Stein": "University of Mississippi",
    "Leor Barack": "University of Southampton",
    "Ling Sun": "The Australian National University",
    "Lorena Magaña Zertuche": "Niels Bohr Institute",
    "Luisa T. Buchman": "Washington State University, Pullman",
    "Macarena Lagos": "Columbia University",
    "Marceline S. Bonilla": "College of Marin",
    "Maria Okounkova": "Pasadena City College",
    "Marina De Amicis": "Perimeter Institute for Theoretical Physics",
    "Marissa Walker": "Christopher Newport University",
    "Mark A. Scheel": "Caltech",
    "Marlo Morales": "Washington State University",
    "Matteo Boschini": "Albert Einstein Institute",
    "Matthew D. Duez": "Washington State University",
    "Matthew Giesler": "Cornell University",
    "Max Miller": "University of New Hampshire",
    "Maxence Corman": "Albert Einstein Institute",
    "Maximiliano Isi": "Flatiron Institute",
    "Md Arif Shaikh": "Vidyasagar University",
    "Mekhi Dhesi": "University of Southampton",
    "Michael A. Pajkos": "Caltech",
    "Michael Boyle": "Cornell University",
    "Naritaka Oshita": "Kyoto University",
    "Neev Khera": "Penn State University",
    "Nicholas Demos": "Cal State Fullerton",
    "Nicholas Demos": "MIT",
    "Nicholas J. Corso": "Cornell University",
    "Nikolas A. Wittek": "Albert Einstein Institute",
    "Nils L. Vu": "Caltech",
    "Noora Ghadiri": "University of Illinois Urbana-Champaign",
    "Nousha Afshari": "Cal State Fullerton",
    "Oliver Long": "Albert Einstein Institute",
    "Patricia Schmidt": "University of Birmingham",
    "Paul D. Lasky": "Monash University",
    "Peter J. Nee": "Albert Einstein Institute",
    "Peter James Nee": "Albert Einstein Institute",
    "Prayush Kumar": "Tata Institute of Fundamental Research",
    "Qingwen Wang": "Perimeter Institute",
    "Reza Katebi": "Cal State Fullerton",
    "Robert Owen": "Oberlin College",
    "Samuel Rodriguez": "Cal State Fullerton",
    "Sarah Habib": "Caltech",
    "Saul A. Teukolsky": "Cornell University",
    "Scott E. Field": "University of Massachusetts Dartmouth",
    "Sean M. Couch": "Michigan State University",
    "Sebastiano Bernuzzi": "Friedrich Schiller University in Jena",
    "Serguei Ossokine": "Albert Einstein Institute",
    "Sierra Thomas": "Syracuse University",
    "Simone Albanesi": "Friedrich Schiller University in Jena",
    "Sizheng Ma": "Perimeter Institute",
    "Steven J. VanCamp": "Michigan State University",
    "Tanja Hinderer": "Utrecht University",
    "Taylor Knapp": "Caltech",
    "Teagan A. Clarke": "Monash University",
    "Teresita Ramirez": "Northwestern",
    "Teresita Ramirez-Aguilar": "Northwestern University",
    "Tom Włodarczyk": "Albert Einstein Institute",
    "Tommaso De Lorenzo": "Cornell University",
    "Tony Chu": "Princeton University",
    "Tousif Islam": "Kavli Institute for Theoretical Physics, University of California Santa Barbara",
    "Vijay Varma": "University of Massachusetts Dartmouth",
    "Vitor Cardoso": "Niels Bohr Institute & Técnico",
    "Will M. Farr": "Flatiron Institute & Stony Brook University",
    "William Throwe": "Cornell University",
    "Yitian Chen": "Cornell University",
    "Yoonsoo Kim": "Caltech",
}


class Format(Enum):
    NsfAccess = 1
    NsfProposal = 2


def get_initials(name):
    """Take a name, First Middles Last -> F. M. Last
    """
    split_name = name.strip().split()
    initial_name = ""
    for i in range(len(split_name) - 1):
        initial_name += split_name[i][0].upper() + '. '
    return initial_name + split_name[-1]  # add last name


def get_last_name_first(name):
    """Take a name, First Middle Last -> Last First M.
    """
    split_name = name.strip().split()
    initial_name = str(split_name[0]) + " "
    for i in range(1, len(split_name) - 1):
        initial_name += split_name[i][0].upper() + '. '
    return split_name[-1] + ", " + initial_name  # add last name


def ascii_fold(text):
    """Strip accents so that e.g. 'Hébert' and 'Hebert' compare equal."""
    return ''.join(c for c in unicodedata.normalize('NFKD', text)
                   if not unicodedata.combining(c))


def last_first_to_first_last(name):
    """Take a name, Last, First Middle -> First Middle Last

    ADS and INSPIRE use 'Last, First' while arXiv uses 'First Last'. Suffixes
    such as 'Jr.' are dropped since get_initials assumes the last token is the
    last name.
    """
    parts = [p.strip() for p in name.split(',')]
    if len(parts) < 2 or not parts[1]:
        return name.strip()
    return f'{parts[1]} {parts[0]}'


def name_key(name):
    """Key used to identify the same person across name variants and sources.

    Also accepts arXiv search names like 'Deppe_Nils' or 'Deppe_N'.
    """
    if '_' in name and ' ' not in name.strip():
        last, first = name.strip().split('_', 1)
        name = f'{first} {last}'
    # 'Dante A.B. Iozzo' -> 'Dante A. B. Iozzo'
    name = re.sub(r'\.(?=\S)', '. ', name)
    return ascii_fold(get_initials(name)).lower()


def is_collaboration(name):
    return re.search(r'\b(collaborations?|consortium)\b', name,
                     re.IGNORECASE) is not None


# Only these collaborations are candidates for the review file. A large
# author list by itself (e.g. Cosmic Explorer or SXS) is not sufficient.
COLLABORATION_PATTERNS = {
    'LIGO Scientific Collaboration': r'\b(LIGO|LSC|LVC|LVK)\b',
    'LISA Collaboration': r'\bLISA\b|\bLaser Interferometer Space Antenna\b',
    'Einstein Telescope Collaboration': r'\bEinstein Telescope\b|\bET\b',
}
MIN_COLLABORATION_AUTHORS = 50
REVIEW_COLUMNS = ['arxiv_url', 'scix_url', 'inspirehep_url', 'first_author',
                  'collaboration', 'title', 'omit']


def author_is_group(name):
    """Recognize corporate authors without confusing e.g. Lisa Randall."""
    return (is_collaboration(name)
            or name.strip().lower() in {
                'ligo', 'ligo scientific', 'lsc', 'lvc', 'lvk', 'lisa',
                'et', 'einstein telescope', 'cosmic explorer', 'virgo',
                'kagra'})


def arxiv_identifier(value):
    value = value.removeprefix('arXiv:').removeprefix('arxiv:')
    return re.sub(r'v\d+$', '', value)


def record_id_from_url(url):
    """Match saved links despite HTTP/HTTPS, versions, and ADS/SciX aliases."""
    parsed = urllib.parse.urlparse(url.strip())
    path = urllib.parse.unquote(parsed.path).rstrip('/')
    host = (parsed.hostname or '').lower()
    if host in {'arxiv.org', 'www.arxiv.org', 'export.arxiv.org'}:
        if path.startswith('/abs/'):
            return 'arxiv:' + arxiv_identifier(path[len('/abs/'):])
    elif host in {'scixplorer.org', 'www.scixplorer.org',
                  'ui.adsabs.harvard.edu', 'adsabs.harvard.edu'}:
        if path.startswith('/abs/'):
            return 'ads:' + path[len('/abs/'):].removesuffix('/abstract')
    elif host in {'inspirehep.net', 'www.inspirehep.net'}:
        match = re.fullmatch(r'/(?:api/)?literature/(\d+)', path)
        if match:
            return 'inspire:' + match[1]
    return None


def normalize_title(title):
    return re.sub(r'[^a-z0-9]', '', ascii_fold(title).lower())


# Words identifying the organization in a raw affiliation string, in order of
# preference, e.g. 'Cornell University' is preferred over 'Cornell Center for
# Astrophysics and Planetary Science'.
ORGANIZATION_PATTERNS = [
    r'Universi', r'College|Polytechn|Hochschule|[EÉ]cole', r'Institut',
    r'Laborator|Observator|Cent(er|re)\b|Foundation|Agency|NASA'
]


def extract_organization(raw_affiliation):
    """'Theoretical Astrophysics 350-17, California Institute of Technology,
    Pasadena, CA 91125, USA' -> 'California Institute of Technology'
    """
    segments = [s.strip() for s in raw_affiliation.split(',')]
    for pattern in ORGANIZATION_PATTERNS:
        for segment in segments:
            if re.search(pattern, segment, re.IGNORECASE):
                return segment
    # E.g. 'RIKEN iTHEMS, Wako, Saitama, 351-0198, Japan' -> 'RIKEN iTHEMS'
    return segments[0]


def unique(items):
    return list(dict.fromkeys(items))


@dataclass
class Author:
    name: str
    # Organization names, e.g. ['California Institute of Technology']
    affiliations: list = field(default_factory=list)
    # True if all affiliations were matched to an institution database rather
    # than guessed from the raw affiliation string.
    curated: bool = False
    source: str = ''


@dataclass
class Paper:
    title: str
    # (year, month, day)
    date: tuple
    link: str
    source: str
    authors: list
    # Identifiers used to match the same paper across sources, e.g.
    # 'arxiv:2412.06887', 'doi:10.1103/...', 'title:...'
    ids: set = field(default_factory=set)
    sources: set = field(default_factory=set)
    doctype: str = ''
    collaborations: set = field(default_factory=set)
    links: dict = field(default_factory=dict)
    author_count: int = 0
    first_author: str = ''
    first_author_source: str = ''

    def __post_init__(self):
        self.sources.add(self.source)
        if self.link:
            self.links.setdefault(self.source, self.link)
        self.collaborations |= {
            a.name for a in self.authors if author_is_group(a.name)
        }
        people = [a.name for a in self.authors
                  if any(c.isalpha() for c in a.name)
                  and not author_is_group(a.name)]
        if self.authors and not people and self.author_count <= len(self.authors):
            # Some sources count a corporate author as one person.
            self.author_count = 0
        # Count within each source, before absorb concatenates author lists.
        self.author_count = max(self.author_count,
                                len({name_key(n) for n in people}))
        if not self.first_author and people:
            self.first_author = people[0]
        if self.first_author and not self.first_author_source:
            self.first_author_source = self.source
        if self.title:
            self.ids.add('title:' + normalize_title(self.title))
        for link in self.links.values():
            record_id = record_id_from_url(link)
            if record_id:
                self.ids.add(record_id)

    def absorb(self, other):
        """Merge another record of the same paper into this one."""
        self.ids |= other.ids
        self.sources |= other.sources
        self.authors = self.authors + other.authors
        self.collaborations |= other.collaborations
        self.author_count = max(self.author_count, other.author_count)
        for source, link in other.links.items():
            self.links.setdefault(source, link)
        # Prefer dates and links in the order arXiv > INSPIRE > ADS. The arXiv
        # date matches what the script has always used, INSPIRE dates have a
        # day, and ADS pubdates are journal publication months.
        priority = ['arxiv', 'inspire', 'ads']
        if other.first_author and (
                not self.first_author or
                priority.index(other.first_author_source)
                < priority.index(self.first_author_source)):
            self.first_author = other.first_author
            self.first_author_source = other.first_author_source
        if priority.index(other.source) < priority.index(self.source):
            self.date, self.link, self.source = (other.date, other.link,
                                                 other.source)
        if not self.doctype:
            self.doctype = other.doctype


def get_json(url, params, headers=None):
    request = urllib.request.Request(
        url + '?' + urllib.parse.urlencode(params), headers=headers or {})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def parse_date(date_str):
    """'2024-12-09', '2024-12-00', '2024-12', or '2024' -> (2024, 12, 9)"""
    parts = [int(p) for p in date_str.split('-')[:3]]
    parts += [1] * (3 - len(parts))
    return tuple(max(p, 1) for p in parts)


def fetch_arxiv(author):
    arXiv_url = 'http://export.arxiv.org/api/query?search_query=au:{0}&id_list=&start=0&max_results=10000'
    arxiv_feed = fp.parse(arXiv_url.format(author))

    papers = []
    for paper in arxiv_feed.entries:
        # Use last updated to estimate the publish date/year
        updated = paper.updated_parsed
        arxiv_id = arxiv_identifier(paper.id.split('/abs/')[-1])
        ids = {'arxiv:' + arxiv_id}
        if 'arxiv_doi' in paper:
            ids.add('doi:' + paper.arxiv_doi.lower())
        papers.append(
            Paper(title=paper.title,
                  date=(updated.tm_year, updated.tm_mon, updated.tm_mday),
                  link=paper.link,
                  source='arxiv',
                  authors=[
                      Author(name=a.name, source='arxiv')
                      for a in paper.authors
                  ],
                  ids=ids))
    return papers


def fetch_ads_institutions():
    """Get the ADS canonical affiliation table: id -> (name, parent ids).

    See https://github.com/adsabs/CanonicalAffiliations
    """
    url = ('https://raw.githubusercontent.com/adsabs/CanonicalAffiliations/'
           'master/parent_child.tsv')
    try:
        with urllib.request.urlopen(url, timeout=120) as response:
            lines = response.read().decode('utf-8').splitlines()
    except OSError as error:
        print(f'Warning: Could not download the ADS institution table, so '
              f'departments will not be mapped to their institution: {error}',
              file=sys.stderr)
        return {}
    institutions = {}
    for line in lines[1:]:
        parent, child, _, name = line.split('\t')[:4]
        institutions.setdefault(child, (name, []))[1].append(parent)
    return institutions


def ads_institution_name(aff_id, institutions):
    """Map an ADS affiliation ID to its institution, e.g. 'University of
    Toronto, Department of Physics' -> 'University of Toronto, Canada'.

    Only goes to the parent if the child's name contains the parent's name, so
    e.g. 'California State University, Fullerton' does not become 'California
    State University System'.
    """
    name, parents = institutions[aff_id]
    parents = [p for p in parents if p in institutions]
    if len(parents) == 1:
        parent_name = institutions[parents[0]][0]
        if (ascii_fold(parent_name.split(',')[0]).lower()
                in ascii_fold(name).lower()):
            return parent_name
    return name


def ads_author(name, raw_affs, canonical_affs, aff_ids, institutions):
    """Build an Author from the per-author ADS affiliation fields.

    Each field has one entry per author, with multiple affiliations separated
    by '; ' and unmatched affiliations given as '-'.
    """
    raw_affs = [a.strip() for a in raw_affs.split(';')]
    canonical_affs = canonical_affs.split('; ')
    aff_ids = aff_ids.split('; ')
    if not (len(raw_affs) == len(canonical_affs) == len(aff_ids)):
        # Can't tell which raw affiliation goes with which ID, so only use
        # the raw affiliations if nothing was matched.
        canonical_affs = [a for a in canonical_affs if a != '-']
        aff_ids = [a for a in aff_ids if a != '-']
        if canonical_affs or aff_ids:
            raw_affs = []
        length = max(len(raw_affs), len(canonical_affs), len(aff_ids))
        raw_affs += ['-'] * (length - len(raw_affs))
        canonical_affs += ['-'] * (length - len(canonical_affs))
        aff_ids += ['-'] * (length - len(aff_ids))

    affiliations = []
    curated = True
    for raw, canonical, aff_id in zip(raw_affs, canonical_affs, aff_ids):
        if aff_id in institutions:
            affiliations.append(ads_institution_name(aff_id, institutions))
        elif re.search(r'[A-Za-z]{3,}', canonical):
            affiliations.append(canonical)
        elif re.search(r'[A-Za-z]{3,}', raw):
            affiliations.append(extract_organization(raw))
            curated = False
    return Author(name=last_first_to_first_last(name),
                  affiliations=unique(affiliations),
                  curated=curated and bool(affiliations),
                  source='ads')


def fetch_ads(orcid, token, min_year):
    """Query ADS/SciX for all records claimed by or tagged with an ORCID."""
    url = 'https://api.adsabs.harvard.edu/v1/search/query'
    headers = {'Authorization': f'Bearer {token}'}
    institutions = fetch_ads_institutions()
    papers = []
    start = 0
    while True:
        result = get_json(
            url, {
                'q': f'orcid:{orcid} year:[{min_year} TO *]',
                'fl': 'author,aff,aff_canonical,aff_id,title,pubdate,'
                'identifier,doi,bibcode,doctype,author_count',
                'rows': 2000,
                'start': start,
                'sort': 'date desc',
            }, headers)['response']
        for doc in result['docs']:
            ids = {'ads:' + doc['bibcode']}
            for identifier in doc.get('identifier', []):
                if identifier.startswith('arXiv:'):
                    ids.add('arxiv:' + arxiv_identifier(identifier))
            ids |= {'doi:' + doi.lower() for doi in doc.get('doi', [])}
            names = doc.get('author', [])

            def per_author(field_name):
                values = doc.get(field_name, [])
                return values + ['-'] * (len(names) - len(values))

            papers.append(
                Paper(title=(doc.get('title') or [''])[0],
                      date=parse_date(doc['pubdate']),
                      link='https://ui.adsabs.harvard.edu/abs/' +
                      doc['bibcode'],
                      source='ads',
                      authors=[
                          ads_author(*fields, institutions)
                          for fields in zip(names, per_author('aff'),
                                            per_author('aff_canonical'),
                                            per_author('aff_id'))
                      ],
                      ids=ids,
                      author_count=doc.get('author_count', 0),
                      doctype=doc.get('doctype', '')))
        start += len(result['docs'])
        if not result['docs'] or start >= result['numFound']:
            return papers


def inspire_bai_from_orcid(orcid):
    """Look up the INSPIRE author identifier (e.g. 'Nils.Deppe.1').

    INSPIRE's literature search does not support searching by ORCID directly.
    """
    hits = get_json('https://inspirehep.net/api/authors', {
        'q': f'ids.value:{orcid}',
        'fields': 'ids'
    })['hits']['hits']
    for hit in hits:
        for author_id in hit['metadata'].get('ids', []):
            if author_id['schema'] == 'INSPIRE BAI':
                return author_id['value']
    return None


def fetch_inspire_institutions(institution_ids):
    """Map INSPIRE institution record IDs to the top-level organization name,
    e.g. 'Division of Physics, Mathematics and Astronomy' at Caltech ->
    'California Institute of Technology'.
    """
    institution_ids = sorted(institution_ids)
    names = {}
    chunk_size = 100
    for i in range(0, len(institution_ids), chunk_size):
        chunk = institution_ids[i:i + chunk_size]
        hits = get_json(
            'https://inspirehep.net/api/institutions', {
                'q': f'control_number:({" OR ".join(chunk)})',
                'fields': 'control_number,institution_hierarchy,legacy_ICN,'
                'addresses.cities',
                'size': chunk_size,
            })['hits']['hits']
        for hit in hits:
            metadata = hit['metadata']
            name = inspire_institution_name(metadata)
            if name:
                names[str(metadata['control_number'])] = name
    return names


def inspire_institution_name(metadata):
    """Name an INSPIRE institution record, e.g. 'Kavli Institute for
    Theoretical Physics, University of California, Santa Barbara'.

    The hierarchy goes from the most specific to the most general, e.g.
    ['Department of Physics', 'University of Illinois'] or ['Sezione di
    Torino', 'Istituto Nazionale di Fisica Nucleare']. Departments are dropped
    but other sub-units (institutes, sections, ...) are kept.
    """
    hierarchy = [h['name'] for h in metadata.get('institution_hierarchy', [])]
    if not hierarchy:
        return metadata.get('legacy_ICN')
    parts = [hierarchy[-1]] + [
        h for h in hierarchy[:-1]
        if not re.match(r'(Dep(t|artment)|Division|School|Faculty|Cent(er|re|ro))\b', h)
    ]
    name = ', '.join(reversed(parts)) if len(parts) > 1 else parts[0]
    # Multi-campus systems like 'University of California' need the campus
    cities = [
        city for address in metadata.get('addresses', [])
        for city in address.get('cities', [])
    ]
    if (re.fullmatch(r'(The )?University of [A-Z][a-z]+( [A-Z][a-z]+)?',
                     hierarchy[-1]) and cities and cities[0] not in name):
        name += ', ' + cities[0]
    return name


def inspire_author(author, institutions):
    affiliations = []
    curated = True
    for affiliation in author.get('affiliations', []):
        institution_id = affiliation.get('record', {}).get('$ref',
                                                           '').split('/')[-1]
        if institution_id in institutions:
            affiliations.append(institutions[institution_id])
    if not affiliations:
        # Not linked to an institution record, so guess from the raw string
        affiliations = [
            extract_organization(a['value'])
            for a in author.get('raw_affiliations', [])
        ]
        curated = False
    return Author(name=last_first_to_first_last(author['full_name']),
                  affiliations=unique(affiliations),
                  curated=curated and bool(affiliations),
                  source='inspire')


def fetch_inspire(bai, min_year):
    url = 'https://inspirehep.net/api/literature'
    hits = []
    page = 1
    while True:
        result = get_json(
            url, {
                'q': f'a {bai} and de > {min_year - 1}',
                'fields': 'control_number,titles.title,authors.full_name,'
                'authors.affiliations,authors.raw_affiliations,'
                'arxiv_eprints.value,dois.value,earliest_date,document_type,'
                'collaborations.value,author_count,external_system_identifiers',
                'size': 250,
                'page': page,
                'sort': 'mostrecent',
            })
        hits += result['hits']['hits']
        if 'next' not in result.get('links', {}):
            break
        page += 1

    institutions = fetch_inspire_institutions({
        affiliation['record']['$ref'].split('/')[-1]
        for hit in hits for author in hit['metadata'].get('authors', [])
        for affiliation in author.get('affiliations', [])
        if 'record' in affiliation
    })

    papers = []
    for hit in hits:
        metadata = hit['metadata']
        ids = {'arxiv:' + arxiv_identifier(e['value'])
               for e in metadata.get('arxiv_eprints', [])}
        ids.add('inspire:' + str(metadata['control_number']))
        ids |= {'doi:' + d['value'].lower()
                for d in metadata.get('dois', [])}
        ids |= {'ads:' + identifier['value']
                for identifier in metadata.get('external_system_identifiers', [])
                if identifier['schema'] == 'ADS'}
        papers.append(
            Paper(title=(metadata.get('titles')
                         or [{'title': ''}])[0]['title'],
                  date=parse_date(metadata['earliest_date']),
                  link='https://inspirehep.net/literature/' +
                  str(metadata['control_number']),
                  source='inspire',
                  authors=[
                      inspire_author(a, institutions)
                      for a in metadata.get('authors', [])
                  ],
                  ids=ids,
                  collaborations={c['value'] for c in
                                  metadata.get('collaborations', [])},
                  author_count=metadata.get('author_count', 0),
                  doctype=','.join(metadata.get('document_type', []))))
    return papers


def merge_papers(papers):
    """Merge records of the same paper (matched by arXiv ID, DOI, or title)."""
    merged = []
    id_to_index = {}
    for paper in papers:
        matches = sorted(
            {id_to_index[i]
             for i in paper.ids if i in id_to_index})
        if not matches:
            target = len(merged)
            merged.append(paper)
        else:
            target = matches[0]
            merged[target].absorb(paper)
            # The new record may link two records we thought were distinct.
            for other in matches[1:]:
                merged[target].absorb(merged[other])
                merged[other] = None
        for i in merged[target].ids:
            id_to_index[i] = target
    return [paper for paper in merged if paper is not None]


def likely_full_collaborations(paper):
    """Return target names supported by metadata or corporate authors.

    Do not infer a collaboration from a title, an affiliation, or the length
    of an author list alone. Zero means only a group was listed, or the count
    is unavailable, so include it for manual review.
    """
    if 0 < paper.author_count < MIN_COLLABORATION_AUTHORS:
        return []
    return [name for name, pattern in COLLABORATION_PATTERNS.items()
            if any(re.search(pattern, group, re.IGNORECASE)
                   for group in paper.collaborations)]


def review_row(paper):
    def identifier(prefix):
        return next((i[len(prefix):] for i in sorted(paper.ids)
                     if i.startswith(prefix)), '')

    arxiv_id = identifier('arxiv:')
    bibcode = identifier('ads:')
    inspire_id = identifier('inspire:')
    # Keep the file one physical line per paper even with multiline titles.
    return dict(zip(REVIEW_COLUMNS, [
        'https://arxiv.org/abs/' + arxiv_id if arxiv_id else '',
        'https://scixplorer.org/abs/' + urllib.parse.quote(bibcode, safe='.:')
        + '/abstract' if bibcode else '',
        'https://inspirehep.net/literature/' + inspire_id if inspire_id else '',
        ' '.join(paper.first_author.split()),
        '; '.join(' '.join(group.split())
                  for group in sorted(paper.collaborations)),
        ' '.join(paper.title.split()),
        'Y',
    ]))


def review_row_keys(row):
    keys = {record_id_from_url(row[column]) for column in REVIEW_COLUMNS[:3]}
    keys.discard(None)
    if row['title'].strip():
        keys.add('title:' + normalize_title(row['title']))
    return keys


def read_collaboration_review(path):
    """Read decisions without modifying any existing rows."""
    try:
        with open(path, newline='', encoding='utf-8-sig') as stream:
            reader = csv.DictReader(stream, delimiter='\t')
            if reader.fieldnames is None:
                return []
            if reader.fieldnames != REVIEW_COLUMNS:
                raise ValueError(f'{path}: expected TSV columns: '
                                 + '\t'.join(REVIEW_COLUMNS))
            rows = list(reader)
    except FileNotFoundError:
        return []
    for line, row in enumerate(rows, 2):
        if (None in row or any(v is None for v in row.values())
                or row['omit'].strip().upper() not in {'Y', 'N'}):
            raise ValueError(f'{path}: invalid row {line}; expected seven '
                             'columns and omit Y or N')
        if not review_row_keys(row):
            raise ValueError(f'{path}: row {line} needs a record URL or title')
    return rows


def apply_collaboration_review(path, papers, rows):
    """Append new candidates, then exclude only papers marked Y in the TSV."""
    decisions = {}

    def remember(keys, omit):
        for key in keys:
            if key in decisions and decisions[key] != omit:
                raise ValueError(f'{path}: conflicting omit decisions for {key}')
            decisions[key] = omit

    for row in rows:
        remember(review_row_keys(row), row['omit'].strip().upper())

    new_rows = []
    retained = []
    omitted = []
    for paper in sorted(papers, key=lambda p: p.date, reverse=True):
        matches = {decisions[key] for key in paper.ids if key in decisions}
        if len(matches) > 1:
            raise ValueError(f'{path}: conflicting omit decisions for '
                             f'{paper.title}')
        if matches:
            omit = matches.pop()
        else:
            collaborations = likely_full_collaborations(paper)
            if not collaborations:
                retained.append(paper)
                continue
            row = review_row(paper)
            new_rows.append(row)
            omit = 'Y'
        # Include every alias from the merged record for this run. Existing
        # rows are never rewritten, even when more metadata becomes available.
        remember(paper.ids, omit)
        (omitted if omit == 'Y' else retained).append(paper)

    if new_rows or not os.path.exists(path) or os.path.getsize(path) == 0:
        needs_header = not os.path.exists(path) or os.path.getsize(path) == 0
        needs_newline = False
        if not needs_header:
            with open(path, 'rb') as stream:
                stream.seek(-1, os.SEEK_END)
                needs_newline = stream.read(1) not in {b'\n', b'\r'}
        with open(path, 'a', newline='', encoding='utf-8') as stream:
            if needs_newline:
                stream.write('\n')
            writer = csv.DictWriter(stream, fieldnames=REVIEW_COLUMNS,
                                    delimiter='\t', lineterminator='\n')
            if needs_header:
                writer.writeheader()
            writer.writerows(new_rows)
    print(f'Collaboration review: {len(new_rows)} new entries in {path}; '
          f'{len(omitted)} papers omitted (Y)', file=sys.stderr)
    return retained


def print_authors(author,
                  years_back,
                  formatting,
                  orcid=None,
                  inspire_bai=None,
                  ads_token=None,
                  use_ads=True,
                  use_inspire=True,
                  check_affiliations=False,
                  show_papers=False,
                  show_skipped=False,
                  collaboration_review=None):
    """Print the coauthors of `author`, combining arXiv, ADS/SciX, and INSPIRE.

    ADS/SciX is queried if `use_ads` and both an ORCID and an ADS API token
    are given. INSPIRE is queried if `use_inspire` and an INSPIRE author ID is
    given or can be looked up from the ORCID.

    Affiliations come from the `affiliations` dict if present, otherwise from
    the coauthor's most recent ADS/SciX or INSPIRE record that has one.
    """
    current_year = dt.now().year
    min_year = current_year - years_back
    review_rows = (read_collaboration_review(collaboration_review)
                   if collaboration_review is not None else [])

    papers = fetch_arxiv(author)
    print(f'arXiv: {len(papers)} papers', file=sys.stderr)
    if use_ads and orcid and ads_token:
        ads_papers = fetch_ads(orcid, ads_token, min_year)
        print(f'ADS/SciX: {len(ads_papers)} records', file=sys.stderr)
        papers += ads_papers
    elif use_ads and orcid:
        print('Warning: Not querying ADS/SciX because no ADS API token was '
              'given (set ADS_TOKEN or pass --ads-token)', file=sys.stderr)
    if use_inspire and inspire_bai is None and orcid:
        inspire_bai = inspire_bai_from_orcid(orcid)
        if inspire_bai is None:
            print(f'Warning: No INSPIRE author found for ORCID {orcid}',
                  file=sys.stderr)
    if use_inspire and inspire_bai:
        inspire_papers = fetch_inspire(inspire_bai, min_year)
        print(f'INSPIRE ({inspire_bai}): {len(inspire_papers)} records',
              file=sys.stderr)
        papers += inspire_papers
    papers = merge_papers(papers)
    if collaboration_review is not None:
        # Use the same year window as the normal coauthor output. Out-of-window
        # papers must not add review rows or contribute any author information.
        papers = apply_collaboration_review(
            collaboration_review,
            [paper for paper in papers if paper.date[0] >= min_year],
            review_rows)

    # All keys under which the author themselves may appear
    self_keys = {name_key(author)} | {
        name_key(name)
        for name, remapped in remapped_names.items() if remapped == author
    }

    coauthors = {}
    missing_from_arxiv = []
    total_papers = len(papers)
    for i, paper in enumerate(
            sorted(papers, key=lambda p: p.date, reverse=True)):
        title = paper.title
        year_updated = paper.date[0]

        if year_updated + years_back < current_year:
            if show_skipped:
                print(f'{i + 1}/{total_papers}: {year_updated} '
                      f'{title}--Skipping ', file=sys.stderr)
            continue

        if show_papers:
            print(f'{i + 1}/{total_papers}: {year_updated} {title} '
                  f'[{",".join(sorted(paper.sources))}]', file=sys.stderr)
        if 'arxiv' not in paper.sources:
            missing_from_arxiv.append(paper)

        # Count each coauthor at most once per paper, even if the paper was
        # found in several sources.
        authors_by_key = {}
        for paper_author in paper.authors:
            # Remap names to the same spelling
            name = remapped_names.get(paper_author.name, paper_author.name)
            if not name.strip() or is_collaboration(name):
                continue
            key = name_key(name)
            if key in self_keys:
                continue
            authors_by_key.setdefault(key, []).append((name, paper_author))

        for key, paper_authors in authors_by_key.items():
            coauthor = coauthors.setdefault(key, {
                'count': 0,
                'date': (0, 0, 0),
                'link': None,
                'names': set(),
                'affiliation': None,
            })
            coauthor['count'] += 1
            coauthor['names'] |= {name for name, _ in paper_authors}
            if paper.date > coauthor['date']:
                coauthor['date'] = paper.date
                coauthor['link'] = paper.link
            # Use the affiliation from the most recent paper that has one,
            # preferring ones matched to an institution database, and ADS
            # over INSPIRE.
            for _, paper_author in paper_authors:
                if not paper_author.affiliations:
                    continue
                candidate = {
                    'rank': (paper.date, paper_author.curated,
                             paper_author.source == 'ads'),
                    'name': ' & '.join(paper_author.affiliations),
                    'curated': paper_author.curated,
                    'source': paper_author.source,
                    'link': paper.link,
                }
                if (coauthor['affiliation'] is None
                        or candidate['rank'] > coauthor['affiliation']['rank']):
                    coauthor['affiliation'] = candidate

    for coauthor in coauthors.values():
        # Prefer a spelling we have an affiliation for, otherwise the most
        # complete one (e.g. 'Lawrence E. Kidder' over 'L. Kidder').
        coauthor['name'] = max(coauthor['names'],
                               key=lambda n: (n in affiliations, len(n), n))

    if missing_from_arxiv:
        print(f'\n{len(missing_from_arxiv)} records found only in ADS/SciX '
              'or INSPIRE (check these are yours and not duplicates):',
              file=sys.stderr)
        for paper in missing_from_arxiv:
            print(f'  {paper.date[0]}-{paper.date[1]:02} '
                  f'[{",".join(sorted(paper.sources))}'
                  f'{": " + paper.doctype if paper.doctype else ""}] '
                  f'{paper.title}\n    {paper.link}', file=sys.stderr)

    # Different keys that may be the same person, e.g. 'Nils Fischer' and
    # 'Nils L. Vu' would not be caught, but 'J. Smith' and 'J. A. Smith' are.
    by_initial_and_last = {}
    for key, coauthor in coauthors.items():
        split_key = key.split()
        by_initial_and_last.setdefault((split_key[0][0], split_key[-1]),
                                       []).append(coauthor['name'])
    possible_duplicates = [
        names for names in by_initial_and_last.values() if len(names) > 1
    ]
    if possible_duplicates:
        print('\nPossible duplicate coauthors (add to remapped_names if they '
              'are the same person):', file=sys.stderr)
        for names in possible_duplicates:
            print('  ' + ' | '.join(sorted(names)), file=sys.stderr)

    def describe(affiliation):
        year, month, _ = affiliation['rank'][0]
        how = ('' if affiliation['curated'] else
               ', guessed from raw affiliation string')
        return (f'[{affiliation["source"]} {year}-{month:02}{how}] '
                f'{affiliation["link"]}')

    from_papers = [
        c for c in coauthors.values()
        if c['name'] not in affiliations and c['affiliation']
    ]
    if from_papers:
        print('\nAffiliations taken from papers (add to `affiliations` to '
              'override):', file=sys.stderr)
        for coauthor in sorted(from_papers, key=lambda c: c['name']):
            print(f'  {coauthor["name"]}: {coauthor["affiliation"]["name"]}\n'
                  f'    {describe(coauthor["affiliation"])}', file=sys.stderr)

    if check_affiliations:
        print('\nAffiliations in `affiliations` vs. most recent paper:',
              file=sys.stderr)
        for coauthor in sorted(coauthors.values(), key=lambda c: c['name']):
            if (coauthor['name'] in affiliations
                    and coauthor['affiliation'] is not None):
                print(f'  {coauthor["name"]}:\n'
                      f'    dict:  {affiliations[coauthor["name"]]}\n'
                      f'    paper: {coauthor["affiliation"]["name"]} '
                      f'{describe(coauthor["affiliation"])}', file=sys.stderr)
    print(file=sys.stderr)

    def sort_key(key):
        return ascii_fold(coauthors[key]['name'].split()[-1]).lower()

    if formatting == Format['NsfAccess']:
        print("Name | Number of Papers | Last Paper")
        for key in sorted(coauthors, key=sort_key):
            coauthor = coauthors[key]
            name = get_initials(coauthor['name'])
            print(f'{name.replace(". ", ".~"):30} '
                  f'{coauthor["date"][0]} {coauthor["count"]:4} '
                  f'{coauthor["date"][1]}')
    elif formatting == Format['NsfProposal']:
        print("Name")
        for key in sorted(coauthors, key=sort_key):
            coauthor = coauthors[key]
            year, month, day = coauthor['date']
            to_print = str(
                f'{get_last_name_first(coauthor["name"])}').strip()
            if coauthor['name'] in affiliations:
                to_print += f'\t{affiliations[coauthor["name"]]}'
            elif coauthor['affiliation'] is not None:
                to_print += f'\t{coauthor["affiliation"]["name"]}'
            else:
                print(f"Could find an affiliation for {coauthor['name']}", file=sys.stderr)
            to_print += f'\t\t{month}/{day}/{year}'
            print(to_print)


if __name__ == '__main__':
    import argparse as ap
    parser = ap.ArgumentParser(
        prog='arxiv-collaborators',
        description='Pull list of arxiv collaborators based on your arxiv name.'
    )
    parser.add_argument('--arxiv-name',
                        help='Your arxiv name, e.g. Deppe_Nils',
                        required=True)
    parser.add_argument(
        '--years',
        help='Number of years back to use for getting collabotars',
        type=int,
        required=True)
    parser.add_argument('--formatting',
                        help='The format to output the authors in.',
                        choices=['NsfAccess', 'NsfProposal'],
                        required=True)
    parser.add_argument(
        '--orcid',
        help='Your ORCID, e.g. 0000-0003-4557-4115. If given, ADS/SciX and '
        'INSPIRE are also queried to catch papers missing from arXiv.')
    parser.add_argument(
        '--inspire-bai',
        help='Your INSPIRE author ID, e.g. Nils.Deppe.1. Looked up from the '
        'ORCID if not given.')
    parser.add_argument(
        '--ads-token',
        default=os.environ.get('ADS_TOKEN'),
        help='ADS/SciX API token. Defaults to the ADS_TOKEN environment '
        'variable.')
    parser.add_argument(
        '--ads',
        action=ap.BooleanOptionalAction,
        help='Query ADS/SciX. By default it is queried if --orcid and an ADS '
        'token are given. Passing --ads makes it an error if they are missing.')
    parser.add_argument(
        '--inspire',
        action=ap.BooleanOptionalAction,
        help='Query INSPIRE-HEP. By default it is queried if --orcid or '
        '--inspire-bai is given. Passing --inspire makes it an error if both '
        'are missing.')
    parser.add_argument(
        '--check-affiliations',
        action='store_true',
        help='Compare the `affiliations` dict to the affiliations on each '
        "coauthor's most recent paper (printed to stderr).")
    parser.add_argument('--show-papers',
                        action='store_true',
                        help='Print the papers used (to stderr).')
    parser.add_argument(
        '--collaboration-review',
        metavar='FILE.tsv',
        help='Append likely full LSC, LISA, or ET papers to a review TSV with '
        'omit=Y, preserving existing rows and Y/N edits. Only papers marked '
        'Y in this file are excluded from the coauthor output. Large author '
        'lists alone (e.g. Cosmic Explorer) are not flagged.')
    args = parser.parse_args()
    if args.ads and not (args.orcid and args.ads_token):
        parser.error('--ads requires --orcid and an ADS API token (set '
                     'ADS_TOKEN or pass --ads-token)')
    if args.inspire and not (args.orcid or args.inspire_bai):
        parser.error('--inspire requires --orcid or --inspire-bai')
    formatting = Format[args.formatting]
    print_authors(args.arxiv_name,
                  args.years,
                  formatting,
                  orcid=args.orcid,
                  inspire_bai=args.inspire_bai,
                  ads_token=args.ads_token,
                  use_ads=args.ads is not False,
                  use_inspire=args.inspire is not False,
                  check_affiliations=args.check_affiliations,
                  show_papers=args.show_papers,
                  collaboration_review=args.collaboration_review)
