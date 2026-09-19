"""
cardology.py — Richmond/Camp Destiny Card computation engine

System: The Book of Destiny (Robert Lee Camp), derived from Olney H. Richmond's
        "The Mystic Test Book" (1893). This is the authoritative calculation layer.
        All rules encoded here are verified by Prince (system owner).
        Source of truth: BookStack 1535 (Cardology Engine book).
        SOP: BookStack 1562 (Reading Protocol SOP).

PLANET NUMBERING CONVENTION — 1-INDEXED (agreed 2026-09-11):
    0 = Sun (the subject / center — used as reference only)
    1 = Mercury
    2 = Venus
    3 = Mars
    4 = Jupiter
    5 = Saturn
    6 = Uranus
    7 = Neptune
    PLANET_LABELS list is 0-indexed internally (PLANET_LABELS[0]='Mercury'),
    but all reading steps are expressed as 1-indexed counts:
    "6 steps left = Uranus" because Uranus is the 6th planet.

SPREAD ORIENTATION (confirmed from source):
    Rows:    Mercury (row 1, top)  →  Neptune (row 7, bottom)
    Columns: Mercury (col 1, rightmost)  →  Neptune (col 7, leftmost)
    Reading direction: RIGHT TO LEFT, then DOWN. 1-indexed from the right.
    Grid array storage: left-to-right (col7 at low index, col1 at high index within each row).
    Crown: 3 cards above center columns only — Mars(col3), Jupiter(col4), Saturn(col5).

THE 13-CARD YEARLY READING (confirmed 2026-09-11):
    13 × 4 suits = 52 cards = 52 weeks. The 13-card structure is the fundamental unit.
    From the birth card position in the age spread:
        Moon         : 1 step RIGHT  (the card read just before BC in R-to-L direction)
        Birth Card   : the subject (step 0)
        Mercury      : 1 step left
        Venus        : 2 steps left
        Mars         : 3 steps left
        Jupiter      : 4 steps left
        Saturn       : 5 steps left
        Uranus       : 6 steps left
        Neptune      : 7 steps left
        Pluto        : 8 steps left
        Result       : 9 steps left
        Displacement : Life Spread card at BC's current position in the age spread
        Environment  : Card at BC's permanent Life Spread home in the age spread
        Long Range   : Direct card at (age%7) planet in get_age_spread(age//7)

    Symmetric pair:
        Displacement = LIFE_SPREAD[age_spread.index(bc)]  — where did BC land?
        Environment  = age_spread[LIFE_SPREAD.index(bc)]  — what landed at BC's home?

    LEFT WRAP RULE: within a row, leftmost (col7/Neptune) wraps to rightmost (col1/Mercury)
    of the NEXT row down. Neptune row leftmost wraps to Mercury row rightmost (full cycle).
    Crown leftmost wraps to Mercury row rightmost.

    MOON WRAP RULE (going right): Mercury col (rightmost of any row) wraps UP to
    Mercury col of the row above. Mercury row rightmost wraps to Crown rightmost.

THREE SIGNIFICATORS:
    A complete reading requires three spreads — one per significator:
    1. Birth Card (BC) — primary, carries most weight
    2. Planetary Ruling Card (PRC) — secondary, derived from sun sign ruling planet
    3. Decanate Card (Dec) — third significator
    Connections that don't appear in one spread show across the three.

THREE-LAYER MATRIX:
    Layer 1 (Active)     : the card from the current age spread
    Layer 2 (Underlying) : LIFE_SPREAD[age_spread.index(active_card)] — see get_underlying()
    Layer 3 (Spiritual)  : suit of SPIRITUAL_SPREAD at card's permanent Life Spread home
    Spiritual suit domains: H=relationships, C=mind/action, D=material, S=transformation

SEPTENARY SYSTEM (Long Range):
    Life divides into 7-year blocks. Within each block, years cycle Mercury→Neptune.
    period = age // 7         (which 7-year block; 0=Life Spread block)
    year_planet = PLANET_LABELS[age % 7]   (0=Mercury ... 6=Neptune)
    long_range_card = read_direct(get_age_spread(period), bc)[year_planet]
    Verified: TH age 49=3C (Mercury year), age 50=8H (Venus year). 2026-09-11.

FREE vs PROPRIETARY TIER SPLIT:
    Basic  (/basic):  BC + Mercury→Neptune direct + Displacement + 52-day + weekly + daily
    Full   (/full):   All 13 cards + verticals for all 7 periods + Three-Layer Matrix
                      + all three significator spreads + relationship layer
    See SOP BookStack 1562 for complete tier definitions.

FIXED AND SEMI-FIXED CARDS:
    Fixed (never move in any spread): KS, JH, 8C
    Semi-fixed pairs (do not quadrate): AC↔2H, 9H↔7D
    These cards occupy all positions simultaneously — their period cards = birth card.
"""

