"""
Real Karnataka ground-truth reference data used to seed the synthetic FIR dataset.

Everything here is *real* (districts, approximate geo-centroids, IPC/other acts &
sections, crime-head taxonomy, lookups) so the generated data looks and behaves like
genuine Karnataka State Police records. Only the individual FIR *records* are synthetic.

Sources of truth: Karnataka revenue districts (31), NCRB crime-head taxonomy,
Indian Penal Code / special-act sections commonly seen in FIRs.
"""

# ---------------------------------------------------------------------------
# GEOGRAPHY
# ---------------------------------------------------------------------------

STATE = {"StateID": 29, "StateName": "Karnataka", "NationalityID": 1, "Active": 1}

# 31 Karnataka districts with approximate centroid lat/long and a relative
# "crime propensity" weight (urban districts generate more FIRs). The (lat, lng)
# span is used to scatter incidents realistically inside the district.
# weight is roughly proportional to population / urbanisation.
DISTRICTS = [
    # DistrictID, Name, lat, lng, span(deg), weight
    (4001, "Bengaluru City",        12.9716, 77.5946, 0.18, 30.0),
    (4002, "Bengaluru Rural",       13.2846, 77.5960, 0.30, 4.0),
    (4003, "Ramanagara",            12.7217, 77.2807, 0.25, 3.0),
    (4004, "Kolar",                 13.1367, 78.1292, 0.28, 4.0),
    (4005, "Chikkaballapura",       13.4355, 77.7315, 0.28, 3.0),
    (4006, "Tumakuru",              13.3379, 77.1173, 0.35, 6.0),
    (4007, "Mysuru",                12.2958, 76.6394, 0.30, 9.0),
    (4008, "Mandya",                12.5223, 76.8954, 0.28, 5.0),
    (4009, "Hassan",                13.0072, 76.0962, 0.30, 5.0),
    (4010, "Chamarajanagar",        11.9261, 76.9438, 0.30, 2.5),
    (4011, "Kodagu",                12.3375, 75.8069, 0.28, 2.0),
    (4012, "Dakshina Kannada",      12.9141, 74.8560, 0.28, 7.0),
    (4013, "Udupi",                 13.3409, 74.7421, 0.25, 4.0),
    (4014, "Chikkamagaluru",        13.3161, 75.7720, 0.32, 3.0),
    (4015, "Shivamogga",            13.9299, 75.5681, 0.32, 6.0),
    (4016, "Davanagere",            14.4644, 75.9218, 0.28, 5.5),
    (4017, "Chitradurga",           14.2251, 76.3980, 0.32, 4.0),
    (4018, "Ballari",               15.1394, 76.9214, 0.30, 6.0),
    (4019, "Vijayanagara",          15.3350, 76.4600, 0.28, 3.0),
    (4020, "Koppal",                15.3547, 76.1550, 0.30, 3.0),
    (4021, "Raichur",               16.2076, 77.3463, 0.32, 4.5),
    (4022, "Kalaburagi",            17.3297, 76.8343, 0.35, 7.0),
    (4023, "Yadgir",                16.7700, 77.1376, 0.28, 2.5),
    (4024, "Bidar",                 17.9106, 77.5199, 0.30, 4.0),
    (4025, "Vijayapura",            16.8302, 75.7100, 0.35, 5.0),
    (4026, "Bagalkote",             16.1691, 75.6615, 0.30, 4.0),
    (4027, "Belagavi",              15.8497, 74.4977, 0.38, 9.0),
    (4028, "Dharwad",               15.4589, 75.0078, 0.28, 6.0),
    (4029, "Gadag",                 15.4292, 75.6290, 0.25, 3.0),
    (4030, "Haveri",                14.7935, 75.4045, 0.28, 3.5),
    (4031, "Uttara Kannada",        14.7935, 74.6869, 0.40, 3.5),
]

