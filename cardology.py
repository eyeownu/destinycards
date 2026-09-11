"""
Cardology Engine - Open-source implementation of Richmond's quadration mathematics.

The first computational implementation of the card science formulas published in
Olney H. Richmond's "The Mystic Test Book" (1893) and systematized by
Robert Lee Camp in "Cards of Your Destiny" (2014).

MIT License - https://github.com/eyeownu/destinycards
"""

from datetime import date
from dataclasses import dataclass

SUITS = ['H', 'C', 'D', 'S']
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
SOLAR_ORDER = [r + s for s in SUITS for r in RANKS]
PLANETS = ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']
FIXED_CARDS = {'KS', 'JH', '8C'}
SEMI_FIXED_PAIRS = [('AC', '2H'), ('9H', '7D')]

SPIRITUAL_SPREAD = [
    'KS', 'QS', 'JS',
    '7H', '6H', '5H', '4H', '3H', '2H', 'AH',
    'AC', 'KH', 'QH', 'JH', 'TH', '9H', '8H',
    '8C', '7C', '6C', '5C', '4C', '3C', '2C',
    '2D', 'AD', 'KC', 'QC', 'JC', 'TC', '9C',
    '9D', '8D', '7D', '6D', '5D', '4D', '3D',
    '3S', '2S', 'AS', 'KD', 'QD', 'JD', 'TD',
    'TS', '9S', '8S', '7S', '6S', '5S', '4S',
]

LIFE_SPREAD = [
    'KS', '8D', 'TC',
    'AS', '3D', '5C', 'TS', 'QC', 'AC', '3H',
    '2H', '9S', '9C', 'JH', '5S', '7D', '7H',
    '8C', 'JS', '2D', '4C', '6H', 'KD', 'KH',
    'AD', 'AH', '8S', 'TD', 'TH', '4S', '6D',
    '5D', '7C', '9H', '3S', '3C', '5H', 'QD',
    'JD', 'KC', '2C', '7S', '9D', 'JC', 'QS',
    'QH', '6S', '6C', '8H', '2S', '4D', '4H',
]

def solar_value(month, day):
    """SV = 55 - (2*M + D). Returns 0 for Dec 31 (Joker), 1-52 otherwise."""
    return 55 - (2 * month + day)

def sv_to_card(sv):
    if sv == 0: return 'JOKER'
    sv = ((sv - 1) % 52) + 1
    return SOLAR_ORDER[sv - 1]

def birth_card(month, day):
    return sv_to_card(solar_value(month, day))

def quadrate(deck):
    """One quadration: deal 3-at-a-time to 4 piles, stack, deal 1-at-a-time, restack.
    Source: Richmond (1893), Camp p.26-28."""
    names = ['H', 'C', 'D', 'S']
    piles = {n: [] for n in names}
    idx = 0
    while (52 - idx) > 4:
        for p in names:
            group = deck[idx:idx + 3]
            piles[p] = piles[p] + list(reversed(group))
            idx += 3
    for p in names:
        piles[p].append(deck[idx])
        idx += 1
    stacked = piles['H'] + piles['C'] + piles['D'] + piles['S']
    piles2 = {n: [] for n in names}
    for i in range(52):
        piles2[names[i % 4]].append(stacked[-(i + 1)])
    return piles2['H'] + piles2['C'] + piles2['D'] + piles2['S']

def lay_spread(stacked_deck):
    """Lay stacked deck into Grand Solar Spread: 7 rows of 7 right-to-left, last 3 = Crown."""
    rows, pos = [], len(stacked_deck) - 1
    for _ in range(7):
        row = []
        for _ in range(7):
            row.append(stacked_deck[pos]); pos -= 1
        rows.append(list(reversed(row)))
    crown = [stacked_deck[pos - i] for i in range(3)]
    crown.reverse()
    return crown + [c for r in rows for c in r]

def _build_cycle():
    spirit_pos = {c: i for i, c in enumerate(SPIRITUAL_SPREAD)}
    life_pos = {c: i for i, c in enumerate(LIFE_SPREAD)}
    Q = [life_pos[SPIRITUAL_SPREAD[i]] for i in range(52)]
    visited = set()
    for start in range(52):
        if start in visited: continue
        cycle = []
        pos = start
        while pos not in visited:
            visited.add(pos); cycle.append(pos); pos = Q[pos]
        if len(cycle) == 45:
            return [LIFE_SPREAD[p] for p in cycle]
    raise RuntimeError("No 45-cycle found")

