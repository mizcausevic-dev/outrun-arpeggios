"""Factual article draft. Not published."""

from __future__ import annotations

from tools.statements import AUDITION, ON_PICTURE, PREVIEW_LINE, PROGRAM, PUBLICATION, WARNING

TITLE = "Outrun Arpeggios is a note-only MIDI study pack"
SUBTITLE = "Eight studies of register-aware arpeggios, a matched byte check, and a simple-synth preview that is not a master"
TAGS = ["midi", "synthwave", "arpeggio", "music-production", "composition"]
TAG_LINE = "Tags: " + ", ".join(TAGS)

PARAGRAPHS = [
    "DRAFT. " + PUBLICATION,
    TAG_LINE,
    "The pack is eight arpeggio studies in 4/4. Tempos are integers from 96 to 124 BPM. Lengths were chosen first: seven studies are 16 bars and Held Peak is 8. Each study has two arpeggio variations. That is the core: sixteen files. Each study also has two harmonic references. Those sixteen files are not part of the core count, and they are not merged into the arpeggio files.",
    "A variation has to change the line. The same attacks with only a new velocity do not count. Horizon Ladder climbs in eighths and rests on beat 4. Dotted Gate uses a dotted-eighth grid. Turn and Hold keeps a long note after a short turn. Held Peak is two pickups and a note that gets louder every bar. Offbeat Shimmer never lands on the downbeat. Triplet Glow is six triplet eighths, then variation B switches to duple attacks and adds the 9th. Wide Leap is two notes and a large gap. Pair and Hold uses sixteenth pairs around a longer leap, not a bar of continuous sixteenths. Variation A attack times are different in every study.",
    "The arpeggio stays monophonic between MIDI 48 and 84, so notes inside that file do not overlap. The register moves with the chord: low at the start of a phrase, higher as the harmony changes. Source harmony is written in the harmonic reference: Am F C G, Dm Bb F C, Em C G D, Bm G D A, F#m D A E, Cm Ab Eb Bb, Gm Eb Bb F, and Fm Db Ab Eb. Horizon Ladder, Turn and Hold, Offbeat Shimmer, Wide Leap, and Pair and Hold each use a different reference voicing. They are not one chord shape moved by a constant interval. One flagged F#4 appears in Wide Leap variation B. C4 is 60. The resolution is 960 ticks per quarter note. There is no swing offset.",
    PROGRAM,
    "Chorus, filters, and slides are not in the files. The preview synth uses a short square-sine pluck for the arpeggio and a quiet sine for the chord. Velocity changes the pluck level, so the written accents remain. That mapping is documented. It is not a program change.",
    "The primary preview is study 01, Horizon Ladder, variation A, for all 16 bars at 112 BPM: the arpeggio file and harmonic reference A together. Score time is 64 quarter notes at 535714 microseconds per quarter, which is 34.286 seconds before MP3 container padding. The encoded MP3 is MP3_SECONDS seconds. The other studies are in the MIDI and are not in that audio file. "
    + PREVIEW_LINE
    + ". The film takes its audio from that preview file and shows the words "
    + ON_PICTURE
    + " on the picture and in the WebVTT captions.",
    AUDITION
    + " The validator reopened the MIDI bytes and compared them with the canonical score. That is a structural check. The sample peak written beside the preview is the peak of the integer mix. It is not LUFS and it is not a true-peak reading. Nothing in this build is claimed as a master.",
    "The stills are procedural illustrations of a sunset grid and an accent skyline. They are not photographs of a session or of performers.",
    "When a public URL exists, use either the combined arrangement or the separate parts. " + WARNING,
    "Call to action: the MIDI, the matched report, and the preview belong together. Do not publish this draft to Medium, Instagram, or X from the draft files alone.",
]


def set_measured_preview(seconds: float) -> None:
    rendered = f"{seconds:.3f}"
    for index, paragraph in enumerate(PARAGRAPHS):
        if "MP3_SECONDS" in paragraph:
            PARAGRAPHS[index] = paragraph.replace("MP3_SECONDS", rendered)


def markdown() -> str:
    body = "\n\n".join(PARAGRAPHS)
    return f"# {TITLE}\n\n{SUBTITLE}\n\n{body}\n"


def plain_text() -> str:
    lines = [TITLE, "", SUBTITLE, "", *PARAGRAPHS, ""]
    return "\n".join(lines) + "\n"