# Representative police-station name stems per district (each district gets several
# numbered/named stations built from these). Bengaluru City gets real-ish names.
BENGALURU_STATIONS = [
    "Cubbon Park", "Halasuru Gate", "Vidhana Soudha", "Commercial Street", "Shivajinagar",
    "Chamarajpet", "Jayanagar", "Banashankari", "Basavanagudi", "J P Nagar",
    "Koramangala", "Madiwala", "HSR Layout", "Marathahalli", "Whitefield",
    "K R Puram", "Ramamurthy Nagar", "Indiranagar", "Ashok Nagar", "Wilson Garden",
    "Electronic City", "Hebbal", "Yelahanka", "Peenya", "Rajajinagar",
    "Vijayanagar", "Kengeri", "Yeshwanthpur", "Sampigehalli", "Bagalur",
]
GENERIC_STATION_SUFFIXES = ["Town", "Rural", "Market", "Extension", "East", "West", "North", "South", "Circle"]

# ---------------------------------------------------------------------------
# UNIT / ORG STRUCTURE
# ---------------------------------------------------------------------------

UNIT_TYPES = [
    # UnitTypeID, Name, CityDistState, Hierarchy
    (1, "State Headquarters", "State", 1),
    (2, "Range Office", "State", 2),
    (3, "Commissionerate", "City", 2),
    (4, "District Office", "District", 3),
    (5, "Sub-Division", "District", 4),
    (6, "Circle Office", "District", 5),
    (7, "Police Station", "District", 6),
]

RANKS = [
    # RankID, RankName, Hierarchy(lower=higher)
    (1, "Director General of Police", 1),
    (2, "Additional Director General of Police", 2),
    (3, "Inspector General of Police", 3),
    (4, "Deputy Inspector General of Police", 4),
    (5, "Superintendent of Police", 5),
    (6, "Additional Superintendent of Police", 6),
    (7, "Deputy Superintendent of Police", 7),
    (8, "Police Inspector", 8),
    (9, "Police Sub-Inspector", 9),
    (10, "Assistant Sub-Inspector", 10),
    (11, "Head Constable", 11),
    (12, "Police Constable", 12),
]

DESIGNATIONS = [
    (1, "Station House Officer", 1),
    (2, "Investigating Officer", 2),
    (3, "Circle Inspector", 3),
    (4, "Additional SHO", 4),
    (5, "Duty Officer", 5),
]

# ---------------------------------------------------------------------------
# CASE-LEVEL LOOKUPS
# ---------------------------------------------------------------------------

# CaseCategory: the leading digit of CrimeNo encodes this.
CASE_CATEGORIES = [
    (1, "FIR"),        # First Information Report
    (3, "UDR"),        # Unnatural Death Report
    (4, "PAR"),        # Preliminary Assessment Report
    (8, "Zero FIR"),   # Zero FIR (jurisdiction-agnostic)
]

GRAVITY_OFFENCES = [
    (1, "Heinous"),
    (2, "Non-Heinous"),
    (3, "Serious"),
    (4, "Minor"),
]

CASE_STATUSES = [
    (1, "Under Investigation"),
    (2, "Charge Sheeted"),
    (3, "Closed - Undetected"),
    (4, "Closed - False"),
    (5, "Convicted"),
    (6, "Acquitted"),
    (7, "Pending Trial"),
]

RELIGIONS = [
    (1, "Hindu"), (2, "Muslim"), (3, "Christian"), (4, "Jain"),
    (5, "Sikh"), (6, "Buddhist"), (7, "Other"),
]

CASTES = [
    (1, "General"), (2, "OBC"), (3, "SC"), (4, "ST"),
    (5, "Category-I"), (6, "Category-IIA"), (7, "Category-IIIB"), (8, "Unknown"),
]

OCCUPATIONS = [
    (1, "Farmer"), (2, "Agricultural Labourer"), (3, "Daily Wage Worker"),
    (4, "Government Employee"), (5, "Private Employee"), (6, "Business/Trader"),
    (7, "Student"), (8, "Homemaker"), (9, "Unemployed"), (10, "Driver"),
    (11, "IT Professional"), (12, "Auto/Cab Driver"), (13, "Skilled Worker"),
    (14, "Retired"), (15, "Self Employed"),
]

