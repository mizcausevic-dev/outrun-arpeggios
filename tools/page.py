"""Catalog page. The arpeggio and the chord are read from separate MIDI files."""

from __future__ import annotations

import json
from pathlib import Path

from tools.screening import render_media, sunset_frames
from tools.statements import AUDITION, ON_PICTURE, PREVIEW_LINE, PROGRAM, PUBLICATION, WARNING

SPELL = {
    "s01": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
    "s02": ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"],
    "s03": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
    "s04": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
    "s05": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
    "s06": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
    "s07": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
    "s08": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
}


def write_page(path: Path, catalog: dict, report: dict, preview: dict, film: dict) -> None:
    path.write_text(render_page(catalog, report, preview, film), encoding="utf-8")
    root = path.parent
    path.with_name("media.html").write_text(render_media({
        "pack_name": catalog["pack_name"],
        "subject": "The still is a sunset grid. Taller skyline bars are louder arpeggio accents.",
        "colors": {
            "bg": "#140818",
            "paper": "#ffe6cf",
            "ink": "#1a0c16",
            "accent": "#ff7a3c",
            "muted": "#e7b8c4",
        },
        "frames": sunset_frames(root),
        "preview_seconds": preview["seconds_encoded"],
        "film_seconds": film["duration_seconds"],
    }), encoding="utf-8")


