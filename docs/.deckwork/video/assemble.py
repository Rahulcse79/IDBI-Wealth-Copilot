#!/usr/bin/env python
"""Synthesize Veena narration per scene and assemble the demo MP4."""
import os, subprocess, glob

HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(HERE, "frames")
AUD = os.path.join(HERE, "audio")
SEG = os.path.join(HERE, "segments")
for d in (AUD, SEG):
    os.makedirs(d, exist_ok=True)

OUT = os.path.expanduser("~/Downloads/IDBI_Wealth_Copilot_Demo.mp4")
VOICE, RATE = "Veena", "166"

NARR = [
    "Meet Aanya, the IDBI Wealth Copilot. An avatar-led, agentic, and explainable AI wealth "
    "advisor, built into the IDBI mobile app. Team Agentic Hackers created it for IDBI Innovate "
    "2026, Track 01, Wealth Advisory. Aanya turns each customer's own spending into personalized, "
    "bank-grade guidance. Let me show you how it works.",

    "Tap, My snapshot. Aanya reads your transactions to estimate your income, your savings rate, "
    "idle cash, and any high-interest debt. Then she ranks the actions that matter most, and "
    "every one of them is backed by your own numbers.",

    "Where my money goes breaks your spending into a clear donut chart, by category, and compares "
    "your income against your spending. You understand your money visually, in just a few seconds.",

    "Planning a goal? Ask Aanya to plan fifty lakh rupees for a house in eight years. She computes "
    "the exact monthly investment, recommends a real IDBI product allocation, and projects your "
    "growth, with a live slider to explore every what-if.",

    "The very same engine plans your retirement, two crore rupees over twenty years, instantly. "
    "Every figure is computed, never guessed, and every projection is shown as a chart you can trust.",

    "Aanya scores your risk capacity from zero to one hundred, and explains it factor by factor: "
    "your age, your horizon, your income stability, and more. That explainability is exactly what "
    "a bank, and a regulator, expect.",

    "Need products? Aanya searches the IDBI catalogue and recommends only real products, with their "
    "indicative, never guaranteed, returns, compared side by side.",

    "And when you ask her to guarantee returns, Aanya refuses. A compliance guardrail, enforced in "
    "code and unit-tested, blocks any guaranteed-return claim, and any product she has not actually "
    "looked up. Compliant, by design.",

    "Aanya. A personal wealth manager for every customer, at near-zero marginal cost. Avatar, voice, "
    "charts, and trust, ready for the IDBI app. Thank you, from team Agentic Hackers.",
]

frames = sorted(glob.glob(os.path.join(FRAMES, "*.png")))
assert len(frames) == len(NARR), (len(frames), len(NARR))


def duration(path):
    import wave
    with wave.open(path, "rb") as f:
        return f.getnframes() / float(f.getframerate())


seg_files = []
total = 0.0
for i, (frame, text) in enumerate(zip(frames, NARR), 1):
    wav = os.path.join(AUD, f"{i:02d}.wav")
    subprocess.run(["say", "-v", VOICE, "-r", RATE,
                    "--file-format=WAVE", "--data-format=LEI16@22050", "-o", wav, text], check=True)
    dur = duration(wav) + 0.7  # small tail pause
    total += dur
    seg = os.path.join(SEG, f"{i:02d}.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-framerate", "25", "-i", frame, "-i", wav,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-vf", "scale=1920:1080", "-af", "apad", "-t", f"{dur:.2f}", seg,
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    seg_files.append(seg)
    print(f"scene {i}: {dur:.1f}s")

listfile = os.path.join(HERE, "concat.txt")
with open(listfile, "w") as f:
    for s in seg_files:
        f.write(f"file '{s}'\n")

subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-c", "copy", OUT,
], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print(f"\nSaved: {OUT}")
print(f"Duration: {int(total // 60)}m {int(total % 60)}s")