MAGIC_CIRCLE = _build_cycle()
_CIRCLE_INDEX = {c: i for i, c in enumerate(MAGIC_CIRCLE)}

def displacement(birth_card_str, age):
    """O(1) displacement: which card's seat does birth_card occupy at given age."""
    if birth_card_str in FIXED_CARDS or birth_card_str not in _CIRCLE_INDEX:
        return birth_card_str
    idx = _CIRCLE_INDEX[birth_card_str]
    return MAGIC_CIRCLE[(idx + age) % 45]

@dataclass
class Spread:
    cards: list
    @property
    def crown(self): return self.cards[0:3]
    @property
    def mercury(self): return self.cards[3:10]
    @property
    def venus(self): return self.cards[10:17]
    @property
    def mars(self): return self.cards[17:24]
    @property
    def jupiter(self): return self.cards[24:31]
    @property
    def saturn(self): return self.cards[31:38]
    @property
    def uranus(self): return self.cards[38:45]
    @property
    def neptune(self): return self.cards[45:52]
    def row(self, planet): return getattr(self, planet.lower())
    def find(self, card): return self.cards.index(card)
    def __str__(self):
        lines = [f"Crown:     {' '.join(self.crown)}"]
        for p in PLANETS:
            lines.append(f"{p:10s}: {' '.join(self.row(p))}")
        return '\n'.join(lines)

def age_spread(age):
    """Compute Grand Solar Spread for any age. Age 0 = Life Spread. Cycles at 90."""
    age = age % 90
    deck = list(SOLAR_ORDER)
    for i in range(age + 1):
        deck = quadrate(deck)
        if i < age:
            deck = list(reversed(deck))
    return Spread(lay_spread(deck))

