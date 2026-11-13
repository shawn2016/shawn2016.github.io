"""Local faster-whisper transcription for BV18JW96aEog."""
import json
import os
import sys

from faster_whisper import WhisperModel

MODEL_PATH = (
    "/Users/shawn/.cache/huggingface/hub/models--Systran--faster-whisper-tiny/"
    "snapshots/d90ca5fe260221311c53c58e660288d3deb8d356"
)
AUDIO = sys.argv[1]
OUT = sys.argv[2]

model = WhisperModel(MODEL_PATH, device="cpu", compute_type="int8")
segments, info = model.transcribe(AUDIO, language="zh", beam_size=5, vad_filter=True)
data = [
    {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
    for s in segments
]
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(
        {"duration": info.duration, "language": info.language, "segments": data},
        f,
        ensure_ascii=False,
        indent=2,
    )
lines = [f"[{d['start']:6.1f}-{d['end']:6.1f}] {d['text']}" for d in data]
with open(OUT.replace(".json", ".txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"OK: {len(data)} segments, duration={info.duration:.1f}s -> {OUT}")