BIRTH_CARD_TABLE = {
    (1,1):'KS',
    (1,2):'QS',
    (1,3):'JS',
    (1,4):'TS',
    (1,5):'9S',
    (1,6):'8S',
    (1,7):'7S',
    (1,8):'6S',
    (1,9):'5S',
    (1,10):'4S',
    (1,11):'3S',
    (1,12):'2S',
    (1,13):'AS',
    (1,14):'KD',
    (1,15):'QD',
    (1,16):'JD',
    (1,17):'TD',
    (1,18):'9D',
    (1,19):'8D',
    (1,20):'7D',
    (1,21):'6D',
    (1,22):'5D',
    (1,23):'4D',
    (1,24):'3D',
    (1,25):'2D',
    (1,26):'AD',
    (1,27):'KC',
    (1,28):'QC',
    (1,29):'JC',
    (1,30):'TC',
    (1,31):'9C',
    (2,1):'JS',
    (2,2):'TS',
    (2,3):'9S',
    (2,4):'8S',
    (2,5):'7S',
    (2,6):'6S',
    (2,7):'5S',
    (2,8):'4S',
    (2,9):'3S',
    (2,10):'2S',
    (2,11):'AS',
    (2,12):'KD',
    (2,13):'QD',
    (2,14):'JD',
    (2,15):'TD',
    (2,16):'9D',
    (2,17):'8D',
    (2,18):'7D',
    (2,19):'6D',
    (2,20):'5D',
    (2,21):'4D',
    (2,22):'3D',
    (2,23):'2D',
    (2,24):'AD',
    (2,25):'KC',
    (2,26):'QC',
    (2,27):'JC',
    (2,28):'TC',
    (2,29):'9C',
    (3,1):'9S',
    (3,2):'8S',
    (3,3):'7S',
    (3,4):'6S',
    (3,5):'5S',
    (3,6):'4S',
    (3,7):'3S',
    (3,8):'2S',
    (3,9):'AS',
    (3,10):'KD',
    (3,11):'QD',
    (3,12):'JD',
    (3,13):'TD',
    (3,14):'9D',
    (3,15):'8D',
    (3,16):'7D',
    (3,17):'6D',
    (3,18):'5D',
    (3,19):'4D',
    (3,20):'3D',
    (3,21):'2D',
    (3,22):'AD',
    (3,23):'KC',
    (3,24):'QC',
    (3,25):'JC',
    (3,26):'TC',
    (3,27):'9C',
    (3,28):'8C',
    (3,29):'7C',
    (3,30):'6C',
    (3,31):'5C',
    (4,1):'7S',
    (4,2):'6S',
    (4,3):'5S',
    (4,4):'4S',
    (4,5):'3S',
    (4,6):'2S',
    (4,7):'AS',
    (4,8):'KD',
    (4,9):'QD',
    (4,10):'JD',
    (4,11):'TD',
    (4,12):'9D',
    (4,13):'8D',
    (4,14):'7D',
    (4,15):'6D',
    (4,16):'5D',
    (4,17):'4D',
    (4,18):'3D',
    (4,19):'2D',
    (4,20):'AD',
    (4,21):'KC',
    (4,22):'QC',
    (4,23):'JC',
    (4,24):'TC',
    (4,25):'9C',
    (4,26):'8C',
    (4,27):'7C',
    (4,28):'6C',
    (4,29):'5C',
    (4,30):'4C',
    (5,1):'5S',
    (5,2):'4S',
    (5,3):'3S',
    (5,4):'2S',
    (5,5):'AS',
    (5,6):'KD',
    (5,7):'QD',
    (5,8):'JD',
    (5,9):'TD',
    (5,10):'9D',
    (5,11):'8D',
    (5,12):'7D',
    (5,13):'6D',
    (5,14):'5D',
    (5,15):'4D',
    (5,16):'3D',
    (5,17):'2D',
    (5,18):'AD',
    (5,19):'KC',
    (5,20):'QC',
    (5,21):'JC',
    (5,22):'TC',
    (5,23):'9C',
    (5,24):'8C',
    (5,25):'7C',
    (5,26):'6C',
    (5,27):'5C',
    (5,28):'4C',
    (5,29):'3C',
    (5,30):'2C',
    (5,31):'AC',
    (6,1):'3S',
    (6,2):'2S',
    (6,3):'AS',
    (6,4):'KD',
    (6,5):'QD',
    (6,6):'JD',
    (6,7):'TD',
    (6,8):'9D',
    (6,9):'8D',
    (6,10):'7D',
    (6,11):'6D',
    (6,12):'5D',
    (6,13):'4D',
    (6,14):'3D',
    (6,15):'2D',
    (6,16):'AD',
    (6,17):'KC',
    (6,18):'QC',
    (6,19):'JC',
    (6,20):'TC',
    (6,21):'9C',
    (6,22):'8C',
    (6,23):'7C',
    (6,24):'6C',
    (6,25):'5C',
    (6,26):'4C',
    (6,27):'3C',
    (6,28):'2C',
    (6,29):'AC',
    (6,30):'KH',
    (7,1):'AS',
    (7,2):'KD',
    (7,3):'QD',
    (7,4):'JD',
    (7,5):'TD',
    (7,6):'9D',
    (7,7):'8D',
    (7,8):'7D',
    (7,9):'6D',
    (7,10):'5D',
    (7,11):'4D',
    (7,12):'3D',
    (7,13):'2D',
    (7,14):'AD',
    (7,15):'KC',
    (7,16):'QC',
    (7,17):'JC',
    (7,18):'TC',
    (7,19):'9C',
    (7,20):'8C',
    (7,21):'7C',
    (7,22):'6C',
    (7,23):'5C',
    (7,24):'4C',
    (7,25):'3C',
    (7,26):'2C',
    (7,27):'AC',
    (7,28):'KH',
    (7,29):'QH',
    (7,30):'JH',
    (7,31):'TH',
    (8,1):'QD',
    (8,2):'JD',
    (8,3):'TD',
    (8,4):'9D',
    (8,5):'8D',
    (8,6):'7D',
    (8,7):'6D',
    (8,8):'5D',
    (8,9):'4D',
    (8,10):'3D',
    (8,11):'2D',
    (8,12):'AD',
    (8,13):'KC',
    (8,14):'QC',
    (8,15):'JC',
    (8,16):'TC',
    (8,17):'9C',
    (8,18):'8C',
    (8,19):'7C',
    (8,20):'6C',
    (8,21):'5C',
    (8,22):'4C',
    (8,23):'3C',
    (8,24):'2C',
    (8,25):'AC',
    (8,26):'KH',
    (8,27):'QH',
    (8,28):'JH',
    (8,29):'TH',
    (8,30):'9H',
    (8,31):'8H',
    (9,1):'TD',
    (9,2):'9D',
    (9,3):'8D',
    (9,4):'7D',
    (9,5):'6D',
    (9,6):'5D',
    (9,7):'4D',
    (9,8):'3D',
    (9,9):'2D',
    (9,10):'AD',
    (9,11):'KC',
    (9,12):'QC',
    (9,13):'JC',
    (9,14):'TC',
    (9,15):'9C',
    (9,16):'8C',
    (9,17):'7C',
    (9,18):'6C',
    (9,19):'5C',
    (9,20):'4C',
    (9,21):'3C',
    (9,22):'2C',
    (9,23):'AC',
    (9,24):'KH',
    (9,25):'QH',
    (9,26):'JH',
    (9,27):'TH',
    (9,28):'9H',
    (9,29):'8H',
    (9,30):'7H',
    (10,1):'8D',
    (10,2):'7D',
    (10,3):'6D',
    (10,4):'5D',
    (10,5):'4D',
    (10,6):'3D',
    (10,7):'2D',
    (10,8):'AD',
    (10,9):'KC',
    (10,10):'QC',
    (10,11):'JC',
    (10,12):'TC',
    (10,13):'9C',
    (10,14):'8C',
    (10,15):'7C',
    (10,16):'6C',
    (10,17):'5C',
    (10,18):'4C',
    (10,19):'3C',
    (10,20):'2C',
    (10,21):'AC',
    (10,22):'KH',
    (10,23):'QH',
    (10,24):'JH',
    (10,25):'TH',
    (10,26):'9H',
    (10,27):'8H',
    (10,28):'7H',
    (10,29):'6H',
    (10,30):'5H',
    (10,31):'4H',
    (11,1):'6D',
    (11,2):'5D',
    (11,3):'4D',
    (11,4):'3D',
    (11,5):'2D',
    (11,6):'AD',
    (11,7):'KC',
    (11,8):'QC',
    (11,9):'JC',
    (11,10):'TC',
    (11,11):'9C',
    (11,12):'8C',
    (11,13):'7C',
    (11,14):'6C',
    (11,15):'5C',
    (11,16):'4C',
    (11,17):'3C',
    (11,18):'2C',
    (11,19):'AC',
    (11,20):'KH',
    (11,21):'QH',
    (11,22):'JH',
    (11,23):'TH',
    (11,24):'9H',
    (11,25):'8H',
    (11,26):'7H',
    (11,27):'6H',
    (11,28):'5H',
    (11,29):'4H',
    (11,30):'3H',
    (12,1):'4D',
    (12,2):'3D',
    (12,3):'2D',
    (12,4):'AD',
    (12,5):'KC',
    (12,6):'QC',
    (12,7):'JC',
    (12,8):'TC',
    (12,9):'9C',
    (12,10):'8C',
    (12,11):'7C',
    (12,12):'6C',
    (12,13):'5C',
    (12,14):'4C',
    (12,15):'3C',
    (12,16):'2C',
    (12,17):'AC',
    (12,18):'KH',
    (12,19):'QH',
    (12,20):'JH',
    (12,21):'TH',
    (12,22):'9H',
    (12,23):'8H',
    (12,24):'7H',
    (12,25):'6H',
    (12,26):'5H',
    (12,27):'4H',
    (12,28):'3H',
    (12,29):'2H',
    (12,30):'AH',
    (12,31):'KS',
}
# ─── CONSTANTS ────────────────────────────────────────────────────────────────────
FIXED_CARDS = frozenset({'KS','JH','8C'})       # never move in any spread
SEMI_FIXED_PAIRS = frozenset({'AC','2H','9H','7D'})  # do not quadrate: AC<->2H, 9H<->7D
NO_ROTATE = FIXED_CARDS | SEMI_FIXED_PAIRS       # legacy union; get_timing() uses only FIXED_CARDS for is_fixed check (semi-fixed cards ARE findable in spread)