# GenderID convention used across the schema (m/f/t)
GENDERS = {1: "Male", 2: "Female", 3: "Transgender"}
BLOOD_GROUPS = {1: "O+", 2: "A+", 3: "B+", 4: "AB+", 5: "O-", 6: "A-", 7: "B-", 8: "AB-"}

# ---------------------------------------------------------------------------
# CRIME-HEAD TAXONOMY  (NCRB-style major head -> sub-head)
# ---------------------------------------------------------------------------

# CrimeHead: CrimeHeadID, CrimeGroupName
CRIME_HEADS = [
    (1, "Crimes Against Body"),
    (2, "Crimes Against Property"),
    (3, "Crimes Against Women"),
    (4, "Crimes Against Children"),
    (5, "Crimes Against Public Order & Safety"),
    (6, "Economic Offences"),
    (7, "Offences Against State / Special Laws"),
    (8, "Cyber Crimes"),
]

# CrimeSubHead: CrimeSubHeadID, CrimeHeadID, CrimeHeadName(sub-head name), SeqID
CRIME_SUBHEADS = [
    (101, 1, "Murder", 1),
    (102, 1, "Attempt to Murder", 2),
    (103, 1, "Culpable Homicide", 3),
    (104, 1, "Grievous Hurt", 4),
    (105, 1, "Assault / Hurt", 5),
    (106, 1, "Kidnapping & Abduction", 6),
    (201, 2, "Dacoity", 1),
    (202, 2, "Robbery", 2),
    (203, 2, "Burglary / House Breaking", 3),
    (204, 2, "Theft", 4),
    (205, 2, "Motor Vehicle Theft", 5),
    (206, 2, "Chain Snatching", 6),
    (207, 2, "Criminal Trespass", 7),
    (301, 3, "Rape", 1),
    (302, 3, "Dowry Death", 2),
    (303, 3, "Cruelty by Husband/Relatives", 3),
    (304, 3, "Assault on Woman (Outrage Modesty)", 4),
    (305, 3, "Sexual Harassment", 5),
    (401, 4, "Child Abuse (POCSO)", 1),
    (402, 4, "Child Kidnapping", 2),
    (403, 4, "Child Labour", 3),
    (501, 5, "Rioting", 1),
    (502, 5, "Unlawful Assembly", 2),
    (503, 5, "Public Nuisance", 3),
    (504, 5, "Rash & Negligent Act", 4),
    (601, 6, "Cheating", 1),
    (602, 6, "Criminal Breach of Trust", 2),
    (603, 6, "Forgery", 3),
    (604, 6, "Counterfeiting", 4),
    (701, 7, "NDPS (Narcotics)", 1),
    (702, 7, "Arms Act", 2),
    (703, 7, "Excise / Prohibition", 3),
    (704, 7, "Gambling", 4),
    (801, 8, "Online Financial Fraud", 1),
    (802, 8, "Cyber Stalking / Harassment", 2),
    (803, 8, "Identity Theft", 3),
    (804, 8, "Data / OTP Fraud", 4),
]

# ---------------------------------------------------------------------------
# ACTS & SECTIONS (real legal references)
# ---------------------------------------------------------------------------

