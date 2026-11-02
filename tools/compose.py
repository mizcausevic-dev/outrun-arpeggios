"""Original outrun arpeggio studies.

Tempos, lengths, and source harmony are fixed before the notes. The arpeggio
is monophonic and is the only core part. The harmonic reference is a separate
file that holds the chord the arpeggio outlines. Offsets are 0. Nothing here
is a reconstruction of a known theme.
"""

from __future__ import annotations

from tools.midi_io import BAR_TICKS_4_4, PPQ, bpm_to_us, effective_bpm

GENERATOR_VERSION = "1.0.0"
PACK_ID = "outrun-arpeggios"
PACK_NAME = "Outrun Arpeggios"
BAR = BAR_TICKS_4_4


class Part:
    def __init__(self, study, part_id, role, variation, core, channel, slug, mono, poly, lo, hi):
        self.study = study
        self.part_id = part_id
        self.role = role
        self.variation = variation
        self.core = core
        self.channel = channel
        self.file_slug = slug
        self.monophonic = mono
        self.max_poly = poly
        self.lo = lo
        self.hi = hi
        self.container_ticks = study["bars"] * BAR
        self.notes = []

    def add(self, start, duration, pitch, velocity, departure=False):
        end = start + duration
        if start < 0 or duration <= 0 or end > self.container_ticks:
            raise ValueError(f"{self.part_id} boundary {start}+{duration}")
        if not self.lo <= pitch <= self.hi:
            raise ValueError(f"{self.part_id} pitch {pitch}")
        if not 1 <= velocity <= 127:
            raise ValueError(f"{self.part_id} velocity {velocity}")
        active = 1
        for other in self.notes:
            o0 = other["performed_start"]
            o1 = o0 + other["duration"]
            if start < o1 and o0 < end:
                if other["pitch"] == pitch or self.monophonic:
                    raise ValueError(f"{self.part_id} overlap {pitch}@{start}")
                active += 1
        if active > self.max_poly:
            raise ValueError(f"{self.part_id} poly {active}")
        self.notes.append({
            "nominal_start": start,
            "offset": 0,
            "performed_start": start,
            "duration": duration,
            "pitch": pitch,
            "velocity": velocity,
            "channel": self.channel,
            "departure": departure,
        })

    def finish(self):
        ordered = sorted(self.notes, key=lambda n: (n["performed_start"], n["pitch"]))
        if self.core and len(ordered) < 8:
            raise ValueError(f"{self.part_id} too few notes")
        if not ordered:
            raise ValueError(f"{self.part_id} empty")
        for index, note in enumerate(ordered, 1):
            note["id"] = f"{self.part_id}.n{index:04d}"
        return {
            "id": self.part_id,
            "study_id": self.study["id"],
            "slug": self.study["slug"],
            "role": self.role,
            "variation": self.variation,
            "core": self.core,
            "channel": self.channel,
            "file_slug": self.file_slug,
            "path": f"midi/{self.study['slug']}/{self.file_slug}.mid",
            "monophonic": self.monophonic,
            "max_poly": self.max_poly,
            "container_ticks": self.container_ticks,
            "container_bars": self.study["bars"],
            "bpm": self.study["bpm"],
            "tempo_us": self.study["tempo_us"],
            "notes": ordered,
        }


def arp(study, variation):
    return Part(
        study, f"{study['id']}.arp.{variation}", "arpeggio", variation, True, 0,
        f"arp-{variation}", True, 1, 48, 84,
    )


def harmony(study, variation):
    return Part(
        study, f"{study['id']}.harmony.{variation}", "harmonic-reference", variation, False, 1,
        f"harmony-{variation}", False, 4, 48, 76,
    )


def _fit(pitch):
    while pitch > 84:
        pitch -= 12
    while pitch < 48:
        pitch += 12
    return pitch


def _window(pool, bar, count):
    start = min(bar % 4, max(0, len(pool) - count))
    return pool[start:start + count]


def _region(study, bar):
    cursor = 0
    for region in study["regions"]:
        cursor += region["bars"]
        if bar < cursor:
            return region
    raise ValueError(bar)