# 1-indexed planet order (Mercury=1 ... Neptune=7; Sun=0 as subject/reference).
# PLANET_LABELS is 0-indexed internally: PLANET_LABELS[0]='Mercury' etc.
# When counting steps in a reading, use 1-indexed: "6 steps left = Uranus (6th planet)".
PLANET_LABELS = ['Mercury','Venus','Mars','Jupiter','Saturn','Uranus','Neptune']
SUITS=['H','C','D','S']
RANKS=['A','2','3','4','5','6','7','8','9','T','J','Q','K']
SOLAR_DECK=[r+s for s in SUITS for r in RANKS]

def _quadrate(deck):
    """Apply one pass of Richmond's quadration procedure to a 52-card deck.
    Deals into 4 suit piles (H/C/D/S) in groups of 3, reversed, with 1 remainder each.
    Then re-stacks and reverses. One full quadration cycle = one year of age.
    Called by get_age_spread(age) which applies age+1 passes with deck reversal between.
    Source: Richmond, The Mystic Test Book (1893); verified computationally 2026-09-09.
    """
    names=['H','C','D','S']
    piles={n:[] for n in names}
    idx=0
    while (52-idx)>4:
        for p in names:
            piles[p]=piles[p]+list(reversed(deck[idx:idx+3]))
            idx+=3
    for p in names:
        piles[p].append(deck[idx]);idx+=1
    stacked=piles['H']+piles['C']+piles['D']+piles['S']
    piles2={n:[] for n in names}
    for i in range(52):
        piles2[names[i%4]].append(stacked[-(i+1)])
    return piles2['H']+piles2['C']+piles2['D']+piles2['S']