ACTS = [
    # ActCode, ActDescription, ShortName
    ("IPC", "Indian Penal Code, 1860", "IPC"),
    ("CRPC", "Code of Criminal Procedure, 1973", "CrPC"),
    ("NDPS", "Narcotic Drugs and Psychotropic Substances Act, 1985", "NDPS"),
    ("ARMS", "Arms Act, 1959", "Arms Act"),
    ("POCSO", "Protection of Children from Sexual Offences Act, 2012", "POCSO"),
    ("IT", "Information Technology Act, 2000", "IT Act"),
    ("MVA", "Motor Vehicles Act, 1988", "MV Act"),
    ("EXCISE", "Karnataka Excise Act, 1965", "KE Act"),
    ("KPA", "Karnataka Police Act, 1963", "KP Act"),
    ("DP", "Dowry Prohibition Act, 1961", "DP Act"),
    ("SCST", "SC/ST (Prevention of Atrocities) Act, 1989", "SC/ST Act"),
    ("GAMB", "Karnataka Police Act (Gaming)", "Gaming"),
]

# Section: (ActCode, SectionCode, SectionDescription)
# Also mapped to the crime sub-head it typically represents (for coherent generation).
# tuple: ActCode, SectionCode, Description, subhead_id
SECTIONS = [
    ("IPC", "302", "Punishment for murder", 101),
    ("IPC", "307", "Attempt to murder", 102),
    ("IPC", "304", "Culpable homicide not amounting to murder", 103),
    ("IPC", "304A", "Causing death by negligence", 504),
    ("IPC", "326", "Voluntarily causing grievous hurt by dangerous weapons", 104),
    ("IPC", "324", "Voluntarily causing hurt by dangerous weapons", 105),
    ("IPC", "323", "Voluntarily causing hurt", 105),
    ("IPC", "363", "Punishment for kidnapping", 106),
    ("IPC", "366", "Kidnapping/abducting woman to compel marriage", 106),
    ("IPC", "395", "Punishment for dacoity", 201),
    ("IPC", "392", "Punishment for robbery", 202),
    ("IPC", "397", "Robbery/dacoity with attempt to cause death", 202),
    ("IPC", "457", "House-breaking by night", 203),
    ("IPC", "380", "Theft in dwelling house", 204),
    ("IPC", "379", "Punishment for theft", 204),
    ("IPC", "379A", "Snatching", 206),
    ("IPC", "447", "Punishment for criminal trespass", 207),
    ("IPC", "376", "Punishment for rape", 301),
    ("IPC", "304B", "Dowry death", 302),
    ("IPC", "498A", "Cruelty by husband or relatives", 303),
    ("IPC", "354", "Assault to outrage modesty of woman", 304),
    ("IPC", "354A", "Sexual harassment", 305),
    ("IPC", "509", "Word/gesture to insult modesty of woman", 305),
    ("IPC", "147", "Punishment for rioting", 501),
    ("IPC", "143", "Punishment for unlawful assembly", 502),
    ("IPC", "290", "Punishment for public nuisance", 503),
    ("IPC", "420", "Cheating and dishonestly inducing delivery of property", 601),
    ("IPC", "406", "Punishment for criminal breach of trust", 602),
    ("IPC", "468", "Forgery for purpose of cheating", 603),
    ("IPC", "489A", "Counterfeiting currency notes", 604),
    ("NDPS", "20", "Punishment for offences relating to cannabis", 701),
    ("NDPS", "22", "Punishment for offences relating to psychotropic substances", 701),
    ("ARMS", "25", "Punishment for possessing arms without licence", 702),
    ("EXCISE", "32", "Illegal possession/sale of liquor", 703),
    ("GAMB", "79", "Gaming in common gaming house", 704),
    ("POCSO", "8", "Punishment for sexual assault on child", 401),
    ("POCSO", "12", "Punishment for sexual harassment of child", 401),
    ("IT", "66C", "Identity theft", 803),
    ("IT", "66D", "Cheating by personation using computer", 801),
    ("IT", "67", "Publishing obscene material in electronic form", 802),
    ("MVA", "184", "Driving dangerously", 504),
    ("SCST", "3", "Punishments for offences of atrocities", 105),
]

