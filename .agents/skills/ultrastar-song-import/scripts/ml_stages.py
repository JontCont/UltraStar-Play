"""ML stages for the UltraStar song import skill.

Each stage writes its output into the work folder and is skipped when that
output already exists. Heavy imports stay inside the functions, so chart_core
and its tests run without torch. Install requirements-ml.txt before using this
module.
"""

from __future__ import annotations

import gc
import re
import shutil
import subprocess
from pathlib import Path

from chart_core import ChartError, log, write_json

MODEL = "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"
REVISION = "99ccb2737be22b8bb50dcfcc39ad4d567fb90cfd"
PITCH_FMIN = 65.4
PITCH_FMAX = 1046.5
CREPE_HOP_SECONDS = 0.01
CREPE_VOICED_CONFIDENCE = 0.21


def decode(path: Path, sample_rate: int, channels: int):
    import numpy as np

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise ChartError("ffmpeg was not found on PATH")
    result = subprocess.run(
        [ffmpeg, "-v", "error", "-i", str(path), "-f", "f32le", "-ar", str(sample_rate),
         "-ac", str(channels), "pipe:1"], check=True, capture_output=True)
    samples = np.frombuffer(result.stdout, dtype="<f4").copy().reshape(-1, channels).T
    if samples.size == 0 or not np.isfinite(samples).all():
        raise ChartError("Empty or non-finite audio")
    return samples


def separate(work: Path, audio: Path) -> None:
    import numpy as np
    import soundfile as sf
    import torch
    import torchaudio

    target = work / "vocals.wav"
    if target.exists():
        log("Reusing separated vocals")
        return
    bundle = torchaudio.pipelines.HDEMUCS_HIGH_MUSDB_PLUS
    model = bundle.get_model().eval()
    sr = bundle.sample_rate
    waveform = torch.from_numpy(decode(audio, sr, 2))
    mean = waveform.mean()
    scale = waveform.mean(0).std()
    if scale < 1e-6:
        raise ChartError("Source audio is silent")
    waveform = (waveform - mean) / scale
    length = waveform.shape[-1]
    output = torch.zeros(length)
    weight = torch.zeros(length)
    chunk = 8 * sr
    overlap = 2 * sr
    stride = chunk - overlap
    index = model.sources.index("vocals")
    with torch.inference_mode():
        for start in range(0, length, stride):
            stop = min(start + chunk, length)
            segment = waveform[:, start:stop]
            estimate = model(segment[None])[0, index].mean(0) * scale
            fade = torch.ones(stop - start)
            if start > 0:
                n = min(overlap, fade.numel())
                fade[:n] *= torch.linspace(0, 1, n)
            if stop < length:
                n = min(overlap, fade.numel())
                fade[-n:] *= torch.linspace(1, 0, n)
            output[start:stop] += estimate * fade
            weight[start:stop] += fade
            log(f"Vocal separation {stop / sr:.1f}/{length / sr:.1f}s")
            if stop == length:
                break
    if not torch.all(weight > 0):
        raise ChartError("Separation did not cover every sample")
    output /= weight
    if not torch.isfinite(output).all():
        raise ChartError("Non-finite separated vocals")
    temporary = work / "vocals.partial.wav"
    sf.write(temporary, output.numpy(), sr, subtype="FLOAT")
    temporary.replace(target)
    write_json(work / "separation.json", {
        "model": "torchaudio/HDEMUCS_HIGH_MUSDB_PLUS", "sample_rate": sr, "duration": length / sr,
        "rms": float(np.sqrt(np.mean(output.numpy() ** 2)))})