def _lay_spread(deck):
    """Lay a quadrated deck into the 7x7 grid + 3-card Crown format.
    Returns a list of 52 cards: indices [0,1,2] = Crown, [3..51] = 7 rows of 7.
    Grid storage is left-to-right per row: index 3 = row1 col7 (Neptune col, leftmost),
    index 9 = row1 col1 (Mercury col, rightmost).
    Physical reading direction is RIGHT TO LEFT (Mercury col first, Neptune col last),
    so decrement array index to move left in the reading direction.
    Crown sits above columns 3/4/5 (Mars/Jupiter/Saturn). No crown for cols 1/2/6/7.
    """
    pos=len(deck)-1
    rows=[]
    for _ in range(7):
        row=[deck[pos-c] for c in range(7)]
        rows.append(list(reversed(row)))
        pos-=7
    crown=list(reversed([deck[pos-c] for c in range(3)]))
    return crown+[c for r in rows for c in r]

_SPREAD_CACHE={}

def get_age_spread(age):
    """Return the Grand Solar Spread for a given age (0-89; wraps at 90).
    Applies Richmond quadration age+1 times, with deck reversal between each pass.
    Result is cached. age=0 returns the Life Spread (permanent card home positions).
    age=45 and age=90 also return the Life Spread (90-year full cycle).
    Used for: yearly spreads (get_age_spread(age)), long range septenary spreads
    (get_age_spread(age//7)), and weekly spreads (get_age_spread(days_alive//7 % 90)).
    Bug fixed 2026-09-10: reversal between quadrations was missing, causing wrong spreads
    for all ages > 0. Verified against Prince's known spreads for ages 42 and 17.
    """
    age=age%90
    if age not in _SPREAD_CACHE:
        deck=list(SOLAR_DECK)
        for i in range(age+1):
            deck=_quadrate(deck)
            if i < age:
                deck=list(reversed(deck))  # required between quadrations
        _SPREAD_CACHE[age]=_lay_spread(deck)
    return _SPREAD_CACHE[age]

LIFE_SPREAD=get_age_spread(0)
LIFE_POSITION={card:i for i,card in enumerate(LIFE_SPREAD)}
# Layer 3: Natural/Spiritual/Perfect Spread.
# Source: Camp (Love Cards / Exploring the Little Book). Spades K->A, Diamonds K->A,
# Clubs K->A, Hearts K->A. This is NOT SOLAR_DECK -- SOLAR_DECK is only the
# computational starting deck for quadration. The Spiritual Spread is the fixed
# eternal template that every other spread derives from.
NATURAL_ORDER = (
    ['KS','QS','JS','TS','9S','8S','7S','6S','5S','4S','3S','2S','AS'] +
    ['KD','QD','JD','TD','9D','8D','7D','6D','5D','4D','3D','2D','AD'] +
    ['KC','QC','JC','TC','9C','8C','7C','6C','5C','4C','3C','2C','AC'] +
    ['KH','QH','JH','TH','9H','8H','7H','6H','5H','4H','3H','2H','AH']
)
SPIRITUAL_SPREAD=_lay_spread(list(NATURAL_ORDER))
# Verified: Mercury row=Hearts, Mars row=Clubs, Jupiter row=mixed/Clubs,
#           Saturn row=Diamonds. SPIRITUAL_SPREAD[19]="6C" (2D Life Spread position).

