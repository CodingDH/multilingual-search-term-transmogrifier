"""Curated overrides used by the language-metadata pipeline."""

_SIL_NAME_OVERRIDES = {
    'kro':      'Kru languages',
    'tokipona': 'Toki Pona',
}

MANUAL_LANG_TO_SET5 = {
    # Indo-European > Germanic
    'af': 'gem', 'afr': 'gem', 'da': 'gem', 'dan': 'gem',
    'de': 'gem', 'deu': 'gem', 'en': 'gem', 'eng': 'gem',
    'fy': 'gem', 'fry': 'gem', 'is': 'gem', 'isl': 'gem',
    'lb': 'gem', 'ltz': 'gem', 'nl': 'gem', 'nld': 'gem',
    'no': 'gem', 'nor': 'gem', 'nb': 'gem', 'nob': 'gem',
    'nn': 'gem', 'nno': 'gem', 'sv': 'gem', 'swe': 'gem',
    'yi': 'gem', 'yid': 'gem',
    # Wikimedia Germanic (non-ISO 639-1)
    'als': 'gem', 'ang': 'gem', 'bar': 'gem', 'got': 'gem',
    'ksh': 'gem', 'nds': 'gem', 'nds-nl': 'gem', 'pdc': 'gem',
    'sco': 'gem', 'vls': 'gem',
    # Indo-European > Romance
    'ca': 'roa', 'cat': 'roa', 'es': 'roa', 'spa': 'roa',
    'fr': 'roa', 'fra': 'roa', 'gl': 'roa', 'glg': 'roa',
    'it': 'roa', 'ita': 'roa', 'la': 'roa', 'lat': 'roa',
    'oc': 'roa', 'oci': 'roa', 'pt': 'roa', 'por': 'roa',
    'ro': 'roa', 'ron': 'roa',
    # Wikimedia Romance
    'an': 'roa', 'co': 'roa', 'ext': 'roa', 'frp': 'roa',
    'fur': 'roa', 'ht': 'roa', 'lad': 'roa', 'lij': 'roa',
    'lmo': 'roa', 'mwl': 'roa', 'nap': 'roa', 'nrm': 'roa',
    'pms': 'roa', 'roa-rup': 'roa', 'sc': 'roa', 'scn': 'roa',
    'vec': 'roa', 'wa': 'roa',
    # Indo-European > Slavic
    'be': 'sla', 'bel': 'sla', 'bg': 'sla', 'bul': 'sla',
    'bs': 'sla', 'bos': 'sla', 'cs': 'sla', 'ces': 'sla',
    'hr': 'sla', 'hrv': 'sla', 'mk': 'sla', 'mkd': 'sla',
    'pl': 'sla', 'pol': 'sla', 'ru': 'sla', 'rus': 'sla',
    'sk': 'sla', 'slk': 'sla', 'sl': 'sla', 'slv': 'sla',
    'sr': 'sla', 'srp': 'sla', 'uk': 'sla', 'ukr': 'sla',
    # Wikimedia Slavic
    'be-x-old': 'sla', 'crn': 'sla', 'csb': 'sla', 'cu': 'sla',
    'dsb': 'sla', 'sh': 'sla',
    # Indo-European > Baltic
    'lt': 'bat', 'lit': 'bat', 'lv': 'bat', 'lav': 'bat',
    'bat-smg': 'bat',
    # Indo-European > Celtic
    'br': 'cel', 'bre': 'cel', 'cy': 'cel', 'cym': 'cel',
    'ga': 'cel', 'gle': 'cel', 'gd': 'cel', 'gla': 'cel',
    'gv': 'cel', 'glv': 'cel', 'kw': 'cel', 'cor': 'cel',
    # Indo-European > Indic
    'as': 'inc', 'asm': 'inc', 'bn': 'inc', 'ben': 'inc',
    'gu': 'inc', 'guj': 'inc', 'hi': 'inc', 'hin': 'inc',
    'mr': 'inc', 'mar': 'inc', 'ne': 'inc', 'nep': 'inc',
    'pa': 'inc', 'pan': 'inc', 'si': 'inc', 'sin': 'inc',
    'ur': 'inc', 'urd': 'inc',
    # Wikimedia Indic
    'awa': 'inc', 'bho': 'inc', 'bpy': 'inc',
    # brx (Bodo) and dz (Dzongkha) are Tibeto-Burman, not Indo-Aryan — see sit block below
    'gbm': 'inc',
    # Indo-European > Iranian
    'fa': 'ira', 'fas': 'ira', 'ku': 'ira', 'kur': 'ira',
    'ps': 'ira', 'pus': 'ira', 'tg': 'ira', 'tgk': 'ira',
    'os': 'ira', 'oss': 'ira',
    # Wikimedia Iranian
    'ckb': 'ira', 'diq': 'ira', 'glk': 'ira',
    'khw': 'ira', 'mzn': 'ira', 'pnb': 'ira',
    # Indo-European > Greek
    'el': 'grk', 'ell': 'grk',
    # Indo-European > Armenian
    'hy': 'hyx', 'hye': 'hyx',
    # Indo-European > Albanian
    'sq': 'sqj', 'sqi': 'sqj',
    # Afro-Asiatic > Semitic
    'ar': 'sem', 'ara': 'sem', 'he': 'sem', 'heb': 'sem',
    'am': 'sem', 'amh': 'sem', 'mt': 'sem', 'mlt': 'sem',
    'ti': 'sem', 'tir': 'sem',
    'arc': 'sem', 'arz': 'sem',
    # Afro-Asiatic > Cushitic
    'so': 'cus', 'som': 'cus', 'om': 'cus', 'orm': 'cus',
    # Afro-Asiatic > Chadic
    'ha': 'cdc', 'hau': 'cdc',
    # Afro-Asiatic > Berber
    'kab': 'ber',
    # Sino-Tibetan
    'zh': 'sit', 'zho': 'sit', 'bo': 'sit', 'bod': 'sit',
    'my': 'sit', 'mya': 'sit',
    # Wikimedia Sino-Tibetan
    'brx': 'sit', 'dz': 'sit',  # Bodo and Dzongkha are Tibeto-Burman (moved from inc above)
    'cdo': 'sit', 'gan': 'sit', 'hak': 'sit', 'man': 'sit',
    'mrh': 'sit', 'wuu': 'sit', 'yue': 'sit',
    'zh-classical': 'sit', 'zh-min-nan': 'sit',
    'zh-tw': 'sit', 'zh-yue': 'sit',
    # Turkic
    'az': 'trk', 'aze': 'trk', 'ba': 'trk', 'bak': 'trk',
    'kk': 'trk', 'kaz': 'trk', 'ky': 'trk', 'kir': 'trk',
    'tk': 'trk', 'tuk': 'trk', 'tr': 'trk', 'tur': 'trk',
    'tt': 'trk', 'tat': 'trk', 'ug': 'trk', 'uig': 'trk',
    'uz': 'trk', 'uzb': 'trk',
    # Wikimedia Turkic
    'cv': 'trk', 'uz_AF': 'trk',
    # Mongolic (xal = Kalmyk is Mongolian, not Turkic — moved to xgn block below)
    # Wikimedia Mongolic
    # Uralic > Finno-Ugrian
    'et': 'fiu', 'est': 'fiu', 'fi': 'fiu', 'fin': 'fiu',
    'hu': 'fiu', 'hun': 'fiu',
    # Uralic > Sami
    'se': 'smi', 'sme': 'smi',
    # Wikimedia Uralic
    'fiu-vro': 'fiu', 'kv': 'fiu', 'udm': 'fiu',
    # Dravidian
    'kn': 'dra', 'kan': 'dra', 'ml': 'dra', 'mal': 'dra',
    'ta': 'dra', 'tam': 'dra', 'te': 'dra', 'tel': 'dra',
    # Niger-Kordofanian > Bantu
    'sw': 'bnt', 'swa': 'bnt', 'zu': 'bnt', 'zul': 'bnt',
    'xh': 'bnt', 'xho': 'bnt', 'rw': 'bnt', 'kin': 'bnt',
    'ny': 'bnt', 'nya': 'bnt', 'sn': 'bnt', 'sna': 'bnt',
    'st': 'bnt', 'sot': 'bnt', 'tn': 'bnt', 'tsn': 'bnt',
    'ln': 'bnt', 'lin': 'bnt', 'lg': 'bnt', 'lug': 'bnt',
    'kg': 'bnt', 'kon': 'bnt', 'rn': 'bnt', 'run': 'bnt',
    'ss': 'bnt', 'ssw': 'bnt', 'ts': 'bnt', 've': 'bnt',
    'nso': 'bnt', 'tum': 'bnt',
    # Niger-Kordofanian > broader Niger-Congo
    'yo': 'nic', 'yor': 'nic', 'ig': 'nic', 'ibo': 'nic',
    'ak': 'nic', 'aka': 'nic', 'ff': 'nic', 'ful': 'nic',
    'ee': 'nic', 'ewe': 'nic', 'tw': 'nic', 'bm': 'nic',
    # Nilo-Saharan
    'kr': 'ssa', 'kau': 'ssa', 'sg': 'ssa', 'sag': 'ssa',
    # Austronesian
    'id': 'map', 'ind': 'map', 'ms': 'map', 'msa': 'map',
    'mg': 'map', 'mlg': 'map', 'mi': 'map', 'mri': 'map',
    'tl': 'map', 'tgl': 'map', 'fj': 'map', 'fij': 'map',
    'sm': 'map', 'smo': 'map', 'to': 'map', 'ton': 'map',
    'bi': 'map', 'bis': 'map', 'ch': 'map', 'cha': 'map',
    'mh': 'map', 'mah': 'map', 'na': 'map', 'nau': 'map',
    # Wikimedia Austronesian
    'bcl': 'map', 'bug': 'map', 'ceb': 'map', 'gil': 'map',
    'haw': 'map', 'ilo': 'map', 'jv': 'map', 'map-bms': 'map',
    'min': 'map', 'pag': 'map', 'pam': 'map', 'su': 'map',
    'tet': 'map', 'ty': 'map', 'war': 'map',
    # Japonic
    'ja': 'jpx', 'jpn': 'jpx',
    # Tai-Kadai
    'th': 'tai', 'tha': 'tai', 'lo': 'tai', 'lao': 'tai',
    # Austro-Asiatic
    'km': 'mkh', 'khm': 'mkh', 'vi': 'mkh', 'vie': 'mkh',
    # Mongolic
    'mn': 'xgn', 'mon': 'xgn', 'bxr': 'xgn', 'xal': 'xgn',
    # Eskimo-Aleut
    'iu': 'esx', 'iku': 'esx',
    # Indigenous Americas
    'ay': 'sai', 'qu': 'sai', 'gn': 'sai',
    'cr': 'nai', 'ik': 'nai', 'kl': 'nai',
    'nv': 'nai', 'oj': 'nai',
    # Wikimedia Indigenous Americas
    'cho': 'nai', 'chr': 'nai', 'chy': 'nai',
    'mus': 'nai', 'nah': 'nai',
    # Constructed / Artificial
    'eo': 'art', 'epo': 'art', 'ia': 'art', 'ina': 'art',
    'io': 'art', 'ido': 'art', 'vo': 'art', 'vol': 'art',
    'jbo': 'art', 'ie': 'art',
    'tlh': 'art', 'tokipona': 'art',
    # Caucasian
    'ka': 'ccs', 'kat': 'ccs',        # Georgian > South Caucasian
    'ab': 'ccn', 'abk': 'ccn',        # Abkhaz > North Caucasian
    'av': 'ccn', 'ava': 'ccn',        # Avaric
    'ce': 'ccn', 'che': 'ccn',        # Chechen
    'inh': 'ccn', 'lzz': 'ccn',       # Wikimedia Caucasian
    'xmf': 'ccs',                      # Megrelian > South Caucasian
    # Basque — has its own ISO 639-5 code (euq) as a family of one
    'eu': 'euq', 'eus': 'euq',
    # Korean — language isolate (no genetic relatives)
    'ko': 'isolate', 'kor': 'isolate',
    # Creole / Mixed
    'pap': 'crp', 'pih': 'crp', 'tpi': 'crp',
    # Sign languages
    'sgn': 'sgn',
    # CLDR-only codes not covered by ISO 639-1/2/Wikimedia lookups above
    # Semitic (Afro-Asiatic)
    'apd': 'sem',   # Sudanese Spoken Arabic
    'mey': 'sem',   # Hassaniyya (Saharan Arabic variety)
    # Berber (Afro-Asiatic)
    'grr': 'ber',   # Taznatit (Algerian Berber)
    'mzb': 'ber',   # Tumzabt (Mzab Berber, Algeria)
    # Niger-Kordofanian
    'bjt': 'nic',   # Balanta-Ganja (Atlantic-Congo, Senegal/Guinea-Bissau)
    'bsc': 'nic',   # Bassari (Atlantic-Congo, Senegal/Guinea-Bissau)
    'bsq': 'nic',   # Basa (Cameroon, Niger-Congo)
    'knf': 'nic',   # Mankanya (Atlantic-Congo, Guinea-Bissau)
    'mfv': 'nic',   # Mandjak (Atlantic-Congo, Guinea-Bissau)
    'snf': 'nic',   # Noon (Senegambian, Senegal)
    'tnr': 'bnt',   # Ménik/Tonga (Bantu, Zambia)
    # Indo-European — Romance
    'lld': 'roa',   # Ladin (Romance, spoken in South Tyrol)
    # Indo-European — Germanic
    'mhn': 'gem',   # Mòcheno (Germanic, spoken in Trentino)
    # Indo-European — Indic
    'knn': 'inc',   # Konkani (Indo-Aryan, India)
    # Indo-European — Greek
    'ecy': 'grk',   # Cypriot Greek (extinct variety)
    'gmy': 'grk',   # Mycenaean Greek (ancient)
    # Central American Indian
    'ccr': 'cai',   # Cacaopera (Misumalpan, El Salvador)
    'len': 'cai',   # Lenca (Honduras/El Salvador; sometimes treated as isolate)
    # Uto-Aztecan (North American)
    'ppl': 'azc',   # Pipil / Nawat (Uto-Aztecan, El Salvador)
    # Hmong-Mien
    'mww': 'hmx',   # Hmong Daw / White Hmong
    # Sino-Tibetan
    'nan': 'zhx',   # Min Nan Chinese / Taiwanese
    'stu': 'tbq',   # Samtao (Tibeto-Burman, Myanmar)
    'suz': 'tbq',   # Sunwar (Tibeto-Burman, Nepal)
    # CLDR v45 supplement — dropped from CLDR 48.2 for administrative reasons only
    'ase': 'sgn',   # American Sign Language
    'cwd': 'nai',   # Woods Cree
    'dzg': 'ssa',   # Dazaga (Nilo-Saharan)
    'gom': 'inc',   # Goan Konkani (Indo-Aryan)
    'hax': 'isolate',  # Southern Haida (language isolate)
    'hdn': 'isolate',  # Northern Haida (language isolate)
    'ike': 'esx',   # Eastern Canadian Inuktitut
    'kbl': 'ssa',   # Kanembu (Nilo-Saharan)
    'lou': 'crp',   # Louisiana Creole
    'lsm': 'bnt',   # Saamia (Bantu, Uganda)
    'mde': 'ssa',   # Maba (Nilo-Saharan)
    'mye': 'bnt',   # Myene (Bantu, Gabon)
    'ojb': 'nai',   # Northwestern Ojibwa
    'ojc': 'nai',   # Central Ojibwa
    'ojg': 'nai',   # Eastern Ojibwa
    'sba': 'ssa',   # Ngambay (Nilo-Saharan)
    'shu': 'sem',   # Chadian Arabic (Semitic, Arabic script)
    'slh': 'nai',   # Southern Lushootseed
    'str': 'nai',   # Straits Salish
    'tce': 'nai',   # Southern Tutchone
    'tgx': 'nai',   # Tagish
    'tht': 'nai',   # Tahltan
    'ttm': 'nai',   # Northern Tutchone
}