# quick maps
SUBHEAD_TO_HEAD = {sh[0]: sh[1] for sh in CRIME_SUBHEADS}
SUBHEAD_NAME = {sh[0]: sh[2] for sh in CRIME_SUBHEADS}
# sections grouped by the subhead they represent
SECTIONS_BY_SUBHEAD = {}
for _act, _sec, _desc, _sh in SECTIONS:
    SECTIONS_BY_SUBHEAD.setdefault(_sh, []).append((_act, _sec, _desc))

# Relative frequency of each sub-head (drives realistic case-mix; theft/hurt common,
# murder rare). Keyed by CrimeSubHeadID.
SUBHEAD_WEIGHTS = {
    101: 1.0, 102: 1.5, 103: 0.8, 104: 4.0, 105: 12.0, 106: 2.0,
    201: 0.3, 202: 2.5, 203: 6.0, 204: 18.0, 205: 7.0, 206: 3.0, 207: 4.0,
    # women sub-head weights CALIBRATED to NCRB-2022 Karnataka composition
    # (modesty ~63%, cruelty ~28%, rape ~6%, dowry ~1.7%, insult ~0.8%)
    301: 1.2, 302: 0.35, 303: 5.5, 304: 12.0, 305: 0.16,
    401: 1.2, 402: 0.5, 403: 0.4,
    501: 2.0, 502: 1.5, 503: 3.0, 504: 6.0,
    601: 7.0, 602: 3.0, 603: 2.0, 604: 0.4,
    701: 3.0, 702: 1.0, 703: 3.5, 704: 2.0,
    801: 5.0, 802: 2.0, 803: 1.5, 804: 3.0,
}

# Sub-heads that are "against women" (complainant/victim skew female)
WOMEN_SUBHEADS = {301, 302, 303, 304, 305}
# Sub-heads more likely at night (drives spatiotemporal hotspot signal)
NIGHT_SUBHEADS = {101, 102, 201, 202, 203, 206, 301, 703, 704}
# Heinous sub-heads
HEINOUS_SUBHEADS = {101, 102, 201, 202, 301, 302, 401, 402}

# Karnataka first names for synthetic (non-identifying, common regional names)
FIRST_NAMES_M = ["Ravi", "Kiran", "Manjunath", "Suresh", "Prakash", "Ganesh", "Naveen",
                 "Santosh", "Basavaraj", "Mahesh", "Anand", "Vinod", "Shivakumar",
                 "Nagaraj", "Ramesh", "Dinesh", "Chetan", "Praveen", "Girish", "Umesh"]
FIRST_NAMES_F = ["Lakshmi", "Sushma", "Divya", "Anitha", "Kavya", "Priya", "Roopa",
                 "Shwetha", "Deepa", "Bhavya", "Sowmya", "Rekha", "Geetha", "Nandini",
                 "Pooja", "Vidya", "Ashwini", "Meena", "Rani", "Savitha"]
LAST_NAMES = ["Gowda", "Reddy", "Shetty", "Naik", "Rao", "Hegde", "Patil", "Kumar",
              "Murthy", "Prasad", "Bhat", "Achar", "Jain", "Kulkarni", "Desai",
              "Hiremath", "Angadi", "Malagi", "Poojary", "Kamath"]

# ---------------------------------------------------------------------------
# BriefFacts narrative generation (feeds the NLP pipeline).
#
# Templates DESCRIBE the incident realistically and NEVER name the crime head /
# sub-head (no label leakage) — so classifying the crime type from the narrative
# is a genuine NLP task. Entity slots ({item},{weapon},{vehicle},{value},{pretext},
# {contraband}) give the entity-extraction demo real targets.
# ---------------------------------------------------------------------------

NLP_ENTITIES = {
    "weapon": ["a knife", "a long machete", "an iron rod", "a wooden club", "a sickle",
               "a country-made pistol", "a broken bottle", "a chopper", "a bamboo stick"],
    "vehicle": ["a motorcycle", "a scooter", "a white car", "an autorickshaw",
                "a pickup van", "a black SUV", "a moped"],
    "item": ["gold ornaments", "a mobile phone", "cash", "a laptop", "silver articles",
             "a gold chain", "important documents", "a two-wheeler", "a gold mangalsutra",
             "electronic goods"],
    "contraband": ["ganja", "MDMA pills", "illicit arrack", "brown sugar",
                   "banned gutka", "ganja packets", "whitener bottles"],
    "pretext": ["a fake job offer abroad", "a lottery prize", "a quick loan approval",
                "a matrimonial alliance", "doubling of invested money",
                "a fake insurance maturity", "a work-from-home scheme", "a fake KYC update"],
}