def _rtl_step(pos):
    """One RTL step from current array index pos.
    Rules (confirmed 2026-09-13 by 7D age-40 trace):
    - Crown non-leftmost (idx 1-2): decrement within Crown row.
    - Crown leftmost (idx 0): jump to Row1 rightmost (idx 9).
    - Grid non-leftmost: decrement within row (col moves right->left in RTL direction).
    - Grid leftmost (col7, idx where (idx-3)%7==0): jump to rightmost of NEXT row
      BELOW (+13). The simple pos-1 was wrong here -- it went UP to the previous row.
    Bug confirmed: current code went Row2-leftmost(10) -> Row1-rightmost(9) (backward up)
    instead of Row2-leftmost(10) -> Row3-rightmost(23) (forward down).
    """
    if pos == 0:                    # Crown leftmost -> Row1 rightmost
        return 9
    if pos <= 2:                    # Crown (non-leftmost) -> one step left in Crown
        return pos - 1
    col_in_row = (pos - 3) % 7     # 0 = leftmost col7, 6 = rightmost col1
    if col_in_row == 0:             # Grid leftmost -> rightmost of row below (+13)
        next_row = pos + 13
        if next_row > 51:              # P49 (Neptune x Neptune) has no row below -> wrap to Crown Mars (P50, idx 2)
            return 2
        return next_row
    return pos - 1                  # normal RTL step within row

def read_direct(spread,birth_card):
    """Read the 7 direct planetary cards from birth_card in the given spread.
    Direction: RIGHT TO LEFT using _rtl_step() for each move.
    Row boundary rule: when at leftmost of any grid row (col7), the next card is
    the RIGHTMOST of the row below (col1), not a simple index decrement.
    Crown leftmost wraps to Row1 rightmost (index 9).
    Bug fixed 2026-09-13: simple pos-1 crossed row boundaries going UPWARD (wrong).
    Verified: 7D age40 Uranus=7S Neptune=3D | 8D age42 values unchanged.
    """
    idx=spread.index(birth_card)
    cards={}
    pos=idx
    for label in PLANET_LABELS:
        pos=_rtl_step(pos)
        cards[label]=spread[pos]
    return cards

def read_vertical(spread,birth_card):
    """Read the 7 vertical (column) cards for birth_card in the given spread.
    Rule: start one step ABOVE the birth card in its column, walk upward (decreasing row),
    wrap from Row 1 back to Row 7, assign Mercury through Neptune in that walk order.
    Crown cards sit above Row 1, so the first step immediately wraps to Row 7 (Neptune row)
    and reads upward through all 7 rows - same result as the previous planets_reversed logic.
    Grid cards: walk starts above birth card position, wraps at top, so birth card itself
    lands at Neptune period (step 7, back to self).
    Column for Crown cards: Crown 1=col2(Mars), Crown 2=col3(Jupiter), Crown 3=col4(Saturn).
    Column for grid cards: (idx - 3) % 7, where 0=Neptune col (leftmost), 6=Mercury col (rightmost).
    Returns dict {planet_name: card_code} for Mercury through Neptune.
    Vertical + Direct are ALWAYS from the SAME age spread (not different spreads).
    Bug fixed 2026-09-10: was using forward row order; corrected to reversed.
    Bug fixed 2026-09-19: bottom-to-top was only correct for Crown cards. Grid cards need
    column-relative upward walk from birth card position. Verified: 8D age42 Crown unchanged,
    8D age50 Row4/Uranus-col gives Mercury=QH,Venus=6C,Mars=KD,Jupiter=2D,Saturn=AH,Uranus=TS.
    Confirmed by Prince 2026-09-19.
    """
    idx=spread.index(birth_card)
    if idx < 3:
        # Crown card: above Row 1, first step wraps to Row 7, read bottom-to-top
        col=[2,3,4][idx]
        planets_reversed=list(reversed(PLANET_LABELS))
        return {label:spread[3+i*7+col] for i,label in enumerate(planets_reversed)}
    else:
        # Grid card: start one step above birth card, walk upward, wrap Row1->Row7
        col=(idx-3)%7
        birth_row=(idx-3)//7  # 0-indexed: 0=Mercury row, 6=Neptune row
        cards={}
        for step,label in enumerate(PLANET_LABELS,start=1):
            row=(birth_row-step)%7
            cards[label]=spread[3+row*7+col]
        return cards


def _step_left(spread, bc_idx, n):
    """Walk n steps LEFT from bc_idx using _rtl_step() for each move.
    Uses same row-boundary logic as read_direct.
    Used for: Pluto (n=8), Result (n=9), or any future left-step derivation."""
    pos = bc_idx
    for _ in range(n):
        pos = _rtl_step(pos)
    return spread[pos]


def _idx_to_pos(idx):
    """Array index (0-51) -> position number (1-52), RTL top-to-bottom, Crown last.
    P1=Mercury x Mercury (idx 9). P49=Neptune x Neptune (idx 45).
    P50=Crown Mars rightmost (idx 2). P51=Crown Jupiter (idx 1). P52=Crown Saturn leftmost (idx 0).
    Confirmed: KS=52, JH=11, 8C=21."""
    if idx == 0: return 52
    if idx == 1: return 51
    if idx == 2: return 50
    row = (idx - 3) // 7
    col_from_right = 6 - (idx - 3) % 7
    return row * 7 + col_from_right + 1

def _pos_to_idx(pos):
    """Position number (1-52) -> array index (0-51)."""
    if pos == 52: return 0
    if pos == 51: return 1
    if pos == 50: return 2
    row = (pos - 1) // 7
    col_from_left = 6 - (pos - 1) % 7
    return 3 + row * 7 + col_from_left