def _velocities(study_id, variation, bar, attack, total):
    phrase = bar // 4
    boost = 0
    if study_id == "s01":
        curve = [64, 74, 86, 98, 118, 86]
        boost = phrase * 2 + (6 if phrase == 2 and attack == 4 else 0)
    elif study_id == "s02" and variation == "a":
        curve = [70, 82, 94, 116, 78]
        boost = phrase * 3
    elif study_id == "s02":
        curve = [76, 96, 84, 118]
        boost = phrase * 2
    elif study_id == "s03" and variation == "a":
        curve = [72, 80, 114, 84] if phrase in (0, 2) else [66, 76, 88, 122]
    elif study_id == "s03":
        curve = [118, 84, 74, 96] if phrase in (0, 2) else [70, 80, 108, 90]
    elif study_id == "s04" and variation == "a":
        curve = [64, 74, min(124, 86 + bar * 5)]
    elif study_id == "s04":
        curve = [min(124, 92 + bar * 4), 72, 64]
    elif study_id == "s05" and variation == "a":
        curve = [66, 76, 70, 116, 84]
        boost = (bar % 4) * 2
    elif study_id == "s05":
        curve = [120, 88, 76, 96, 70]
    elif study_id == "s06" and variation == "a":
        curve = [68, 78, 112, 86, 74, 96] if bar < 8 else [64, 74, 84, 90, 100, 122]
    elif study_id == "s06":
        curve = [72, 84, 96, 118]
    elif study_id == "s07" and variation == "a":
        curve = [62, min(124, 90 + bar * 2)]
    elif study_id == "s07":
        curve = [70, min(124, 100 + bar), 78]
    elif study_id == "s08" and variation == "a":
        curve = [70, 74, 92, 70, 76, 104 if bar < 8 else 122]
    elif study_id == "s08":
        curve = [68, 90, 118 if bar >= 8 else 100]
    else:
        raise ValueError(study_id)
    if len(curve) != total:
        raise ValueError((study_id, variation, len(curve), total))
    return max(1, min(127, curve[attack] + boost))


def _arp_pitches(study, bar, variation, count):
    region = _region(study, bar)
    pool = region["pool"]
    if study["id"] == "s01":
        group = _window(pool, bar, count)
        if variation == "b":
            if bar // 4 == 3:
                group = pool[:count]
            else:
                group = _window(pool, 3 - (bar % 4), count)
            return list(reversed(group))
        return group
    if study["id"] == "s02" and variation == "b":
        root, fifth = region["leap"]
        lift = 12 if bar % 4 >= 2 else 0
        return [_fit(pitch + lift) for pitch in (root, root + 12, fifth, fifth + 12)]
    if study["id"] == "s03" and variation == "b":
        group = _window(pool, bar, 4)
        return [group[2], group[1], group[0], group[3]]
    if study["id"] == "s04":
        row = region["rows"][bar - region["start"]]
        return list(reversed(row)) if variation == "b" else list(row)
    if study["id"] == "s05":
        root, third, fifth = region["triad"]
        if variation == "a":
            lift = 12 if bar % 4 == 2 else 0
            seq = (fifth, root, third, fifth + 12, third + 12)
        else:
            lift = 12 if bar % 4 == 0 else 0
            seq = (root + 12, fifth + 12, root, third + 12, fifth)
        return [_fit(pitch + lift) for pitch in seq]
    if study["id"] == "s06":
        root, third, fifth = region["triad"]
        lift = 12 if bar % 4 >= 2 else 0
        if variation == "a":
            seq = (root, third, fifth, root + 12, third + 12, fifth + 12)
            return [_fit(pitch + lift) for pitch in seq]
        ninth = region["ninth"]
        return [_fit(pitch) for pitch in (third + lift, fifth + lift, root + 12 + lift, ninth + lift)]
    if study["id"] == "s07":
        local = bar - region["start"]
        if variation == "a":
            return list(region["leaps"][local])
        if bar == study["bars"] - 1:
            return None
        root, third, fifth = region["triad"]
        lift = 12 if bar % 4 == 1 else 0
        return [_fit(pitch + lift) for pitch in (root, fifth, third + 12)]
    if study["id"] == "s08":
        low, mid, high = region["pair"]
        lift = 12 if bar % 4 == 2 else 0
        if variation == "a":
            return [_fit(pitch + lift) for pitch in (low, mid, high, high + 12, mid + 12, low + 12)]
        return [_fit(pitch) for pitch in (low + lift, high + 12 + lift, mid + lift)]
    return _window(pool, bar, count)