def render_page(catalog: dict, report: dict, preview: dict, film: dict) -> str:
    rows = []
    for part in catalog["parts"]:
        kind = "core" if part["core"] else "harmonic reference"
        rows.append(
            "<tr>"
            f"<td><a href=\"{part['path']}\">{part['id']}</a></td>"
            f"<td>{part['role']}</td>"
            f"<td>{part['variation']}</td>"
            f"<td>{kind}</td>"
            f"<td>{part['bpm']}</td>"
            f"<td>{part['notes']}</td>"
            "</tr>"
        )
    set_map = []
    for study in catalog["studies"]:
        ids = [part["id"] for part in catalog["parts"] if part["study_id"] == study["id"]]
        set_map.append(f"<li><strong>{study['id']} {study['title']}</strong>: {', '.join(ids)}</li>")
    payload = {
        "studies": [
            {
                "id": study["id"],
                "title": study["title"],
                "bpm": study["bpm"],
                "bars": study["bars"],
                "collection": study["collection_name"],
                "tonic": study["tonal_reference"],
                "identity": study["identity"],
                "limitations": study["limitations"],
                "voicing": study["voicing"],
                "layering": study["layering"],
                "accent": study["accent"],
                "departures": study["departures"],
                "harmonic_rhythm": study["harmonic_rhythm"],
                "source_harmony": study["source_harmony"],
                "rhythm_a": study["rhythm_a"],
                "rhythm_b": study["rhythm_b"],
                "changes": study["changes"],
                "change_bars": study["change_bars"],
                "phrases": study["phrases"],
                "tempo_us": study["tempo_us"],
                "spell": SPELL[study["id"]],
            }
            for study in catalog["studies"]
        ],
        "parts": [
            {
                "id": part["id"],
                "study_id": part["study_id"],
                "role": part["role"],
                "variation": part["variation"],
                "path": part["path"],
            }
            for part in catalog["parts"]
        ],
    }
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    seconds = f"{preview['seconds_encoded']:.3f}"
    film_seconds = f"{film['duration_seconds']:.3f}"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Outrun Arpeggios</title>
  <style>
    :root {{
      --night: #140818;
      --ink: #ffe6cf;
      --sun: #ff7a3c;
      --hot: #ff3d6e;
      --gold: #ffc15a;
      --grid: #7d5cff;
      --muted: #e7b8c4;
      --line: rgba(255, 196, 140, .28);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background-color: var(--night);
      background-image:
        linear-gradient(rgba(255, 122, 60, .14) 1px, transparent 1px),
        linear-gradient(90deg, rgba(125, 92, 255, .16) 1px, transparent 1px);
      background-size: 46px 46px;
      color: var(--ink);
      font-family: "Trebuchet MS", "Segoe UI", sans-serif;
      line-height: 1.45;
    }}
    a {{ color: var(--gold); }}
    button, .meta, .kicker {{ font-family: ui-monospace, Menlo, Consolas, monospace; }}
    .wrap {{ width: min(1080px, calc(100% - 28px)); margin: 0 auto; padding-bottom: 28px; }}
    .mast {{
      display: flex; justify-content: space-between; gap: 16px; align-items: end;
      padding: 22px 0 12px;
    }}
    .wordmark {{ margin: 0; letter-spacing: .18em; text-transform: uppercase; font-size: .78rem; color: var(--sun); }}
    .mast nav {{ display: flex; flex-wrap: wrap; gap: 12px; font-size: .82rem; }}
    h1 {{ font-size: clamp(2rem, 5vw, 3.4rem); line-height: 1; margin: 6px 0 10px; font-weight: 600; }}
    h2 {{ font-size: 1.35rem; margin: 0 0 8px; font-weight: 600; }}
    .hero img, audio, video, .chord img {{
      display: block; width: 100%; max-width: 100%; height: auto; background: #000;
    }}
    .hero {{ margin: 0; }}
    figcaption, .meta {{ color: var(--muted); font-size: .82rem; }}
    p.keyline {{ color: var(--gold); font-size: 1.2rem; margin: 4px 0 12px; }}
    .deck {{
      display: grid; grid-template-columns: 220px minmax(0, 1fr); gap: 22px;
      margin-top: 22px; align-items: start;
    }}
    .rail {{ display: flex; flex-direction: column; gap: 6px; }}
    button {{
      border: 1px solid var(--line); background: rgba(20, 8, 24, .55); color: var(--ink);
      border-radius: 8px; padding: 8px 10px; cursor: pointer; text-align: left;
    }}
    button[aria-pressed="true"] {{ background: var(--sun); color: #1a0c16; border-color: var(--sun); }}
    .switch, .phrases {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0; }}
    .panel {{
      margin: 22px 0; padding: 16px;
      border: 1px solid var(--line);
      background: rgba(20, 8, 24, .78);
    }}
    .scroller {{ overflow-x: auto; max-width: 100%; background: #1a0c22; border-radius: 10px; }}
    .lane {{ position: relative; height: 188px; }}
    .harmony-lane {{ height: 132px; }}
    .tick {{
      position: absolute; top: 0; bottom: 0; width: 1px; background: rgba(125, 92, 255, .35);
    }}
    .block {{
      position: absolute; border-radius: 3px; min-width: 3px;
    }}
    .block.cool {{ background: #7d5cff; }}
    .block.warm {{ background: var(--sun); }}
    .block.hot {{ background: var(--hot); box-shadow: 0 0 0 1px var(--gold); }}
    .chord-grid {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;
      margin: 10px 0 14px;
    }}
    .chord {{
      margin: 0; padding: 10px; border: 1px solid var(--line); border-radius: 10px;
      background: #241028;
    }}
    .chord strong {{ display: block; color: var(--gold); font-size: 1.2rem; }}
    .legend {{ display: flex; flex-wrap: wrap; gap: 12px; font-size: .8rem; color: var(--muted); }}
    .swatch {{ display: inline-block; width: 12px; height: 12px; border-radius: 2px; margin-right: 4px; vertical-align: -1px; }}
    .flow {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0; }}
    .flow span {{ border: 1px solid var(--line); border-radius: 999px; padding: 4px 8px; font-size: .78rem; }}
    .table-scroll {{ overflow-x: auto; max-width: 100%; }}
    table {{ width: 100%; border-collapse: collapse; font-size: .8rem; }}
    th, td {{ text-align: left; padding: 7px 6px; border-bottom: 1px solid var(--line); white-space: nowrap; }}
    .transport {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 12px; }}
    @media (max-width: 720px) {{
      .mast, .deck {{ display: block; }}
      .rail {{ flex-direction: row; flex-wrap: wrap; margin-bottom: 12px; }}
      .mast nav {{ margin-top: 8px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <header class="mast">
      <p class="wordmark">Outrun Arpeggios</p>
      <nav>
        <a href="#arp">Arpeggio</a>
        <a href="#harmony">Source harmony</a>
        <a href="#files">Files</a>
        <a href="#reading">Recorded reading</a>
        <a href="media.html">Stills</a>
        <a href="midi/arrangement.mid">Arrangement</a>
      </nav>
    </header>
    <p class="keyline" id="facts"></p>
    <figure class="hero">
      <img src="art/hero.jpg" width="1280" height="720" alt="Illustration of a sunset grid with a skyline of arpeggio accents. Not a photograph of a studio or of performers.">
      <figcaption>Illustration of a sunset grid. The skyline follows an accent contour. Not a photograph.</figcaption>
    </figure>
    <section class="deck">
      <div class="rail" id="rail"></div>
      <div>
        <p class="kicker" id="kicker"></p>
        <h1 id="title">Horizon Ladder</h1>
        <p id="identity"></p>
        <p id="rhythm"></p>
        <p id="source"></p>
        <p id="accent-copy"></p>
        <p class="meta" id="limits"></p>
        <p class="meta" id="departures"></p>
        <div class="switch">
          <button type="button" id="var-a" aria-pressed="true">Variation A</button>
          <button type="button" id="var-b" aria-pressed="false">Variation B</button>
        </div>
        <div class="phrases" id="phrases"></div>
        <div class="transport">
          <button type="button" id="play">Play arpeggio</button>
          <button type="button" id="harmony-toggle" aria-pressed="true">Source harmony</button>
          <span id="transport-label">Space plays. J and K change study.</span>
        </div>
      </div>
    </section>
    <section class="panel" id="arp">
      <h2>Arpeggio</h2>
      <p>These notes are fetched from the arpeggio MIDI file. Taller, hotter bars are louder accents. The chord is not drawn in this lane.</p>
      <div class="scroller" id="arp-scroll">
        <div class="lane" id="arp-lane"></div>
      </div>
      <p class="legend">
        <span><i class="swatch" style="background:#7d5cff"></i>softer attacks</span>
        <span><i class="swatch" style="background:#ff7a3c"></i>velocity 90 to 109</span>
        <span><i class="swatch" style="background:#ff3d6e"></i>velocity 110 and up</span>
      </p>
      <p class="meta" id="status">Reading the MIDI.</p>
    </section>
    <section class="panel" id="harmony">
      <h2>Source harmony</h2>
      <p>This reference is fetched from its own MIDI file. It shows the chord the arpeggio outlines. It is not merged into the arpeggio lane.</p>
      <div class="chord-grid" id="chord-cards"></div>
      <div class="scroller" id="harmony-scroll">
        <div class="lane harmony-lane" id="harmony-lane"></div>
      </div>
    </section>
    <section class="panel">
      <h2>File contract</h2>
      <div class="flow">
        <span>Canonical score</span><span>MIDI</span><span>Reopened validation</span><span>MP3</span><span>Film</span>
        <span>Stills</span><span>Social drafts</span><span>Catalog</span><span>This page</span>
      </div>
      <h2>Set map</h2>
      <ul>
        {''.join(set_map)}
      </ul>
      <p>{catalog['range_statement']}</p>
      <p>{WARNING}</p>
    </section>
    <section class="panel" id="files">
      <h2>Files</h2>
      <p class="meta">Validation {report['result']}. Core arpeggios {catalog['core_part_count']}. Harmonic references {catalog['reference_part_count']}. <a href="midi/validation-Cursor.json">validation report</a> · <a href="catalog/catalog-Cursor.json">catalog</a> · <a href="score/canonical-score-Cursor.json">score</a> · <a href="score/identity-Cursor.md">identity</a></p>
      <div class="table-scroll">
        <table>
          <thead><tr><th>Part</th><th>Role</th><th>Var</th><th>Count</th><th>BPM</th><th>Notes</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
    </section>
    <section class="panel" id="reading">
      <h2>Recorded reading</h2>
      <p class="kicker">Study 01 variation A, all 16 bars, arpeggio plus harmonic reference</p>
      <p>This MP3 is {seconds} seconds. {PREVIEW_LINE}. The film is {film_seconds} seconds and shows {ON_PICTURE}.</p>
      <audio controls preload="metadata" src="preview/preview.mp3"></audio>
      <p><a href="preview/preview.mp3">preview/preview.mp3</a> · <a href="preview/preview-manifest-Cursor.txt">preview manifest</a></p>
      <video controls preload="metadata" poster="film/poster.jpg" width="1280" height="720">
        <source src="film/preview.mp4" type="video/mp4">
        <track kind="captions" src="film/preview.vtt" srclang="en" label="English" default>
      </video>
      <p><a href="film/preview.mp4">film/preview.mp4</a> · <a href="film/preview.vtt">film/preview.vtt</a> · <a href="film/poster.jpg">poster</a></p>
    </section>
    <section class="panel">
      <p>{PROGRAM}</p>
      <p>{AUDITION}</p>
      <p>{PUBLICATION}</p>
      <p>Article draft, not posted: <a href="articles/medium-draft-Cursor.md">Markdown</a> · <a href="articles/medium-paste-Cursor.txt">plain text</a></p>
    </section>
  </div>
  <script id="pack" type="application/json">{data}</script>
  <script>
    const pack = JSON.parse(document.getElementById("pack").textContent);
    const rail = document.getElementById("rail");
    const phrases = document.getElementById("phrases");
    const arpLane = document.getElementById("arp-lane");
    const harmonyLane = document.getElementById("harmony-lane");
    const arpScroll = document.getElementById("arp-scroll");
    const status = document.getElementById("status");
    let studyId = "s01";
    let variation = "a";
    let arpNotes = [];
    let harmonyNotes = [];
    let hearHarmony = true;
    let audio = null;
    let playing = false;
    let followId = 0;
    let rollWidth = 1200;

    function study() {{
      return pack.studies.find((item) => item.id === studyId);
    }}
    function pitchName(pitch) {{
      return study().spell[pitch % 12] + (Math.floor(pitch / 12) - 1);
    }}
    function readVlq(view, offset) {{
      let value = 0;
      let byte = 0;
      do {{
        byte = view.getUint8(offset);
        offset += 1;
        value = (value << 7) | (byte & 0x7f);
      }} while (byte & 0x80);
      return [value, offset];
    }}
    function parseMidi(buffer) {{
      const view = new DataView(buffer);
      if (String.fromCharCode(view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3)) !== "MThd" || view.getUint16(12) !== 960) {{
        throw new Error("unexpected MIDI header");
      }}
      const tracks = view.getUint16(10);
      let offset = 14;
      const notes = [];
      for (let track = 0; track < tracks; track += 1) {{
        if (String.fromCharCode(view.getUint8(offset), view.getUint8(offset + 1), view.getUint8(offset + 2), view.getUint8(offset + 3)) !== "MTrk") {{
          throw new Error("missing track");
        }}
        const length = view.getUint32(offset + 4);
        offset += 8;
        const end = offset + length;
        let tick = 0;
        let running = 0;
        const open = new Map();
        while (offset < end) {{
          let delta;
          [delta, offset] = readVlq(view, offset);
          tick += delta;
          let byte = view.getUint8(offset);
          if (byte >= 0x80) {{
            running = byte;
            offset += 1;
          }}
          if (running === 0xff) {{
            offset += 1;
            let metaLen;
            [metaLen, offset] = readVlq(view, offset);
            offset += metaLen;
            continue;
          }}
          const kind = running & 0xf0;
          const data1 = byte < 0x80 ? byte : view.getUint8(offset);
          if (byte >= 0x80) offset += 1;
          let data2 = 0;
          if (kind !== 0xc0 && kind !== 0xd0) {{
            data2 = view.getUint8(offset);
            offset += 1;
          }}
          const key = (running & 0x0f) + ":" + data1;
          if (kind === 0x90 && data2 > 0) open.set(key, {{ tick: tick, velocity: data2 }});
          else if (kind === 0x80 || (kind === 0x90 && data2 === 0)) {{
            const started = open.get(key);
            if (started) {{
              notes.push({{ pitch: data1, start: started.tick, duration: tick - started.tick, velocity: started.velocity }});
              open.delete(key);
            }}
          }}
        }}
      }}
      notes.sort((a, b) => a.start - b.start || a.pitch - b.pitch);
      return notes;
    }}
    function partPath(role) {{
      const found = pack.parts.find((part) => part.study_id === studyId && part.role === role && part.variation === variation);
      if (!found) throw new Error("missing " + role);
      return found.path;
    }}
    function heat(velocity) {{
      if (velocity >= 110) return "hot";
      if (velocity >= 90) return "warm";
      return "cool";
    }}
    function renderCopy() {{
      const item = study();
      document.getElementById("kicker").textContent = item.id + "  " + item.bpm + " BPM  " + item.bars + " bars";
      document.getElementById("title").textContent = item.title;
      document.getElementById("identity").textContent = item.identity;
      document.getElementById("facts").textContent = item.collection + ". Tonic reference " + item.tonic + ".";
      document.getElementById("rhythm").textContent = variation === "a" ? item.rhythm_a : item.rhythm_b;
      document.getElementById("source").textContent = item.source_harmony + " " + item.harmonic_rhythm;
      document.getElementById("accent-copy").textContent = item.accent;
      document.getElementById("limits").textContent = item.limitations;
      document.getElementById("departures").textContent = item.departures.length ? item.departures.join(" ") : "No pitch in this study is flagged as a departure.";
      document.getElementById("transport-label").textContent = item.title + " " + variation.toUpperCase() + ". Space plays. J and K change study.";
      for (const button of rail.querySelectorAll("button")) button.setAttribute("aria-pressed", button.dataset.id === studyId ? "true" : "false");
      document.getElementById("var-a").setAttribute("aria-pressed", variation === "a" ? "true" : "false");
      document.getElementById("var-b").setAttribute("aria-pressed", variation === "b" ? "true" : "false");
      phrases.innerHTML = "";
      item.phrases.forEach((phrase) => {{
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = phrase.name;
        button.addEventListener("click", () => {{
          arpScroll.scrollTo({{ left: Math.max(0, (phrase.start_bar / item.bars) * rollWidth - 12), behavior: "smooth" }});
        }});
        phrases.appendChild(button);
      }});
    }}
    function paintLane(host, notes, tall) {{
      host.innerHTML = "";
      host.style.width = rollWidth + "px";
      const item = study();
      const container = item.bars * 4 * 960;
      for (let bar = 0; bar <= item.bars; bar += 1) {{
        const tick = document.createElement("div");
        tick.className = "tick";
        tick.style.left = (bar / item.bars) * rollWidth + "px";
        host.appendChild(tick);
      }}
      if (!notes.length) return;
      const low = Math.min(...notes.map((note) => note.pitch));
      const high = Math.max(...notes.map((note) => note.pitch));
      const span = Math.max(1, high - low);
      const ceiling = tall ? 118 : 78;
      notes.forEach((note) => {{
        const block = document.createElement("div");
        block.className = "block " + heat(note.velocity);
        block.title = pitchName(note.pitch) + " velocity " + note.velocity;
        block.dataset.velocity = String(note.velocity);
        block.dataset.pitch = String(note.pitch);
        const y = 12 + (1 - (note.pitch - low) / span) * ceiling;
        const h = 8 + (note.velocity / 127) * (tall ? 40 : 28);
        block.style.left = (note.start / container) * rollWidth + "px";
        block.style.width = Math.max(3, (note.duration / container) * rollWidth - 1) + "px";
        block.style.top = y + "px";
        block.style.height = h + "px";
        host.appendChild(block);
      }});
    }}
    function paintChords() {{
      const item = study();
      const board = document.getElementById("chord-cards");
      board.innerHTML = "";
      let bar = 0;
      item.changes.forEach((name, index) => {{
        const span = item.change_bars[index];
        const start = bar * 4 * 960;
        const end = (bar + span) * 4 * 960;
        const heard = harmonyNotes.filter((note) => note.start >= start && note.start < end);
        const pitches = Array.from(new Set(heard.map((note) => note.pitch))).sort((a, b) => a - b);
        const card = document.createElement("article");
        card.className = "chord";
        const title = document.createElement("strong");
        title.textContent = name;
        const body = document.createElement("p");
        body.textContent = pitches.length ? pitches.map(pitchName).join(" ") : "No reference notes in this region.";
        card.appendChild(title);
        card.appendChild(body);
        board.appendChild(card);
        bar += span;
      }});
    }}
    function draw() {{
      const item = study();
      rollWidth = Math.max(760, item.bars * 168);
      paintLane(arpLane, arpNotes, true);
      paintLane(harmonyLane, harmonyNotes, false);
      paintChords();
      const hot = arpNotes.filter((note) => note.velocity >= 110).length;
      status.textContent = arpNotes.length + " arpeggio notes from the part file. " + hot + " accents at velocity 110 or higher. " + harmonyNotes.length + " reference notes stay in the chord panel.";
    }}
    async function loadStudy() {{
      stopPlayback();
      renderCopy();
      status.textContent = "Reading the MIDI.";
      try {{
        const arpRes = await fetch(partPath("arpeggio"));
        const chordRes = await fetch(partPath("harmonic-reference"));
        if (!arpRes.ok || !chordRes.ok) throw new Error("MIDI request failed");
        arpNotes = parseMidi(await arpRes.arrayBuffer());
        harmonyNotes = parseMidi(await chordRes.arrayBuffer());
        draw();
      }} catch (error) {{
        arpNotes = [];
        harmonyNotes = [];
        status.textContent = "The MIDI did not load. " + error.message;
      }}
    }}
    function freq(pitch) {{
      return 440 * Math.pow(2, (pitch - 69) / 12);
    }}
    function schedule(ctx, note, origin, amount, type) {{
      const item = study();
      const seconds = (tick) => tick / 960 * item.tempo_us / 1000000;
      const when = origin + seconds(note.start);
      const duration = Math.max(0.05, seconds(note.duration));
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = type;
      osc.frequency.value = freq(note.pitch);
      const level = amount * (note.velocity / 110);
      const attack = Math.min(0.012, duration * 0.2);
      gain.gain.setValueAtTime(0.0001, when);
      gain.gain.exponentialRampToValueAtTime(Math.max(0.0002, level), when + attack);
      gain.gain.exponentialRampToValueAtTime(0.0001, when + duration);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(when);
      osc.stop(when + duration + 0.02);
    }}
    function stopPlayback() {{
      playing = false;
      cancelAnimationFrame(followId);
      if (audio) audio.close();
      audio = null;
      document.getElementById("play").textContent = "Play arpeggio";
    }}
    function playLine() {{
      if (!arpNotes.length) return;
      stopPlayback();
      const ctx = new AudioContext();
      audio = ctx;
      playing = true;
      document.getElementById("play").textContent = "Stop";
      const origin = ctx.currentTime + 0.05;
      arpNotes.forEach((note) => schedule(ctx, note, origin, 0.07, "square"));
      if (hearHarmony) harmonyNotes.forEach((note) => schedule(ctx, note, origin, 0.025, "sine"));
      const item = study();
      const container = item.bars * 4 * 60 / item.bpm;
      const follow = () => {{
        if (!playing || !audio) return;
        if (audio.currentTime - origin < container) followId = requestAnimationFrame(follow);
        else stopPlayback();
      }};
      follow();
    }}
    function stepStudy(direction) {{
      const index = pack.studies.findIndex((item) => item.id === studyId);
      studyId = pack.studies[(index + direction + pack.studies.length) % pack.studies.length].id;
      loadStudy();
    }}
    pack.studies.forEach((item) => {{
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.id = item.id;
      button.textContent = item.id.slice(1) + " " + item.title;
      button.addEventListener("click", () => {{ studyId = item.id; loadStudy(); }});
      rail.appendChild(button);
    }});
    document.getElementById("var-a").addEventListener("click", () => {{ variation = "a"; loadStudy(); }});
    document.getElementById("var-b").addEventListener("click", () => {{ variation = "b"; loadStudy(); }});
    document.getElementById("play").addEventListener("click", () => {{ if (playing) stopPlayback(); else playLine(); }});
    document.getElementById("harmony-toggle").addEventListener("click", () => {{
      hearHarmony = !hearHarmony;
      document.getElementById("harmony-toggle").setAttribute("aria-pressed", hearHarmony ? "true" : "false");
    }});
    window.addEventListener("keydown", (event) => {{
      const target = event.target;
      if (target && target.closest && target.closest("video, audio, input, textarea")) return;
      if (event.code === "Space") {{
        event.preventDefault();
        if (playing) stopPlayback(); else playLine();
      }} else if (event.key === "j" || event.key === "J") stepStudy(-1);
      else if (event.key === "k" || event.key === "K") stepStudy(1);
    }});
    loadStudy();
  </script>
</body>
</html>
"""