# per-subhead templates (most distinctive crimes)
BRIEF_SUBHEAD_TEMPLATES = {
    101: ["Complainant found the deceased lying in a pool of blood with grievous injuries near {place}. The body was shifted for postmortem and investigation taken up.",
          "The victim was attacked by unidentified persons with {weapon} at {place} and succumbed on the spot.",
          "A quarrel over money escalated and the accused fatally assaulted the deceased with {weapon} at {place}."],
    102: ["The accused attacked the complainant with {weapon} intending to kill; the injured was rushed to hospital in critical condition from {place}.",
          "Assailants ambushed the complainant near {place} and stabbed repeatedly with {weapon} before fleeing."],
    105: ["Following a heated argument at {place}, the accused assaulted the complainant with {weapon}, causing bleeding injuries.",
          "The complainant was beaten up by a group over an old rivalry near {place} and sustained injuries."],
    106: ["The complainant's {relation} was forcibly taken away in {vehicle} by unknown persons from near {place}.",
          "Unidentified persons abducted the victim near {place} and a ransom demand was later received."],
    202: ["The accused waylaid the complainant at {place}, brandished {weapon}, and forcibly took away {item} and cash worth Rs {value}.",
          "Armed miscreants intercepted the complainant near {place}, threatened with {weapon} and decamped with {item}."],
    203: ["Miscreants broke open the door lock during the night and decamped with {item} and jewellery worth Rs {value} from the house at {place}.",
          "The complainant returned to find the house lock broken and {item} missing from the premises at {place}."],
    204: ["The complainant reported that {item} kept at {place} went missing; the lock was found tampered.",
          "Unknown persons decamped with {item} worth Rs {value} from {place} while the complainant was away."],
    205: ["The complainant parked {vehicle} at {place}; on return it was found missing and a theft is suspected.",
          "{vehicle} left near {place} was stolen by unidentified persons during the night."],
    206: ["Two-wheeler-borne miscreants snatched a gold chain from the complainant near {place} and sped away on {vehicle}.",
          "While the complainant was walking near {place}, the accused snatched {item} and escaped on {vehicle}."],
    201: ["An armed gang stormed the premises at {place}, threatened the inmates with {weapon} and looted {item} and cash of Rs {value}."],
    301: ["The complainant alleged that the accused, known to her, sexually assaulted her at {place} against her will.",
          "A woman lodged a complaint of sexual assault by the accused at {place}; medical examination was conducted."],
    303: ["A married woman alleged persistent harassment and cruelty by her husband and in-laws over dowry demands at {place}.",
          "The complainant stated she was subjected to mental and physical cruelty for additional dowry at her matrimonial home in {place}."],
    302: ["A young married woman died under suspicious circumstances at {place} within seven years of marriage amid dowry harassment allegations."],
    304: ["The accused outraged the modesty of the complainant by inappropriate touching at {place} and fled.",
          "The complainant reported that the accused misbehaved and molested her near {place}."],
    305: ["The complainant, a woman, reported repeated unwelcome advances and lewd remarks by the accused at {place}."],
    401: ["A minor was subjected to inappropriate acts by the accused at {place}; the child's guardian lodged the complaint.",
          "The guardian alleged that the accused sexually abused the minor child near {place}."],
    501: ["A group indulged in stone-pelting, damaged public property and disrupted peace at {place} following a dispute.",
          "Two groups clashed at {place}, pelted stones and torched vehicles amid communal tension."],
    504: ["A speeding {vehicle} driven rashly knocked down the complainant near {place}, causing injuries, and sped off."],
    601: ["The complainant was induced to part with Rs {value} on the false promise of {pretext}; the accused is now absconding.",
          "The accused cheated the complainant of Rs {value} by promising {pretext} and issued a bounced cheque."],
    602: ["Money and valuables entrusted to the accused for safekeeping were dishonestly misappropriated, cheating the complainant of Rs {value}."],
    603: ["The accused fabricated documents and forged signatures to fraudulently obtain Rs {value} from the complainant."],
    701: ["During patrolling near {place}, the accused was found in possession of {contraband} and the same was seized.",
          "Acting on a tip-off, the team intercepted the accused near {place} with {contraband} concealed in {vehicle}."],
    702: ["The accused was found in unauthorised possession of {weapon} without a valid licence near {place}."],
    703: ["The accused was caught transporting {contraband} without permit near {place}; stock was seized."],
    704: ["A group was found gambling and betting money at a common house near {place}; cash and cards were seized."],
    801: ["The complainant received a fraudulent call and link, shared an OTP, and lost Rs {value} from the bank account.",
          "On the pretext of {pretext}, the accused obtained online banking credentials and siphoned Rs {value} digitally."],
    802: ["The complainant reported receiving obscene and threatening messages online from the accused."],
    803: ["Unknown persons created a fake profile impersonating the complainant and misused personal details online."],
    804: ["The complainant shared card and OTP details on a fraudulent portal and Rs {value} was debited without consent."],
}

