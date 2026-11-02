"""Build the Outrun Arpeggios pack in the required order."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.article import TITLE, markdown, plain_text, set_measured_preview  # noqa: E402
from tools.audit import run_audit  # noqa: E402
from tools.compose import GENERATOR_VERSION, compose  # noqa: E402
from tools.page import write_page  # noqa: E402
from tools.render_audio import RENDERER_VERSION, render_preview  # noqa: E402
from tools.render_visual import (  # noqa: E402
    derive_social,
    draw_disclosure,
    encode_film,
    encode_mp3,
    paint,
    ppm_to_jpeg,
    write_ppm,
)
from tools.statements import (  # noqa: E402
    AUDITION,
    ON_PICTURE,
    PREVIEW_LINE,
    PROGRAM,
    PUBLICATION,
    WARNING,
)
from tools.validate import dump_json, validate_tree, write_midi_files  # noqa: E402

def x_body(seconds: float) -> str:
    body = (
        f"Outrun Arpeggios: 8 studies, 96-124 BPM, note-only MIDI. "
        f"Study 01 is {seconds:.3f}s. {PREVIEW_LINE}. {AUDITION}"
    )
    if len(body) > 280 or "DRAFT" in body or AUDITION not in body or PREVIEW_LINE not in body:
        raise RuntimeError(f"X body is {len(body)} characters")
    return body


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(path: Path) -> dict:
    completed = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,sample_rate,channels",
            "-of", "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    streams = payload.get("streams", [])
    return {
        "duration": float(payload["format"]["duration"]),
        "video": any(stream.get("codec_type") == "video" for stream in streams),
        "audio": any(stream.get("codec_type") == "audio" for stream in streams),
        "streams": streams,
    }


def vtt_time(seconds: float) -> str:
    millis = int(math.floor(seconds * 1000 + 1e-9))
    if millis / 1000 > seconds:
        millis -= 1
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def write_readme(catalog: dict, preview: dict, film: dict) -> None:
    study_lines = "\n".join(
        f"- {study['id']} {study['title']}: {study['bpm']} BPM, {study['bars']} bars, {study['collection_name']}, tonic reference {study['tonal_reference']}. Source harmony {', '.join(study['changes'])}."
        for study in catalog["studies"]
    )
    text = f"""# Outrun Arpeggios

Original note-only MIDI studies of register-aware arpeggios. Eight studies, two variations of the arpeggio. Accents change across the phrase, and the register follows the chord. Harmonic references are cataloged separately and are not part of the core count. They are not merged into the arpeggio files.

This repository is the pack. {PUBLICATION}

## What you can open

- `index.html` is the file catalog. The arpeggio lane is drawn from the arpeggio MIDI. The chord panel is drawn from the harmonic reference MIDI.
- `media.html` is the stills page. The film sits under the pictures.
- `midi/arrangement.mid` is a Format 1 preview arrangement of study 01, variation A: arpeggio and harmonic reference.
- Individual Format 0 parts live under `midi/`.
- `midi/validation-Cursor.json` is the report from reopening those exact bytes.
- `preview/preview.mp3` is the primary music preview. It is {preview['seconds_encoded']:.3f} seconds in the encoded file. {PREVIEW_LINE}.
- `film/preview.mp4` and `film/preview.vtt` are the film. On-picture and caption text is `{ON_PICTURE}`.
- `art/hero.jpg` is a 1280x720 illustration. `art/square.jpg` is 1080x1080. Neither is a photograph.

{WARNING}

## Studies

{study_lines}

Core files: {catalog['core_part_count']}. Reference files: {catalog['reference_part_count']}.

{catalog['range_statement']} C4 is 60. PPQ is 960. Meter is 4/4. Offsets are 0. Seeds identify studies and are not random draws. Generator {GENERATOR_VERSION}. Source harmony, register, and accent contour are written on each study. Variation A attack-time tuples differ across the eight studies. No study is a continuous sixteenth-note line.

## Preview path

The preview renders the canonical notes for `s01.arp.a` and `s01.harmony.a` with `{RENDERER_VERSION}`. Tempo authority is the encoded microsecond value in the MIDI, {catalog['arrangement']['tempo_us']} us per quarter note. Sample positions use `floor(seconds * 44100 + 0.5)` from tick 0. Intervals are not summed. Sample-exact repeating loops at an arbitrary BPM are not promised.

The synth mapping is a short square-sine pluck for the arpeggio and a quiet sine for the chord. simple-synth is the renderer name in `{RENDERER_VERSION}`. {PROGRAM} The mapping is not encoded in the MIDI.