def weekly_age(dob, target):
    """Which of 90 spreads governs the current week."""
    return ((target - dob).days // 7) % 90

def yearly_period(dob, target):
    """Current 52-day planetary period."""
    last_bday = date(target.year, dob.month, dob.day)
    if last_bday > target:
        last_bday = date(target.year - 1, dob.month, dob.day)
    days = (target - last_bday).days
    age = target.year - dob.year - ((target.month, target.day) < (dob.month, dob.day))
    period = min(days // 52, 6)
    return {'age': age, 'days_since_birthday': days, 'period_index': period,
            'period_planet': PLANETS[period], 'day_in_period': days % 52,
            'week_in_period': (days % 52) // 7}


# --- RTL Life Spread sequence ---
# Cards read right to left, row by row downward.
# Crown (indices 2,1,0) then each of 7 rows reversed.
def _build_rtl_sequence():
    ls = LIFE_SPREAD
    rtl = [ls[2], ls[1], ls[0]]
    for row_start in range(3, 52, 7):
        rtl += list(reversed(ls[row_start:row_start + 7]))
    return rtl

RTL_SEQUENCE = _build_rtl_sequence()
_RTL_INDEX = {c: i for i, c in enumerate(RTL_SEQUENCE)}

# --- Modern planetary rulerships (locked 2026-09-11) ---
SIGN_RULERS = {
    "Aries":       ["Mars"],
    "Taurus":      ["Venus"],
    "Gemini":      ["Mercury"],
    "Cancer":      ["Moon"],
    "Leo":         ["Sun"],
    "Virgo":       ["Mercury"],
    "Libra":       ["Venus"],
    "Scorpio":     ["Mars", "Pluto"],
    "Sagittarius": ["Jupiter"],
    "Capricorn":   ["Saturn"],
    "Aquarius":    ["Uranus"],
    "Pisces":      ["Neptune"],
}

# --- Modern decanate rulers (locked 2026-09-11) ---
DECAN_RULERS = {
    "Aries":       ["Mars",    "Sun",     "Jupiter"],
    "Taurus":      ["Venus",   "Mercury", "Saturn"],
    "Gemini":      ["Mercury", "Venus",   "Saturn"],
    "Cancer":      ["Moon",    "Mars",    "Jupiter"],
    "Leo":         ["Sun",     "Jupiter", "Mars"],
    "Virgo":       ["Mercury", "Saturn",  "Venus"],
    "Libra":       ["Venus",   "Saturn",  "Mercury"],
    "Scorpio":     ["Mars",    "Neptune", "Moon"],
    "Sagittarius": ["Jupiter", "Mars",    "Sun"],
    "Capricorn":   ["Saturn",  "Venus",   "Mercury"],
    "Aquarius":    ["Uranus",  "Mercury", "Venus"],
    "Pisces":      ["Neptune", "Moon",    "Mars"],
}

PLANET_STEPS = {
    "Mercury": 1, "Venus": 2, "Mars": 3, "Jupiter": 4,
    "Saturn": 5, "Uranus": 6, "Neptune": 7, "Pluto": 8,
    "Moon": -1,
    "Sun": 0,
}

SIGN_ENTRY = {
    "Aries": (3,21), "Taurus": (4,20), "Gemini": (5,21), "Cancer": (6,21),
    "Leo": (7,23), "Virgo": (8,23), "Libra": (9,23), "Scorpio": (10,23),
    "Sagittarius": (11,22), "Capricorn": (12,22), "Aquarius": (1,20), "Pisces": (2,19),
}

def get_sun_sign(month, day):
    result = "Capricorn"
    order = [
        ("Aquarius",(1,20)),("Pisces",(2,19)),("Aries",(3,21)),("Taurus",(4,20)),
        ("Gemini",(5,21)),("Cancer",(6,21)),("Leo",(7,23)),("Virgo",(8,23)),
        ("Libra",(9,23)),("Scorpio",(10,23)),("Sagittarius",(11,22)),("Capricorn",(12,22)),
    ]
    for sign,(em,ed) in order:
        if (month,day) >= (em,ed):
            result = sign
    return result

def get_decanate_index(month, day, sign):
    em, ed = SIGN_ENTRY[sign]
    ref = date(2000, em, ed)
    bdate = date(2000, month, day)
    days = (bdate - ref).days
    if days < 0: days += 365
    return min(days // 10, 2)

def rtl_step(bc, steps):
    if bc not in _RTL_INDEX: return bc
    pos = _RTL_INDEX[bc]
    return RTL_SEQUENCE[(pos + steps) % 52]

def get_prc_decanate(month, day):
    bc = birth_card(month, day)
    sign = get_sun_sign(month, day)
    dec_idx = get_decanate_index(month, day, sign)
    dec_ruler = DECAN_RULERS[sign][dec_idx]
    s = PLANET_STEPS.get(dec_ruler, 0)
    dec_card = bc if s == 0 else rtl_step(bc, s)
    rulers = SIGN_RULERS[sign]
    prc_list = []
    for planet in rulers:
        ps = PLANET_STEPS.get(planet, 0)
        prc_card = bc if ps == 0 else rtl_step(bc, ps)
        prc_list.append({"planet": planet, "card": prc_card})
    return {
        "birth_card": bc, "sun_sign": sign,
        "decanate": dec_idx + 1, "decan_ruler": dec_ruler,
        "decanate_card": dec_card, "prc": prc_list,
    }

class CardologyEngine:
    def birth_card(self, month, day): return birth_card(month, day)
    def displacement(self, card, age): return displacement(card, age)
    def age_spread(self, age): return age_spread(age)
    def weekly_age(self, dob, target): return weekly_age(dob, target)
    def yearly_period(self, dob, target): return yearly_period(dob, target)

if __name__ == '__main__':
    deck = list(SOLAR_ORDER)
    deck = quadrate(deck)
    spread = lay_spread(deck)
    assert spread == LIFE_SPREAD, "Quadration failed"
    print("ok Quadration verified (52/52)")
    assert birth_card(5, 11) == '8D'
    assert birth_card(12, 31) == 'JOKER'
    print("ok Solar Value verified")
    assert displacement('8D', 42) == 'TC'
    assert displacement('8D', 48) == 'QC'
    print("ok Displacement verified")
    for card in MAGIC_CIRCLE:
        assert displacement(card, 45) == card
    print("ok 45-cycle verified")
    s0, s90 = age_spread(0), age_spread(90)
    assert s0.cards == s90.cards
    print("ok 90-cycle verified (age 0 = age 90)")
    print(f"\n8D age 42 displaces: {displacement('8D', 42)}")
    print(f"\nAge 42 Spread:")
    print(age_spread(42))