def _get_moon(spread, bc_idx):
    """Moon card = card at position (P_birthcard - 1) in the spread.
    Uses position numbering (1-52 RTL), NOT array index stepping.
    Confirmed 2026-09-12: 8D at P50 age 42 -> Moon=P49=4S.
    Cross-check: 4S Mercury direct = 8D. Verified."""
    p_bc   = _idx_to_pos(bc_idx)
    p_moon = p_bc - 1 if p_bc > 1 else 52
    return spread[_pos_to_idx(p_moon)]

def get_underlying(card, age_spread):
    """Return Life Spread underlying card + row/col rulers for card's grid position."""
    try:
        idx = age_spread.index(card)
    except ValueError:
        return None
    underlying = LIFE_SPREAD[idx]
    if idx < 3:
        # Crown: idx 2 (rightmost) = Crown 1 = Mars col
        #        idx 1 (center)    = Crown 2 = Jupiter col
        #        idx 0 (leftmost)  = Crown 3 = Saturn col
        crown_num = 3 - idx          # 1-indexed right-to-left
        crown_col = {2:'Mars', 1:'Jupiter', 0:'Saturn'}[idx]
        return {'card': underlying, 'position': f'Crown {crown_num}',
                'row_ruler': 'Crown', 'col_ruler': crown_col}
    else:
        row0 = (idx - 3) // 7        # 0-indexed: 0=Mercury row, 6=Neptune row
        col0 = (idx - 3) % 7         # 0-indexed from left: 0=Neptune col, 6=Mercury col
        row_ruler = PLANET_LABELS[row0]
        col_ruler = PLANET_LABELS[6 - col0]   # invert: leftmost=Neptune=index6
        return {'card': underlying,
                'position': f'Row {row0+1} Col {7-col0}',  # 1-indexed RTL
                'row_ruler': row_ruler, 'col_ruler': col_ruler}

def get_spiritual_suit(card, age_spread=None):
    """Return the permanent Spiritual Spread suit of a card.
    Looks up the card's fixed position in the Life Spread, then reads the
    Spiritual Spread card at that same grid index.
    Spiritual suit is a permanent property of the card -- 2D is always Clubs
    (Mars row, 6C position) regardless of which age spread it currently occupies.
    Suit mapping: H=Hearts(Mercury), C=Clubs(Mars), D=Diamonds(Saturn), S=Spades.
    age_spread kept for API compatibility but is not used."""
    try:
        ls_idx = LIFE_SPREAD.index(card)   # permanent Life Spread home position
    except ValueError:
        return None
    return SPIRITUAL_SPREAD[ls_idx][-1]  # suit of the Spiritual card at that position


# PRC and Decanate Card (ported from destiny-birth-card.php, confirmed working)
SIGN_RULERS = {
    'Aries':['Mars'],'Taurus':['Venus'],'Gemini':['Mercury'],
    'Cancer':['Moon'],'Leo':['Sun'],'Virgo':['Mercury'],'Libra':['Venus'],
    'Scorpio':['Mars','Pluto'],'Sagittarius':['Jupiter'],
    'Capricorn':['Saturn'],'Aquarius':['Uranus'],'Pisces':['Neptune'],
}
DECAN_RULERS = {
    'Aries':['Mars','Sun','Jupiter'],'Taurus':['Venus','Mercury','Saturn'],
    'Gemini':['Mercury','Venus','Saturn'],'Cancer':['Moon','Mars','Jupiter'],
    'Leo':['Sun','Jupiter','Mars'],'Virgo':['Mercury','Saturn','Venus'],
    'Libra':['Venus','Saturn','Mercury'],'Scorpio':['Mars','Neptune','Moon'],
    'Sagittarius':['Jupiter','Mars','Sun'],'Capricorn':['Saturn','Venus','Mercury'],
    'Aquarius':['Uranus','Mercury','Venus'],'Pisces':['Neptune','Moon','Mars'],
}
SIGN_ENTRY = {
    'Aries':(3,21),'Taurus':(4,20),'Gemini':(5,21),'Cancer':(6,21),
    'Leo':(7,23),'Virgo':(8,23),'Libra':(9,23),'Scorpio':(10,23),
    'Sagittarius':(11,22),'Capricorn':(12,22),'Aquarius':(1,20),'Pisces':(2,19),
}
ZODIAC = [
    (3,21,4,19,'Aries'),(4,20,5,20,'Taurus'),(5,21,6,20,'Gemini'),
    (6,21,7,22,'Cancer'),(7,23,8,22,'Leo'),(8,23,9,22,'Virgo'),
    (9,23,10,22,'Libra'),(10,23,11,21,'Scorpio'),(11,22,12,21,'Sagittarius'),
    (12,22,12,31,'Capricorn'),(1,1,1,19,'Capricorn'),(1,20,2,18,'Aquarius'),
    (2,19,3,20,'Pisces'),
]
PLANET_STEPS = {'Mercury':1,'Venus':2,'Mars':3,'Jupiter':4,'Saturn':5,'Uranus':6,'Neptune':7,'Pluto':8}