Encoded MP3 settings: libmp3lame, 192 kbps. Film audio is AAC at 160 kbps re-encoded from that MP3, so the decoded film audio is not byte-identical to the MP3. Film duration probe: {film['duration_seconds']:.3f} seconds. {film['duration_relation']} The picture is a still illustration with rasterized disclosure text. DejaVu Sans Bold from the build machine supplies the glyphs. The font file is not in this pack.

{AUDITION} A sample peak is recorded in the preview manifest. It is not LUFS and it is not a true peak.

## Build

From the repository root, with Python 3.11+ and ffmpeg (libmp3lame, aac, libx264):

```bash
python3 tools/build_pack.py
python3 -m http.server 43161
```

The page is static. It is served with Python's HTTP server so the MIDI and media keep working relative paths. There is no application server and no package install. Standard library only.

`build/` holds the intermediate WAV, the procedural PPM, and the film plate. Those files are gitignored. The delivered audio is the MP3.

## Checks the validator actually runs

File existence, parse, PPQ, tempo, 4/4, end-of-track boundary, note pairing, ranges, monophonic arpeggio, harmonic reference polyphony cap of four, note-off before note-on at a shared tick, absence of program changes and other channel messages, departure flags against the declared pitch-class set, agreement with the canonical score, and agreement between `arrangement.mid` and the two source files. A negative overlap fixture is written outside the pack and must be rejected.

## Drafts and publication

Social captions, the X post, and the Medium article are drafts. They are not access controls. If this repository is public, the drafts are public. Do not treat them as posted to Instagram, X, or Medium.

Prepared repository description: Original note-only MIDI studies of outrun arpeggios, with matched validation and a simple-synth preview.

Prepared topics: midi, synthwave, arpeggio, music-production, composition.

No release tag was created. `index.html` keeps its name because players and links depend on it. This page is the file catalog the pack requires.

## Limitations

Variation compatibility is per study and is written on the page. Variation A and variation B of a study are alternatives. Pair harmonic reference A with arpeggio A, and reference B with arpeggio B. The arrangement is only study 01. Stacking it with the part files doubles those notes. These lines are original. They are not reconstructions of known themes.
"""
    (ROOT / "README.md").write_text(text, encoding="utf-8")


def write_identity(catalog: dict) -> None:
    lines = [
        "# Study identity",
        "",
        "Container lengths, tempos, and collections were fixed before note generation. No stochastic draws.",
        "",
    ]
    for study in catalog["studies"]:
        lines.append(f"## {study['id']} {study['title']}")
        lines.append("")
        lines.append(study["identity"])
        lines.append("")
        lines.append(f"Limitations: {study['limitations']}")
        lines.append("")
    (ROOT / "score" / "identity-Cursor.md").write_text("\n".join(lines), encoding="utf-8")


def write_social(seconds: float) -> None:
    ig = ROOT / "social" / "instagram-Cursor"
    xdir = ROOT / "social" / "x-Cursor"
    ig.mkdir(parents=True, exist_ok=True)
    xdir.mkdir(parents=True, exist_ok=True)
    caption = f"""DRAFT
This file is a draft. It has not been posted.

Caption

Outrun Arpeggios. Eight studies, 96-124 BPM, two arpeggio variations each. Harmonic references are separate files, and their voicings are not one transposed shape. The study 01 preview is {seconds:.3f} seconds. {PREVIEW_LINE}. {AUDITION}

Hashtags

#midi #synthwave #arpeggio #musicproduction #composition

Alt text, 1080x1080

Illustration of a sunset grid and a skyline of accent bars. Not a photograph of a studio or of performers.

Alt text, 1080x1350

Illustration of the same sunset grid, cropped from the square still and reframed as a vertical 1080 by 1350 image. Not a photograph of a studio or of performers.
"""
    (ig / "captions-Cursor.md").write_text(caption, encoding="utf-8")
    body = x_body(seconds)
    post = f"DRAFT\nThis label is not the post body.\n\nPOST BODY\n{body}\n"
    if "DRAFT" in body:
        raise RuntimeError("DRAFT leaked into the X body")
    (xdir / "post-Cursor.txt").write_text(post, encoding="utf-8")
    (xdir / "alt-text-Cursor.txt").write_text(
        "Illustration of a sunset grid and accent skyline, resized from the 1280 by 720 still. Not a photograph of a studio or of performers.\n",
        encoding="utf-8",
    )


def write_publication_plan(preview: dict) -> None:
    text = f"""# Publication plan

Status: not published.

{PUBLICATION}

## What is local

The MIDI, matched validation report, MP3 ({preview['seconds_encoded']:.3f} s), MP4, VTT, raster stills, drafts, page, and README are in this working tree. Draft labels do not hide files. A public remote would make the drafts public.

## What was not done

The public repository is https://github.com/mizcausevic-dev/outrun-arpeggios . No description or topics were applied by this build. No release tag was created. Nothing was posted to Medium, Instagram, or X. The catalog address is the GitHub Pages URL in the publication line. Treat that address as live only after it responds.