def _paint_arp(part, pattern):
    study = part.study
    for bar_index in range(study["bars"]):
        special = _arp_pitches(study, bar_index, part.variation, len(pattern))
        if special is None:
            pitches = [(53, False), (66, True), (60, False)]
        else:
            pitches = [(pitch, False) for pitch in special]
        if len(pitches) != len(pattern):
            raise ValueError(f"{part.part_id} bar {bar_index} count")
        for attack, ((offset, duration), (pitch, departure)) in enumerate(zip(pattern, pitches)):
            velocity = _velocities(study["id"], part.variation, bar_index, attack, len(pattern))
            part.add(bar_index * BAR + offset, duration, pitch, velocity, departure=departure)


def _paint_harmony(part):
    study = part.study
    for bar_index in range(study["bars"]):
        region = _region(study, bar_index)
        if part.variation == "a":
            pitches = region["close"]
            start, duration, velocity = 0, 2880, 66 + (bar_index // 4) * 4
        else:
            pitches = region["open"]
            start, duration, velocity = 960, 1920, 58 + (bar_index // 4) * 3
        for pitch in pitches:
            part.add(bar_index * BAR + start, duration, pitch, min(96, velocity))


def _build(study):
    parts = []
    for variation, pattern in (("a", study["pattern_a"]), ("b", study["pattern_b"])):
        line = arp(study, variation)
        _paint_arp(line, pattern)
        chord = harmony(study, variation)
        _paint_harmony(chord)
        parts.extend((line, chord))
    return parts


def _patterns():
    return {
        "s01": ([(0, 400), (480, 400), (960, 400), (1440, 400), (1920, 400), (2400, 400)],
                [(240, 360), (720, 360), (1200, 700), (1920, 360), (2400, 360), (2880, 700)]),
        "s02": ([(0, 600), (720, 600), (1440, 600), (2160, 600), (2880, 600)],
                [(0, 800), (960, 800), (1920, 400), (2400, 800)]),
        "s03": ([(0, 900), (960, 400), (1440, 400), (2400, 1200)],
                [(0, 400), (480, 400), (1440, 900), (2880, 700)]),
        "s04": ([(0, 420), (480, 420), (960, 1680)],
                [(0, 1680), (1920, 420), (2640, 420)]),
        "s05": ([(240, 200), (720, 440), (1680, 200), (2160, 680), (3120, 400)],
                [(0, 700), (960, 400), (1440, 400), (2400, 900), (3360, 300)]),
        "s06": ([(0, 520), (640, 520), (1280, 520), (1920, 520), (2560, 520), (3200, 520)],
                [(0, 800), (960, 400), (1920, 800), (2880, 700)]),
        "s07": ([(480, 900), (1920, 1400)],
                [(0, 600), (1440, 600), (2880, 700)]),
        "s08": ([(0, 180), (240, 180), (960, 800), (1920, 180), (2160, 180), (2880, 700)],
                [(480, 1000), (1680, 480), (2400, 1000)]),
    }


def _region_row(name, bars, close, open_, pool=None, leap=None, triad=None, ninth=None, rows=None, pair=None, leaps=None):
    pcs = sorted({pitch % 12 for pitch in close})
    return {
        "name": name,
        "bars": bars,
        "pcs": pcs,
        "close": close,
        "open": open_,
        "pool": pool or [],
        "leap": leap,
        "triad": triad,
        "ninth": ninth,
        "rows": rows,
        "pair": pair,
        "leaps": leaps,
    }


def studies():
    patterns = _patterns()
    rows = [
        {
            "id": "s01", "slug": "s01-horizon-ladder", "title": "Horizon Ladder", "bpm": 112, "bars": 16,
            "tonic": "A", "tonal_reference": "A", "collection_name": "A natural minor",
            "pitch_classes": [0, 2, 4, 5, 7, 9, 11], "seed": 11201,
            "rhythm_a": "six eighths climbing from the downbeat, with a gap before each attack and a rest through beat 4",
            "rhythm_b": "the same six tones in reverse, entering on the second 16th and holding across the middle of the bar",
            "accent": "Velocity climbs inside the bar and peaks on the fifth attack. Phrase 3 adds another step to that peak.",
            "color_pcs": [],
            "regions": [
                _region_row("Am", 4, [57, 60, 64], [57, 64, 72], pool=[52, 57, 60, 64, 69, 72, 76, 81]),
                _region_row("F", 4, [53, 57, 60], [53, 60, 69], pool=[53, 57, 60, 65, 69, 72, 77, 81]),
                _region_row("C", 4, [60, 64, 67], [48, 67, 76], pool=[55, 60, 64, 67, 72, 76, 79, 84]),
                _region_row("G", 4, [55, 59, 62], [55, 62, 71], pool=[50, 55, 59, 62, 67, 71, 74, 79]),
            ],
        },
        {
            "id": "s02", "slug": "s02-dotted-gate", "title": "Dotted Gate", "bpm": 104, "bars": 16,
            "tonic": "D", "tonal_reference": "D", "collection_name": "D natural minor",
            "pitch_classes": [0, 2, 4, 5, 7, 9, 10], "seed": 10402,
            "rhythm_a": "five attacks on a dotted-eighth grid, each shorter than the grid so the notes do not touch",
            "rhythm_b": "four attacks: two quarters, a short answer, and a quarter, leaping octaves instead of climbing",
            "accent": "The fourth dotted attack is the loud one. Each four-bar phrase raises that accent.",
            "color_pcs": [],
            "regions": [
                _region_row("Dm", 4, [50, 53, 57], [50, 57, 65], pool=[50, 53, 57, 62, 65, 69, 74, 77], leap=(50, 57)),
                _region_row("Bb", 4, [58, 62, 65], [58, 65, 70], pool=[58, 62, 65, 70, 74, 77, 82], leap=(58, 65)),
                _region_row("F", 4, [53, 57, 60], [53, 60, 69], pool=[53, 57, 60, 65, 69, 72, 77, 81], leap=(53, 60)),
                _region_row("C", 4, [48, 52, 55], [48, 55, 64], pool=[48, 52, 55, 60, 64, 67, 72, 76], leap=(48, 55)),
            ],
        },
        {
            "id": "s03", "slug": "s03-turn-and-hold", "title": "Turn and Hold", "bpm": 120, "bars": 16,
            "tonic": "E", "tonal_reference": "E", "collection_name": "E natural minor",
            "pitch_classes": [0, 2, 4, 6, 7, 9, 11], "seed": 12003,
            "rhythm_a": "a long downbeat, two short turns, then a held note through beat 4",
            "rhythm_b": "the turn moves to the front of the bar and the held note moves to beat 4",
            "accent": "In phrases 1 and 3 the short turn is loudest. In phrases 2 and 4 the held note is loudest.",
            "color_pcs": [],
            "regions": [
                _region_row("Em", 4, [52, 55, 59], [52, 59, 67], pool=[52, 55, 59, 64, 67, 71, 76, 83]),
                _region_row("C", 4, [48, 52, 55], [48, 55, 64], pool=[48, 52, 55, 60, 64, 67, 72, 76, 79, 84]),
                _region_row("G", 4, [55, 59, 62], [55, 62, 71], pool=[55, 59, 62, 67, 71, 74, 79]),
                _region_row("D", 4, [50, 54, 57], [50, 57, 66], pool=[50, 54, 57, 62, 66, 69, 74, 81]),
            ],
        },
        {
            "id": "s04", "slug": "s04-held-peak", "title": "Held Peak", "bpm": 100, "bars": 8,
            "tonic": "B", "tonal_reference": "B", "collection_name": "B natural minor",
            "pitch_classes": [1, 2, 4, 6, 7, 9, 11], "seed": 10004,
            "rhythm_a": "two short pickups and one held peak, then silence for the rest of the bar",
            "rhythm_b": "the held peak moves onto the downbeat and the pickups answer after beat 3",
            "accent": "The held note gets louder on every bar. Variation B puts that growing accent on beat 1.",
            "color_pcs": [],
            "regions": [
                _region_row("Bm", 2, [59, 62, 66], [59, 66, 71], rows=([59, 62, 71], [62, 66, 78])),
                _region_row("G", 2, [55, 59, 62], [55, 62, 71], rows=([55, 59, 67], [59, 62, 74])),
                _region_row("D", 2, [50, 54, 57], [50, 57, 66], rows=([50, 54, 62], [54, 57, 69])),
                _region_row("A", 2, [57, 61, 64], [57, 64, 73], rows=([57, 61, 69], [61, 64, 76])),
            ],
        },
        {
            "id": "s05", "slug": "s05-offbeat-shimmer", "title": "Offbeat Shimmer", "bpm": 124, "bars": 16,
            "tonic": "F#", "tonal_reference": "F#", "collection_name": "F# natural minor",
            "pitch_classes": [1, 2, 4, 6, 8, 9, 11], "seed": 12405,
            "rhythm_a": "five offbeat attacks. The downbeat is empty. The longest note sits after beat 3",
            "rhythm_b": "five on-beat attacks, with octave leaps and a short last 16th",
            "accent": "The long offbeat after beat 3 is the peak in variation A. Variation B accents the opening octave.",
            "color_pcs": [],
            "regions": [
                _region_row("F#m", 4, [54, 57, 61], [54, 61, 69], triad=(54, 57, 61)),
                _region_row("D", 4, [50, 54, 57], [50, 57, 66], triad=(50, 54, 57)),
                _region_row("A", 4, [57, 61, 64], [57, 64, 73], triad=(57, 61, 64)),
                _region_row("E", 4, [52, 56, 59], [52, 59, 68], triad=(52, 56, 59)),
            ],
        },
        {
            "id": "s06", "slug": "s06-triplet-glow", "title": "Triplet Glow", "bpm": 108, "bars": 16,
            "tonic": "C", "tonal_reference": "C", "collection_name": "C natural minor",
            "pitch_classes": [0, 2, 3, 5, 7, 8, 10], "seed": 10806,
            "rhythm_a": "six triplet eighths with a short gap inside each triplet, not a sixteenth grid",
            "rhythm_b": "four duple attacks. The last of them is the 9th above the same triad",
            "accent": "For eight bars the accent sits on the third triplet. After that it moves to the last triplet.",
            "color_pcs": [2, 10, 5, 0],
            "regions": [
                _region_row("Cm", 4, [48, 51, 55], [48, 55, 63], triad=(48, 51, 55), ninth=62),
                _region_row("Ab", 4, [56, 60, 63], [56, 63, 72], triad=(56, 60, 63), ninth=70),
                _region_row("Eb", 4, [51, 55, 58], [51, 58, 67], triad=(51, 55, 58), ninth=65),
                _region_row("Bb", 4, [58, 62, 65], [58, 65, 74], triad=(58, 62, 65), ninth=72),
            ],
        },
        {
            "id": "s07", "slug": "s07-wide-leap", "title": "Wide Leap", "bpm": 96, "bars": 16,
            "tonic": "G", "tonal_reference": "G", "collection_name": "G natural minor",
            "pitch_classes": [0, 2, 3, 5, 7, 9, 10], "seed": 9607,
            "rhythm_a": "two notes per bar, after the downbeat and on beat 3, with a long gap between them",
            "rhythm_b": "three notes that start on the downbeat variation A left empty",
            "accent": "The upper leap grows louder across all 16 bars. The lower note stays quiet.",
            "color_pcs": [],
            "departures": ["Variation B bar 16 uses F#4 (66) once, between F3 and C4, under the F chord. It is flagged."],
            "regions": [
                _region_row("Gm", 4, [55, 58, 62], [55, 62, 70], triad=(55, 58, 62),
                            leaps=((55, 67), (55, 74), (55, 79), (55, 62))),
                _region_row("Eb", 4, [51, 55, 58], [51, 58, 67], triad=(51, 55, 58),
                            leaps=((51, 70), (51, 75), (63, 82), (51, 67))),
                _region_row("Bb", 4, [58, 62, 65], [58, 65, 74], triad=(58, 62, 65),
                            leaps=((58, 70), (58, 77), (58, 82), (58, 65))),
                _region_row("F", 4, [53, 57, 60], [53, 60, 69], triad=(53, 57, 60),
                            leaps=((53, 65), (53, 72), (53, 77), (53, 60))),
            ],
        },
        {
            "id": "s08", "slug": "s08-pair-and-hold", "title": "Pair and Hold", "bpm": 118, "bars": 16,
            "tonic": "F", "tonal_reference": "F", "collection_name": "F natural minor",
            "pitch_classes": [0, 1, 3, 5, 7, 8, 10], "seed": 11808,
            "rhythm_a": "a pair of sixteenths, a longer leap, another sixteenth pair, then a hold. The bar is not a continuous sixteenth line",
            "rhythm_b": "three notes only: a late pickup, a short leap, and a hold. The sixteenth pairs are gone",
            "accent": "The sixteenth pairs stay soft. The final hold is louder in the second half of the study.",
            "color_pcs": [],
            "regions": [
                _region_row("Fm", 4, [53, 56, 60], [53, 60, 68], pair=(53, 56, 60)),
                _region_row("Db", 4, [49, 53, 56], [49, 56, 65], pair=(49, 53, 56)),
                _region_row("Ab", 4, [56, 60, 63], [56, 63, 72], pair=(56, 60, 63)),
                _region_row("Eb", 4, [51, 55, 58], [51, 58, 67], pair=(51, 55, 58)),
            ],
        },
    ]
    phrases_16 = [
        ({"name": "Climb", "start_bar": 0, "bars": 4}, {"name": "Lift", "start_bar": 4, "bars": 4},
         {"name": "Crest", "start_bar": 8, "bars": 4}, {"name": "Cadence", "start_bar": 12, "bars": 4}),
        ({"name": "Gate", "start_bar": 0, "bars": 4}, {"name": "Answer", "start_bar": 4, "bars": 4},
         {"name": "Octave", "start_bar": 8, "bars": 4}, {"name": "Land", "start_bar": 12, "bars": 4}),
        ({"name": "Plate", "start_bar": 0, "bars": 4}, {"name": "Turn", "start_bar": 4, "bars": 4},
         {"name": "Rise", "start_bar": 8, "bars": 4}, {"name": "Hold", "start_bar": 12, "bars": 4}),
        None,
        ({"name": "Shimmer", "start_bar": 0, "bars": 4}, {"name": "Push", "start_bar": 4, "bars": 4},
         {"name": "High", "start_bar": 8, "bars": 4}, {"name": "Fold", "start_bar": 12, "bars": 4}),
        ({"name": "Glow", "start_bar": 0, "bars": 4}, {"name": "Cycle", "start_bar": 4, "bars": 4},
         {"name": "Color", "start_bar": 8, "bars": 4}, {"name": "Resolve", "start_bar": 12, "bars": 4}),
        ({"name": "Leap", "start_bar": 0, "bars": 4}, {"name": "Span", "start_bar": 4, "bars": 4},
         {"name": "Wide", "start_bar": 8, "bars": 4}, {"name": "Close", "start_bar": 12, "bars": 4}),
        ({"name": "Pair", "start_bar": 0, "bars": 4}, {"name": "Answer", "start_bar": 4, "bars": 4},
         {"name": "Lift", "start_bar": 8, "bars": 4}, {"name": "Hold", "start_bar": 12, "bars": 4}),
    ]
    phrase_8 = (
        {"name": "Bloom", "start_bar": 0, "bars": 2},
        {"name": "Open", "start_bar": 2, "bars": 2},
        {"name": "Leap", "start_bar": 4, "bars": 2},
        {"name": "Peak", "start_bar": 6, "bars": 2},
    )
    for index, row in enumerate(rows):
        if not 95 <= row["bpm"] <= 125:
            raise ValueError(row["bpm"])
        pattern_a, pattern_b = patterns[row["id"]]
        row["pattern_a"] = pattern_a
        row["pattern_b"] = pattern_b
        cursor = 0
        for region in row["regions"]:
            region["start"] = cursor
            cursor += region["bars"]
        if cursor != row["bars"]:
            raise ValueError(row["id"])
        row["changes"] = [region["name"] for region in row["regions"]]
        row["change_bars"] = [region["bars"] for region in row["regions"]]
        row["phrases"] = list(phrase_8 if row["bars"] == 8 else phrases_16[index])
        names = ", ".join(row["changes"])
        row["harmonic_rhythm"] = f"Source harmony: {names}. Each chord lasts {row['change_bars'][0]} bars."
        row["source_harmony"] = (
            f"The harmonic reference holds {names} as written triads. "
            "It is a separate file and it is not part of the core count."
        )
        row["identity"] = (
            f"{row['title']} moves through {names}. Variation A is {row['rhythm_a']}. "
            f"The register shifts with each chord. Variation B is {row['rhythm_b']}."
        )
        row["limitations"] = (
            "Pair arpeggio A with harmonic reference A, and B with B. "
            "The arpeggio is monophonic and leaves gaps, so notes inside that file do not overlap. "
            "Variation A of the reference sounds for three beats and rests on beat 4. "
            "Variation B of the reference enters on beat 2. The arrangement is only study 01."
        )
        row["voicing"] = row["source_harmony"]
        row["layering"] = (
            "One arpeggio channel. The chord is the harmonic reference on its own channel and in its own file. "
            "Do not merge the two files into one part."
        )
        row.setdefault("departures", [])
        row["meter"] = "4/4"
        row["bar_ticks"] = BAR
        row["ppq"] = PPQ
        row["stochastic_draws"] = 0
        row["tempo_us"] = bpm_to_us(row["bpm"])
        row["effective_bpm"] = effective_bpm(row["tempo_us"])
        if sum(item["bars"] for item in row["phrases"]) != row["bars"]:
            raise ValueError(row["id"] + " phrases")
    return rows


def _sig(notes):
    return tuple((note["performed_start"], note["pitch"], note["duration"]) for note in notes)


def _attack_tuples(notes):
    return tuple(sorted({(note["performed_start"] % BAR, note["duration"]) for note in notes}))


def _continuous_sixteenths(notes, bars):
    template = tuple(step * 240 for step in range(16))
    grouped = [[] for _ in range(bars)]
    for note in notes:
        grouped[note["performed_start"] // BAR].append(note["performed_start"] % BAR)
    return all(tuple(sorted(group)) == template for group in grouped)


def assert_music(catalog_studies, parts):
    allowed = {study["id"]: set(study["pitch_classes"]) for study in catalog_studies}
    by_study = {study["id"]: study for study in catalog_studies}
    for part in parts:
        study = by_study[part["study_id"]]
        pool = allowed[part["study_id"]]
        for note in part["notes"]:
            inside = (note["pitch"] % 12) in pool
            if note["departure"] and inside:
                raise ValueError(f"{part['id']} departure {note['pitch']} is inside the collection")
            if not note["departure"] and not inside:
                raise ValueError(f"{part['id']} note {note['pitch']} left the collection")
            region = _region(study, note["performed_start"] // BAR)
            pc = note["pitch"] % 12
            if part["role"] == "harmonic-reference" and pc not in region["pcs"]:
                raise ValueError(f"{part['id']} reference {note['pitch']} is outside {region['name']}")
            if part["role"] == "arpeggio" and not note["departure"] and pc not in region["pcs"]:
                if not (part["variation"] == "b" and pc in study["color_pcs"]):
                    raise ValueError(f"{part['id']} arp {note['pitch']} does not outline {region['name']}")
    arps = [part for part in parts if part["role"] == "arpeggio"]
    grouped = {}
    for part in arps:
        grouped.setdefault(part["study_id"], {})[part["variation"]] = part
    tuples = {}
    report = []
    for study_id, variations in grouped.items():
        left, right = variations["a"], variations["b"]
        if _sig(left["notes"]) == _sig(right["notes"]):
            raise ValueError(f"{study_id} variations match")
        signature = _attack_tuples(left["notes"])
        if signature in tuples:
            raise ValueError(f"{study_id} variation A attack tuples repeat {tuples[signature]}")
        tuples[signature] = study_id
        if _continuous_sixteenths(left["notes"], left["container_bars"]):
            raise ValueError(f"{study_id} is a continuous sixteenth template")
        pitches = [note["pitch"] for note in left["notes"]]
        velocities = [note["velocity"] for note in left["notes"]]
        if max(pitches) - min(pitches) < 12:
            raise ValueError(f"{study_id} register span")
        if max(velocities) - min(velocities) < 24:
            raise ValueError(f"{study_id} accent span")
        report.append({
            "study_id": study_id,
            "attack_tuples": [{"offset": offset, "duration": duration} for offset, duration in signature],
            "a": len(left["notes"]),
            "b": len(right["notes"]),
            "register": [min(pitches), max(pitches)],
            "velocity": [min(velocities), max(velocities)],
        })
    if len(tuples) != 8:
        raise ValueError("variation A attack tuples are not eight distinct patterns")
    return {
        "studies": report,
        "method": "Variation A attack-time tuples differ across the eight studies. No study uses a continuous sixteenth-note template. Variation B changes rhythm and contour, not only velocity.",
    }


def compose():
    catalog_studies = studies()
    parts = []
    for study in catalog_studies:
        for part in _build(study):
            parts.append(part.finish())
    identity = assert_music(catalog_studies, parts)
    core = [part for part in parts if part["core"]]
    refs = [part for part in parts if not part["core"]]
    if len(core) != 16 or len(refs) != 16:
        raise ValueError((len(core), len(refs)))
    preview = next(study for study in catalog_studies if study["id"] == "s01")
    arrangement = {
        "id": "arrangement-preview-s01a",
        "path": "midi/arrangement.mid",
        "format": 1,
        "container_ticks": preview["bars"] * BAR,
        "bpm": preview["bpm"],
        "tempo_us": preview["tempo_us"],
        "meter": "4/4",
        "description": "Study 01 variation A arpeggio with harmonic reference A. The chord is not inside the arpeggio file.",
        "tracks": [
            {"name": "Conductor", "source_part": None, "channel": None},
            {"name": "Arpeggio", "source_part": "s01.arp.a", "channel": 0},
            {"name": "Harmonic Reference", "source_part": "s01.harmony.a", "channel": 1},
        ],
    }
    catalog = {
        "pack_id": PACK_ID,
        "pack_name": PACK_NAME,
        "catalog_version": GENERATOR_VERSION,
        "generator_version": GENERATOR_VERSION,
        "ppq": PPQ,
        "meter": {"numerator": 4, "denominator": 4, "bar_ticks": BAR},
        "pitched_range": [48, 84],
        "c4": 60,
        "note_policy": "note-only MIDI. Filters, chorus, and slides are not encoded.",
        "microtiming": "offset is 0; performed_start = nominal_start",
        "stochastic_draws": 0,
        "seed_meaning": "Seeds identify studies. Nothing is random.",
        "core_part_count": len(core),
        "reference_part_count": len(refs),
        "range_statement": "Arpeggios are monophonic, MIDI 48 to 84. Harmonic references use MIDI 48 to 76, at most four notes, and are not part of the core count. C4 is 60.",
        "studies": [{
            key: study[key] for key in (
                "id", "slug", "title", "bpm", "tempo_us", "effective_bpm", "bars", "meter", "bar_ticks",
                "tonic", "tonal_reference", "collection_name", "pitch_classes", "departures", "seed",
                "harmonic_rhythm", "source_harmony", "changes", "change_bars", "phrases", "identity",
                "limitations", "voicing", "layering", "accent", "rhythm_a", "rhythm_b", "stochastic_draws",
            )
        } for study in catalog_studies],
        "parts": [{
            "id": part["id"], "study_id": part["study_id"], "role": part["role"], "variation": part["variation"],
            "core": part["core"], "channel": part["channel"], "path": part["path"], "notes": len(part["notes"]),
            "container_bars": part["container_bars"], "bpm": part["bpm"], "monophonic": part["monophonic"],
        } for part in parts],
        "arrangement": arrangement,
        "preview_part_ids": ["s01.arp.a", "s01.harmony.a"],
        "stack_warning": "Use either the combined arrangement or the separate parts. Do not stack the part files on top of the combined file.",
    }
    score = {
        "pack_id": PACK_ID,
        "generator_version": GENERATOR_VERSION,
        "ppq": PPQ,
        "parts": parts,
        "arrangement": arrangement,
        "identity_check": identity,
    }
    return {"catalog": catalog, "score": score}