def align(work: Path, phrases: list[str], align_window: tuple[float | None, float | None],
          pool_accent_variants: bool) -> None:
    import numpy as np
    import torch
    import torchaudio
    from opencc import OpenCC
    from pypinyin import Style, lazy_pinyin
    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

    if (work / "alignment.json").exists():
        log("Reusing measured character alignment")
        return
    processor = Wav2Vec2Processor.from_pretrained(MODEL, revision=REVISION)
    model = Wav2Vec2ForCTC.from_pretrained(MODEL, revision=REVISION).eval()
    vocab = processor.tokenizer.get_vocab()
    convert = OpenCC("t2s")

    def syllable_key(value: str) -> str:
        if pool_accent_variants:
            value = re.sub(r"^(zh|ch|sh)", lambda match: match[0][0], value)
            value = re.sub(r"ng$", "n", value)
        return value

    characters = [(char, phrase) for phrase, text in enumerate(phrases) for char in text]
    normalized = [syllable_key(syllable) for phrase in phrases
                  for syllable in lazy_pinyin(convert.convert(phrase), style=Style.NORMAL)]
    # Singing does not keep speech tones, so Hanzi with the same syllable share probability mass.
    groups: dict[str, list[int]] = {}
    for char, token in vocab.items():
        if len(char) == 1 and "\u3400" <= char <= "\u9fff":
            syllable = syllable_key(lazy_pinyin(convert.convert(char), style=Style.NORMAL)[0])
            groups.setdefault(syllable, []).append(token)
    missing = sorted(set(char for char in normalized if char not in groups))
    if missing:
        raise ChartError(f"Model lacks {len(missing)} Mandarin syllables from the lyrics")
    blank = model.config.pad_token_id
    selected = sorted(set(normalized))
    mapping = {syllable: index + 1 for index, syllable in enumerate(selected)}
    blank_ids = sorted(set([blank, processor.tokenizer.word_delimiter_token_id]
                           + processor.tokenizer.all_special_ids))
    write_json(work / "alignment-homophones.json", {
        "method": "CTC probabilities pooled by Mandarin syllable (no lexical tone)",
        "accent_normalization": "zh/ch/sh and final n/ng pooled" if pool_accent_variants else None,
        "syllables": {syllable: [processor.tokenizer.convert_ids_to_tokens(token)
                                 for token in groups[syllable]] for syllable in selected}})

    audio = decode(work / "vocals.wav", 16000, 1)[0]
    full_duration = len(audio) / 16000
    offset = 0.0
    start_seconds, end_seconds = align_window
    if start_seconds is not None or end_seconds is not None:
        offset = float(start_seconds or 0.0)
        low = int(offset * 16000)
        high = len(audio) if end_seconds is None else int(end_seconds * 16000)
        audio = audio[low:high]
    emissions, centers, greedy = [], [], []
    core = 16 * 16000
    context = 16000
    with torch.inference_mode():
        for start in range(0, len(audio), core):
            end = min(start + core, len(audio))
            left = max(0, start - context)
            right = min(len(audio), end + context)
            values = processor(audio[left:right], sampling_rate=16000, return_tensors="pt")
            logits = model(**values).logits[0]
            probs = torch.log_softmax(logits, dim=-1)
            times = (left + 200 + np.arange(probs.shape[0]) * 320) / 16000
            keep = (times >= start / 16000) & (times < end / 16000)
            retained = probs[keep]
            emissions.append(torch.stack(
                [torch.logsumexp(retained[:, blank_ids], dim=-1)]
                + [torch.logsumexp(retained[:, groups[syllable]], dim=-1) for syllable in selected],
                dim=-1))
            centers.extend(times[keep].tolist())
            greedy.extend(probs[keep].argmax(dim=-1).tolist())
            log(f"Chinese emissions {end / 16000:.1f}/{len(audio) / 16000:.1f}s")
    del model
    gc.collect()
    emission = torch.cat(emissions).unsqueeze(0)
    np.savez_compressed(work / "phonetic-emissions.npz", log_probability=emission[0].numpy(),
                        centers=np.asarray(centers), syllables=np.asarray(["<blank>"] + selected))
    targets = torch.tensor([[mapping[syllable] for syllable in normalized]], dtype=torch.int32)
    paths, scores = torchaudio.functional.forced_align(emission, targets, blank=0)
    spans = torchaudio.functional.merge_tokens(paths[0], scores[0].exp(), blank=0)
    if len(spans) != len(characters):
        raise ChartError(f"Alignment lost characters: {len(spans)} vs {len(characters)}")
    aligned = []
    for (char, phrase), syllable, span in zip(characters, normalized, spans):
        if int(span.token) != mapping[syllable]:
            raise ChartError("Alignment token sequence mismatch")
        raw_probability = emission[0, span.start:span.end, int(span.token)].exp()
        nonblank_mass = 1 - emission[0, span.start:span.end, 0].exp()
        conditional = (raw_probability / nonblank_mass.clamp_min(1e-7)).clamp_max(1)
        aligned.append({
            "text": char, "phrase": phrase,
            "start": max(0, centers[span.start] - 0.01) + offset,
            "end": centers[span.end - 1] + 0.01 + offset,
            "confidence": float(span.score),
            "phoneme_confidence_given_nonblank": float(conditional.mean())})
    write_json(work / "alignment.json", aligned)
    write_json(work / "recognition-check.json", {
        "model": MODEL, "revision": REVISION,
        "greedy_transcript": processor.decode(greedy),
        "duration": full_duration,
        "analysis_window_seconds": [offset, offset + len(audio) / 16000],
        "characters": len(characters),
        "low_confidence_fraction": sum(c["confidence"] < .01 for c in aligned) / len(aligned)})
    log(f"Aligned {len(aligned)} supplied characters")