## Prepared metadata

Description: Original note-only MIDI studies of outrun arpeggios, with matched validation and a simple-synth preview.

Topics: midi, synthwave, arpeggio, music-production, composition.

`index.html` is the Pages entry. `media.html` is the stills page.

## Security note for a later deploy

The page is static. It has no form, no account system, and no secret. It links to MIDI and media in the same tree. A later deploy should not add a checkout or a lead form without a separate privacy review.
"""
    path = ROOT / "docs" / "publication-plan-Cursor.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    data = compose()
    dump_json(ROOT / "catalog" / "catalog-Cursor.json", data["catalog"])
    dump_json(ROOT / "score" / "canonical-score-Cursor.json", data["score"])
    write_midi_files(ROOT, data["score"])
    report = validate_tree(ROOT)
    if report["result"] != "PASS":
        dump_json(ROOT / "midi" / "validation-Cursor.json", report)
        raise SystemExit("MIDI validation failed:\n" + "\n".join(report["errors"]))
    dump_json(ROOT / "midi" / "validation-Cursor.json", report)

    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    ids = data["catalog"]["preview_part_ids"]
    parts = [next(part for part in data["score"]["parts"] if part["id"] == part_id) for part_id in ids]
    arrangement = data["score"]["arrangement"]
    wav_path = build / "preview.wav"
    audio_info = render_preview(parts, arrangement["tempo_us"], arrangement["container_ticks"], wav_path)
    mp3_path = ROOT / "preview" / "preview.mp3"
    mp3_cmd = encode_mp3(wav_path, mp3_path)
    mp3_probe = probe(mp3_path)

    by_path = {record["path"]: record for record in report["files"]}
    source_files = []
    for part in parts:
        record = by_path[part["path"]]
        source_files.append({"path": part["path"], "sha256": record["sha256"], "id": part["id"]})
    manifest = {
        "pack_id": data["catalog"]["pack_id"],
        "renderer": RENDERER_VERSION,
        "renderer_note": audio_info["mapping_note"],
        "mapping": audio_info["mapping"],
        "source_parts": source_files,
        "arrangement_path": arrangement["path"],
        "arrangement_sha256": report["arrangement"]["sha256"],
        "score_sha256": report["score_sha256"],
        "excerpt": {
            "study": "s01",
            "bars": "1-16, the full container",
            "start_tick": 0,
            "end_tick": arrangement["container_ticks"],
            "transposition": "none",
            "sequencing": "arpeggio and harmonic reference, variation A, for the full 16 bars. The reference is cataloged and is not merged into the arpeggio file.",
        },
        "tempo_us": arrangement["tempo_us"],
        "tempo_authority": "encoded MIDI tempo",
        "score_seconds": audio_info["seconds"],
        "rounding": audio_info["rounding"],
        "sample_peak": audio_info["sample_peak"],
        "sample_peak_dbfs": audio_info["sample_peak_dbfs"],
        "sample_peak_note": audio_info["sample_peak_note"],
        "intermediate_wav": "build/preview.wav",
        "intermediate_wav_sha256": sha256_file(wav_path),
        "intermediate_wav_note": "The WAV is gitignored build storage. The delivered preview is the MP3.",
        "mp3_path": "preview/preview.mp3",
        "mp3_sha256": sha256_file(mp3_path),
        "mp3_encode_command": mp3_cmd,
        "seconds_encoded": mp3_probe["duration"],
        "encode": "libmp3lame CBR 192 kbps, mono source",
        "program_changes": PROGRAM,
        "listening": AUDITION,
        "label": PREVIEW_LINE,
    }
    manifest_path = ROOT / "preview" / "preview-manifest-Cursor.txt"
    manifest_path.write_text(PREVIEW_LINE + "\n" + json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    wide = paint(1280, 720, "wide")
    plate_ppm = build / "plate.ppm"
    write_ppm(plate_ppm, 1280, 720, wide)
    plate_jpg = build / "plate.jpg"
    ppm_to_jpeg(plate_ppm, plate_jpg)
    textfile = build / "onpicture.txt"
    film_cmd = encode_film(plate_jpg, mp3_path, ROOT / "film" / "preview.mp4", textfile, f"{mp3_probe['duration']:.6f}")
    mp4_probe = probe(ROOT / "film" / "preview.mp4")
    vtt_end = vtt_time(mp4_probe["duration"])
    vtt = f"WEBVTT\n\n00:00:00.000 --> {vtt_end}\n{ON_PICTURE}\n"
    (ROOT / "film" / "preview.vtt").write_text(vtt, encoding="utf-8")

    ppm_to_jpeg(plate_ppm, ROOT / "art" / "hero.jpg")
    square_rgb = paint(1080, 1080, "square")
    square_ppm = build / "square.ppm"
    write_ppm(square_ppm, 1080, 1080, square_rgb)
    ppm_to_jpeg(square_ppm, ROOT / "art" / "square.jpg")
    poster_cmd = draw_disclosure(ROOT / "art" / "hero.jpg", ROOT / "film" / "poster.jpg", textfile)

    ig_square = ROOT / "social" / "instagram-Cursor" / "square.jpg"
    ig_portrait = ROOT / "social" / "instagram-Cursor" / "portrait.jpg"
    card = ROOT / "social" / "x-Cursor" / "card.jpg"
    ig_square.parent.mkdir(parents=True, exist_ok=True)
    card.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "art" / "square.jpg", ig_square)
    social_cmds = derive_social(ROOT / "art" / "hero.jpg", ROOT / "art" / "square.jpg", ig_portrait, card)
    lineage = {
        "painter": "tools/render_visual.py paint()",
        "hero": "JPEG of the 1280x720 sunset-grid framing. The film plate is a JPEG of the same PPM, made before this final hero file was written.",
        "square": "JPEG of the 1080x1080 square framing of the same painter. Not a scale of the hero.",
        "instagram_square": "Byte copy of art/square.jpg.",
        "instagram_square_sha256": sha256_file(ig_square),
        "square_sha256": sha256_file(ROOT / "art" / "square.jpg"),
        "instagram_portrait": "crop=864:1080:108:0 of the square still, then scale to 1080x1350.",
        "x_card": "scale the 1280x720 hero to 1600x900.",
        "commands": social_cmds,
        "poster_command": poster_cmd,
    }
    if lineage["instagram_square_sha256"] != lineage["square_sha256"]:
        raise SystemExit("Instagram square is not a byte copy of the square still")
    dump_json(ROOT / "social" / "lineage-Cursor.json", lineage)

    film_manifest = {
        "audio_source": "preview/preview.mp3",
        "audio_source_sha256": manifest["mp3_sha256"],
        "picture_source": "build/plate.jpg from the wide procedural paint. Disclosure text is drawn on top.",
        "on_picture": ON_PICTURE,
        "textfile_contents": textfile.read_text(encoding="utf-8").strip(),
        "encode_command": film_cmd,
        "video_codec": "libx264",
        "audio_codec": "aac",
        "audio_bitrate": "160k",
        "reencode_note": "Film audio is decoded from the MP3 and encoded as AAC. It is not byte-identical to the preview.",
        "duration_seconds": mp4_probe["duration"],
        "mp3_duration_seconds": mp3_probe["duration"],
        "streams": mp4_probe["streams"],
        "vtt": "film/preview.vtt",
        "font": "DejaVu Sans Bold, build machine only, not redistributed",
        "listening": AUDITION,
        "duration_relation": (
            f"MP3 container probe {mp3_probe['duration']:.3f} seconds. "
            f"MP4 probe {mp4_probe['duration']:.3f} seconds. "
            "The film ends on a video frame, so it is slightly shorter than the MP3 container. "
            "The music is the same preview, not a different excerpt."
        ),
    }
    if film_manifest["textfile_contents"] != ON_PICTURE:
        raise SystemExit("on-picture textfile drifted")
    dump_json(ROOT / "film" / "film-manifest-Cursor.json", film_manifest)

    set_measured_preview(mp3_probe["duration"])
    articles = ROOT / "articles"
    articles.mkdir(exist_ok=True)
    (articles / "medium-draft-Cursor.md").write_text(markdown(), encoding="utf-8")
    (articles / "medium-paste-Cursor.txt").write_text(plain_text(), encoding="utf-8")
    write_social(mp3_probe["duration"])
    write_identity(data["catalog"])
    write_page(ROOT / "index.html", data["catalog"], report, manifest, film_manifest)
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    write_readme(data["catalog"], manifest, film_manifest)
    write_publication_plan(manifest)

    frame = build / "film-frame.png"
    subprocess.run(
        ["ffmpeg", "-y", "-ss", "1", "-i", str(ROOT / "film" / "preview.mp4"), "-frames:v", "1", str(frame)],
        check=True,
        capture_output=True,
    )
    probes = {"mp3": mp3_probe, "mp4": mp4_probe}
    checklist = run_audit(ROOT, probes)
    dump_json(ROOT / "checks" / "artifact-checklist-Cursor.json", checklist)
    print(checklist["result"])
    for item in checklist["items"]:
        print(f"{item['status']:7} {item['name']} :: {item['evidence']}")
    if checklist["result"] != "PASS":
        raise SystemExit(1)
    print("TITLE", TITLE)
    print("X_BODY_CHARS", len(x_body(mp3_probe["duration"])))


if __name__ == "__main__":
    main()