# per-head fallback templates (guarantee coverage for every sub-head)
BRIEF_HEAD_TEMPLATES = {
    1: ["The complainant sustained injuries in an assault by the accused with {weapon} at {place}."],
    2: ["The complainant reported loss of {item} worth Rs {value} at {place} by unknown persons."],
    3: ["A woman lodged a complaint of harassment and misbehaviour by the accused at {place}."],
    4: ["A complaint concerning the safety of a minor child at {place} was lodged by the guardian."],
    5: ["A disturbance to public peace and order was reported at {place}, requiring police intervention."],
    6: ["The complainant was defrauded of Rs {value} by the accused through deceitful means related to {pretext}."],
    7: ["The accused was found violating special-law provisions with {contraband} near {place}."],
    8: ["The complainant fell victim to an online fraud and lost Rs {value} through a deceptive digital scheme."],
}

RELATIONS = ["minor son", "daughter", "younger brother", "relative", "employee"]

# Low-signal / vague narratives — real FIR briefs are often uninformative. A share of
# cases use these regardless of crime type, so the classifier CAN'T be perfect (forces
# realistic ~85-92% accuracy instead of a suspicious 100%).
GENERIC_BRIEFS = [
    "The complainant submitted a written report regarding an incident that occurred at {place}. The matter is under investigation.",
    "Based on credible information received, a case was registered concerning an offence reported near {place}.",
    "The complainant approached the station alleging an offence by the accused at {place}; statements are being recorded.",
    "An incident arising out of a prior dispute between the parties was reported at {place}. Further enquiry is on.",
    "Police received a complaint about an untoward incident at {place}. Investigation has commenced.",
    "The complainant lodged a report against the accused over an incident at {place}. Action is being taken as per law.",
    "A complaint was received regarding an offence committed at {place}; the accused is yet to be identified.",
]

# Confusable templates shared across related heads (add realistic class-boundary
# ambiguity so different models genuinely differ on the leaderboard).
CONFUSABLE_BRIEFS = {
    # violence + taking property: robbery(2) vs assault(1)
    2: ["The accused confronted the complainant at {place}, assaulted him with {weapon} and took away {item}."],
    1: ["During a scuffle at {place}, the accused attacked the complainant with {weapon}; belongings were also lost."],
    # women vs body: molestation described like assault
    3: ["The accused caught hold of the complainant at {place} and assaulted her when she resisted."],
}