def pyin_pitch(work: Path) -> None:
    import librosa
    import numpy as np

    if (work / "pitch.npz").exists():
        log("Reusing measured pYIN pitch")
        return
    audio = decode(work / "vocals.wav", 22050, 1)[0]
    log("Estimating vocal F0 with pYIN")
    f0, voiced, probability = librosa.pyin(audio, fmin=PITCH_FMIN, fmax=PITCH_FMAX, sr=22050,
                                           frame_length=2048, hop_length=256, fill_na=np.nan)
    rms = librosa.feature.rms(y=audio, frame_length=2048, hop_length=256)[0]
    times = librosa.times_like(f0, sr=22050, hop_length=256)
    np.savez_compressed(work / "pitch.npz", time=times, f0=f0, voiced=voiced,
                        probability=probability, rms=rms)
    log(f"pYIN measured {len(f0)} frames")


def crepe_pitch(work: Path) -> None:
    import librosa
    import numpy as np
    import torch
    import torchcrepe

    if (work / "pitch-crepe.npz").exists():
        log("Reusing measured CREPE pitch")
        return
    audio = decode(work / "vocals.wav", 16000, 1)[0]
    log("Estimating vocal F0 with full CREPE and periodicity")
    with torch.inference_mode():
        f0, probability = torchcrepe.predict(
            torch.from_numpy(audio).unsqueeze(0), 16000, 160, PITCH_FMIN, PITCH_FMAX, "full",
            batch_size=256, device="cpu", return_periodicity=True)
        probability = torchcrepe.filter.median(probability, 3)
        f0 = torchcrepe.filter.median(f0, 3)
    values = f0[0].numpy()
    confidence = probability[0].numpy()
    rms = librosa.feature.rms(y=audio, frame_length=1024, hop_length=160)[0]
    if len(rms) != len(values):
        raise ChartError("CREPE and RMS frame counts differ")
    np.savez_compressed(work / "pitch-crepe.npz",
                        time=np.arange(len(values)) * CREPE_HOP_SECONDS, f0=values,
                        voiced=confidence >= CREPE_VOICED_CONFIDENCE,
                        probability=confidence, rms=rms)
    log(f"CREPE measured {len(values)} frames")


def measure_notes(work: Path, alignment: list[dict], tracker_name: str,
                  review_freestyle: bool) -> tuple[list[dict], list[dict]]:
    import numpy as np

    tracker = np.load(work / tracker_name)
    times, f0 = tracker["time"], tracker["f0"]
    active = tracker["voiced"] & (tracker["probability"] >= .2) & np.isfinite(f0)
    active &= tracker["rms"] >= max(1e-5, float(np.percentile(tracker["rms"], 90)) * .02)
    measured: list[dict] = []
    warnings: list[dict] = []
    for i, char in enumerate(alignment):
        next_start = max(0, alignment[i + 1]["start"] - .03) if i + 1 < len(alignment) else times[-1]
        start = max(0, char["start"] - .03)
        end = min(next_start - .01, char["end"] + .02)
        # CTC spikes can end before a sustained vowel, so extend only through measured voicing.
        limit = min(next_start - .015, char["end"] + 3.5)
        frame = int(np.searchsorted(times, max(start, end)))
        last_active = end
        silent_seconds = 0.0
        while frame < len(times) and times[frame] < limit:
            if active[frame]:
                last_active = float(times[frame])
                silent_seconds = 0.0
            else:
                # Fixed 256/22050 frame length matches the validated charts, even for CREPE's 10 ms hop.
                silent_seconds += 256 / 22050
                if silent_seconds > .12:
                    break
            frame += 1
        end = max(end, last_active)
        valid = (times >= start) & (times <= end) & active
        frequencies = f0[valid]
        issues = []
        if char["confidence"] < .01:
            issues.append("low_alignment_confidence")
        if len(frequencies) < 3:
            midi, kind = 60, "F"
            issues.append("no_reliable_pitch_freestyle")
        else:
            midis = 69 + 12 * np.log2(frequencies / 440)
            midi, kind = int(np.rint(np.median(midis))), ":"
            if np.percentile(midis, 90) - np.percentile(midis, 10) > 3:
                issues.append("pitch_variation_check_melisma")
        if review_freestyle and "low_alignment_confidence" in issues:
            kind = "F"
            issues.append("alignment_uncertain_freestyle_not_scored")
        measured.append({"text": char["text"], "phrase": char["phrase"], "kind": kind,
                         "pitch": midi - 60, "start": start, "end": end,
                         "confidence": char["confidence"], "issues": issues})
        if issues:
            warnings.append({"index": i, "seconds": round(start, 3), "issues": issues})
    return measured, warnings
