"""
REAL, published reference statistics used to evaluate the fidelity of the synthetic
FIR dataset. Every figure here is sourced and cited — this is the ground truth the
synthetic data is measured against in fidelity.py.

Sources
-------
[C11] Census of India 2011, Karnataka district populations.
      https://www.census2011.co.in/census/state/districtlist/karnataka.html
[NCRB22] NCRB "Crime in India 2022", Karnataka figures (as reported by Deccan Herald /
      Vartha Bharati / The Print, Dec 2023). Crimes against women composition,
      chargesheeting rate, cyber-crime volume.
[NCRB22-nat] NCRB 2022 national IPC crime rate = 422.2 per lakh population.

NOTE: real district-level *microdata* (per-FIR) is confidential and unavailable; we
therefore validate against published *aggregates* and *stylized facts*, which is the
standard approach for evaluating synthetic administrative data.
"""

# --- [C11] 2011 Census population by district (mapped to our DistrictID) -----
# Vijayanagara (4019) was carved out of Ballari in 2021 -> no 2011 figure (None).
DISTRICT_POP_2011 = {
    4001: 9_621_551,   # Bengaluru (Urban)
    4002: 990_923,     # Bengaluru Rural
    4003: 1_082_636,   # Ramanagara
    4004: 1_536_401,   # Kolar
    4005: 1_255_104,   # Chikkaballapura
    4006: 2_678_980,   # Tumakuru
    4007: 3_001_127,   # Mysuru
    4008: 1_805_769,   # Mandya
    4009: 1_776_421,   # Hassan
    4010: 1_020_791,   # Chamarajanagar
    4011: 554_519,     # Kodagu
    4012: 2_089_649,   # Dakshina Kannada
    4013: 1_177_361,   # Udupi
    4014: 1_137_961,   # Chikkamagaluru
    4015: 1_752_753,   # Shivamogga
    4016: 1_945_497,   # Davanagere
    4017: 1_659_456,   # Chitradurga
    4018: 2_452_595,   # Ballari
    4019: None,        # Vijayanagara (post-2011)
    4020: 1_389_920,   # Koppal
    4021: 1_928_812,   # Raichur
    4022: 2_566_326,   # Kalaburagi
    4023: 1_174_271,   # Yadgir
    4024: 1_703_300,   # Bidar
    4025: 2_177_331,   # Vijayapura
    4026: 1_889_752,   # Bagalkote
    4027: 4_779_661,   # Belagavi
    4028: 1_847_023,   # Dharwad
    4029: 1_064_570,   # Gadag
    4030: 1_597_668,   # Haveri
    4031: 1_437_169,   # Uttara Kannada
}

# --- [NCRB22] Karnataka crimes-against-women composition, 2022 --------------
# Real counts by category (subset that maps to our CrimeSubHead ids 301-305).
# POCSO is reported under women in NCRB but sits under CrimeHead 4 in our schema,
# so it's excluded from the women-composition comparison.
NCRB22_WOMEN_COUNTS = {
    304: 6201,   # Assault to outrage modesty of woman
    303: 2812,   # Cruelty by husband/relatives
    301: 595,    # Rape
    302: 165,    # Dowry deaths
    305: 78,     # Insult to modesty of woman
}

# Chargesheeting (clearance) rate for crimes against women, Karnataka 2022 [NCRB22]
NCRB22_WOMEN_CHARGESHEET_RATE = 0.828

# Cyber-crime volume, Karnataka 2022 (2nd highest nationally) [NCRB22]
NCRB22_CYBER_CASES = 12556

# National IPC crime rate per lakh population, 2022 [NCRB22-nat]
NCRB22_NATIONAL_IPC_RATE = 422.2

# --- Criminological stylized facts (from the literature) --------------------
# Offending is highly concentrated in a small share of offenders (the "chronic
# offender" finding; Wolfgang et al. 1972; typical offence-count Gini ~0.6-0.75).
STYLIZED_OFFENDER_GINI = (0.55, 0.80)     # plausible range
# Crime counts correlate strongly with population across areal units (Spearman > 0.7).
STYLIZED_POP_CRIME_SPEARMAN_MIN = 0.7