def _get_sun_sign(month, day):
    for m1,d1,m2,d2,sign in ZODIAC:
        if (month==m1 and day>=d1) or (month==m2 and day<=d2): return sign
    return None

def _ls_step_left(birth_card, n):
    pos = LIFE_SPREAD.index(birth_card)
    for _ in range(n):
        pos -= 1
        if pos < 0: pos = 9
    return LIFE_SPREAD[pos]

def get_prc(month, day):
    bc = get_birth_card(month, day)
    if not bc: return []
    sign = _get_sun_sign(month, day)
    if not sign: return []
    bc_idx = LIFE_SPREAD.index(bc)
    out = []
    for planet in SIGN_RULERS.get(sign, []):
        if planet == 'Sun': card = bc
        elif planet == 'Moon': card = _get_moon(LIFE_SPREAD, bc_idx)
        else: card = _ls_step_left(bc, PLANET_STEPS[planet])
        out.append({'planet': planet, 'card': card})
    return out

def get_decanate_card(month, day):
    bc = get_birth_card(month, day)
    if not bc: return None
    sign = _get_sun_sign(month, day)
    if not sign: return None
    entry = SIGN_ENTRY.get(sign)
    if not entry: return None
    from datetime import date as _d
    days = (_d(2000, month, day) - _d(2000, entry[0], entry[1])).days
    if days < 0: days += 365
    dec_idx = min(days // 10, 2)
    sub = DECAN_RULERS[sign][dec_idx]
    bc_idx = LIFE_SPREAD.index(bc)
    if sub == 'Sun': card = bc
    elif sub == 'Moon': card = _get_moon(LIFE_SPREAD, bc_idx)
    else: card = _ls_step_left(bc, PLANET_STEPS[sub])
    return {'planet': sub, 'card': card, 'decanate': ['1st','2nd','3rd'][dec_idx], 'sign': sign}

def get_birth_card(month,day):
    return BIRTH_CARD_TABLE.get((month,day))

def _calendar_age(dob,target):
    age=target.year-dob.year
    if (target.month,target.day)<(dob.month,dob.day): age-=1
    return age

def _last_birthday(dob,target):
    try: bday=dob.replace(year=target.year)
    except ValueError: bday=dob.replace(year=target.year,day=28)
    if bday<=target: return bday
    try: return dob.replace(year=target.year-1)
    except ValueError: return dob.replace(year=target.year-1,day=28)

def get_timing(dob, target, birth_card_override=None):
    """Compute the full cardology timing reading for a birth date and target date.
    Implements the Reading Protocol SOP (BookStack 1562). Returns the Birth Card spread
    layer of a complete reading. PRC and Decanate spreads are separate calls (not yet built).

    Currently implemented (13-card layout):
        yearly.direct    : Mercury through Neptune (steps 1-7 left)
        yearly.vertical  : vertical column cards for all 7 planets
        long_range       : septenary card (get_age_spread(age//7), planet=PLANET_LABELS[age%7])
        Displacement     : LIFE_SPREAD[age_spread.index(bc)] — where BC landed
        period_52day     : current 52-day period (direct + vertical + underlying + spiritual)
        weekly           : weekly spread direct cards
        daily            : daily card from weekly spread

    NOT YET IMPLEMENTED (see SOP backlog):
        Moon card        : 1 step RIGHT of BC in age spread
        Pluto card       : 8 steps left
        Result card      : 9 steps left
        Environment card : age_spread[LIFE_SPREAD.index(bc)] — what landed at BC's home
        Period objects   : 7 {direct, vertical, active} pairs (data exists, not restructured)
        Three-Layer Matrix on all 13 cards (only applied to 52-day currently)

    Free vs proprietary split: see SOP BookStack 1562.
    Returns dict. event_fields sub-dict maps directly to POST /reading/event inputs.
    """
    # PRC and Decanate always derived from the original DOB
    prc_list  = get_prc(dob.month, dob.day)
    dec_data  = get_decanate_card(dob.month, dob.day)
    # Birth card: use override for PRC/Dec spread calls, else derive from DOB
    if birth_card_override:
        birth_card = birth_card_override
    else:
        birth_card = get_birth_card(dob.month, dob.day)
        if not birth_card: return {'error': f'No birth card for {dob.month}/{dob.day}'}
    # For overridden cards, don't re-expose PRC/Dec (they belong to the primary BC spread)
    if birth_card_override:
        prc_list = []
        dec_data = None
    age=_calendar_age(dob,target)
    last_bday=_last_birthday(dob,target)
    days_since_bday=(target-last_bday).days
    days_alive=(target-dob).days
    is_fixed=birth_card in FIXED_CARDS  # semi-fixed (7D,AC,9H,2H) always findable in spread; only truly fixed (KS,JH,8C) short-circuit
    # Long Range card: septenary system (7-year periods)
    # period = age//7, planet = PLANET_LABELS[age%7] (1-indexed: Mercury=1..Neptune=7)
    # Formula confirmed by Prince 2026-09-11: get_age_spread(age//7), direct read at age%7 planet
    lr_period      = age // 7
    lr_year_planet = PLANET_LABELS[age % 7]
    lr_spread      = get_age_spread(lr_period)
    if is_fixed:
        long_range_card = birth_card
    else:
        long_range_card = read_direct(lr_spread, birth_card).get(lr_year_planet, birth_card)
    yearly_spread=get_age_spread(age)
    _ROW_DOMAIN = {
        'Mercury': 'H', 'Venus': 'H',
        'Mars':    'C', 'Jupiter': 'C',
        'Saturn':  'D', 'Uranus': 'D',
        'Neptune': 'S', 'Crown': 'S',
    }
    if is_fixed:
        yearly_direct   = {p: birth_card for p in PLANET_LABELS}
        yearly_vertical = {}
        bc_idx = yearly_spread.index(birth_card)
        moon_card        = birth_card
        pluto_card       = birth_card
        result_card      = birth_card
        environment_card = birth_card
    else:
        yearly_direct   = read_direct(yearly_spread, birth_card)
        yearly_vertical = read_vertical(yearly_spread, birth_card)
        bc_idx = yearly_spread.index(birth_card)
        moon_card        = _get_moon(yearly_spread, bc_idx)
        pluto_card       = _step_left(yearly_spread, bc_idx, 8)
        result_card      = _step_left(yearly_spread, bc_idx, 9)
        ls_home_idx      = LIFE_SPREAD.index(birth_card)
        environment_card = yearly_spread[ls_home_idx]
    period_index=min(days_since_bday//52,6)
    period_planet=PLANET_LABELS[period_index]
    days_into=days_since_bday-period_index*52
    c52d=yearly_direct.get(period_planet,birth_card)
    c52v=yearly_vertical.get(period_planet)
    weeks=days_alive//7
    wkage=weeks%90
    wkspread=get_age_spread(wkage)
    wkdirect={p:birth_card for p in PLANET_LABELS} if is_fixed else read_direct(wkspread,birth_card)
    diw=days_alive%7
    dplanet=PLANET_LABELS[diw%7]
    dcrd=wkdirect.get(dplanet,birth_card)
    # Life Spread overlay for current period
    life_spread_age = age in (0, 45, 90)
    c52d_under = get_underlying(c52d, yearly_spread) if c52d else None
    c52v_under = get_underlying(c52v, yearly_spread) if c52v else None
    c52d_spiritual_suit = get_spiritual_suit(c52d, yearly_spread) if c52d else None
    c52v_spiritual_suit = get_spiritual_suit(c52v, yearly_spread) if c52v else None

    # Yearly spread full overlay
    yearly_overlay_direct  = {p: get_underlying(yearly_direct[p],  yearly_spread)
                               for p in PLANET_LABELS if p in yearly_direct}
    yearly_overlay_vertical= {p: get_underlying(yearly_vertical[p], yearly_spread)
                               for p in PLANET_LABELS if p in yearly_vertical}

    # Build 7 period objects (direct + vertical + domain + active flag)
    periods = []
    for i, planet in enumerate(PLANET_LABELS):
        d_card  = yearly_direct.get(planet, birth_card)
        v_card  = yearly_vertical.get(planet)
        d_under = get_underlying(d_card, yearly_spread) if d_card else None
        row_ruler = (d_under or {}).get('row_ruler', 'Crown')
        domain  = _ROW_DOMAIN.get(row_ruler, 'S')
        is_active = (i == period_index)
        v_under = get_underlying(v_card, yearly_spread) if v_card else None
        p_obj = {
            'planet':            planet,
            'step':              i + 1,
            'direct':            d_card,
            'direct_underlying': d_under,
            'vertical':          v_card,
            'vertical_underlying': v_under,
            'domain':            domain,
            'active':            is_active,
        }
        if is_active:
            p_obj['days_into_period']   = days_into
            p_obj['days_remaining']     = 51 - days_into
        periods.append(p_obj)

    return {
        'birth_card':birth_card,'age':age,'fixed':is_fixed,
        'life_spread_age': life_spread_age,
        'yearly':{'spread_age':age,'direct':yearly_direct,'vertical':yearly_vertical,
                  'underlying':{'direct': yearly_overlay_direct,
                                'vertical': yearly_overlay_vertical}},
        'period_52day':{'planet':period_planet,'index':period_index,
            'days_into_period':days_into,'days_since_birthday':days_since_bday,
            'direct_card':c52d,'direct_underlying':c52d_under,
            'direct_spiritual_suit':c52d_spiritual_suit,
            'vertical_card':c52v,'vertical_underlying':c52v_under,
            'vertical_spiritual_suit':c52v_spiritual_suit},
        'weekly':{'spread_age':wkage,'direct':wkdirect},
        'daily':{'planet':dplanet,'direct_card':dcrd},
        'long_range':{'period':lr_period,'year_planet':lr_year_planet,'card':long_range_card},
        'moon_card':        moon_card,
        'pluto_card':       pluto_card,
        'result_card':      result_card,
        'environment_card': environment_card,
        'displacement_card': LIFE_SPREAD[yearly_spread.index(birth_card)],
        'periods':          periods,
        'prc':          prc_list,
        'decanate_card': dec_data,
        'event_fields':{'birth_card':birth_card,'yearly_card':yearly_direct.get('Mercury'),
            'weekly_card':c52d,'daily_card':dcrd,'long_range_card':long_range_card},
    }