CLDR_V45_SUPPLEMENT = [
    # (code,  English name,                   directionality, modern, is_official)
    ('ase', 'American Sign Language',           'ltr', True, True),
    ('cwd', 'Woods Cree',                       'ltr', True, True),
    ('dzg', 'Dazaga',                           'ltr', True, True),
    ('gom', 'Goan Konkani',                     'ltr', True, False),
    ('hax', 'Southern Haida',                   'ltr', True, True),
    ('hdn', 'Northern Haida',                   'ltr', True, True),
    ('ike', 'Eastern Canadian Inuktitut',       'ltr', True, True),
    ('kbl', 'Kanembu',                          'ltr', True, True),
    ('lou', 'Louisiana Creole',                 'ltr', True, True),
    ('lsm', 'Saamia',                           'ltr', True, True),
    ('mde', 'Maba',                             'ltr', True, True),
    ('mye', 'Myene',                            'ltr', True, True),
    ('ojb', 'Northwestern Ojibwa',              'ltr', True, True),
    ('ojc', 'Central Ojibwa',                   'ltr', True, True),
    ('ojg', 'Eastern Ojibwa',                   'ltr', True, True),
    ('sba', 'Ngambay',                          'ltr', True, True),
    ('shu', 'Chadian Arabic',                   'rtl', True, True),
    ('slh', 'Southern Lushootseed',             'ltr', True, True),
    ('str', 'Straits Salish',                   'ltr', True, True),
    ('tce', 'Southern Tutchone',                'ltr', True, True),
    ('tgx', 'Tagish',                           'ltr', True, True),
    ('tht', 'Tahltan',                          'ltr', True, True),
    ('ttm', 'Northern Tutchone',                'ltr', True, True),
]
