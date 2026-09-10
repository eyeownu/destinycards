# Cardology Engine

**The first open-source computational implementation of Olney Richmond's quadration mathematics for the Science of the Cards.**

The playing card deck is not random. It is a mathematical calendar: 52 cards = 52 weeks, 4 suits = 4 seasons, 13 cards per suit = 13 weeks per quarter. When arranged by a specific dealing procedure called *quadration*, the deck produces 90 unique spreads that map to years of life, weeks, and days.

This library implements the core mathematical formulas, verified against the original sources.

## What This Does

- **Solar Value Formula** — Convert any birthday to its Birth Card
- **Quadration** — The exact dealing procedure that generates all 90 age spreads
- **Displacement** — Find which card position your Birth Card occupies at any age
- **Timing** — Calculate yearly (52-day), weekly, and daily card periods

## Quick Start

```python
from cardology import CardologyEngine
from datetime import date

engine = CardologyEngine()

# Birthday to Birth Card
card = engine.birth_card(month=5, day=11)
print(card)  # '8D' (Eight of Diamonds)

# Displacement at age 42
disp = engine.displacement('8D', age=42)
print(disp)  # 'TC' (Ten of Clubs)

# Full age spread
spread = engine.age_spread(42)
print(spread)

# Weekly card age
weekly = engine.weekly_age(date(1984, 5, 11), date(2026, 9, 9))
print(weekly)  # 48
```

## The Math

### Solar Value
```
SV = 55 - (2 x month + day)
```
Maps 1-52 to cards: AH=1, 2H=2, ... KS=52. SV=0 = Joker (Dec 31).

### Quadration
A deterministic dealing procedure that produces a permutation of the 52-card deck:

1. Arrange deck in solar order (AH through KS), turn face down
2. Deal 3 at a time to 4 piles (representing the 4 seasons)
3. Stack the piles
4. Deal 1 at a time to 4 piles
5. Stack again
6. Lay into 7x7 grid + 3 Crown cards

One quadration of the Spiritual Spread (solar order) produces the Life Spread. Each subsequent quadration produces the next age spread. After 90 quadrations, every card returns to its starting position.

### The Permutation

The quadration produces a permutation with this structure:
- **1 cycle of length 45** — the moveable cards rotate through a single closed loop (the Magic Circle)
- **2 cycles of length 2** — semi-fixed pairs swap on odd quadrations
- **3 fixed points** — King of Spades, Jack of Hearts, Eight of Clubs never move

**Permutation order = LCM(45, 2, 2, 1, 1, 1) = 90**

Displacement can be computed in O(1) instead of simulating N card deals:
```
displacement = CYCLE[(birth_card_index + age) % 45]
```

## Historical Sources

- **Olney H. Richmond** (1893) — *The Mystic Test Book*
- **Robert Lee Camp** (2014) — *Cards of Your Destiny*, *Love Cards*

The quadration procedure is public domain (published 1893). This implementation is original work.

## License

MIT

## Author

[Ramazing Designs](https://ramazingdesigns.com) — Astrology, Cardology & Esoteric Science
