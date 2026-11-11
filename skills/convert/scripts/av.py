#!/usr/bin/env python3
"""av.py: the fragile video and audio decisions of the convert skill, as one script.

Needs Python 3.8+ and ffmpeg + ffprobe on PATH. Standard library only.
Reads only the files you name, writes only the output you name, uses no network.

usage:
  av.py info FILE...                 streams, and whether each plays everywhere
  av.py play IN OUT.mp4 [--keep-hevc] [--crf N]
                                     mp4 for phones, computers, TVs and browsers:
                                     copies what already fits, re-encodes the rest
  av.py size TARGET IN OUT.mp4       fit a size, e.g. 25M, 8.5MB, 2G (decimal, as mail counts)
  av.py check SRC OUT                duration and track counts of OUT against SRC

exit codes: 0 done, 1 failed, 2 wrong arguments, 3 nothing to do, 4 ffmpeg missing
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

UNIVERSAL_AUDIO = {"aac", "mp3"}
TEXT_SUBS = {"subrip", "srt", "ass", "ssa", "webvtt", "mov_text", "text"}
HDR_TRANSFERS = {"smpte2084", "arib-std-b67"}


def fail(msg, code=1):
    print("Error: " + msg, file=sys.stderr)
    sys.exit(code)


def need(tool):
    if not shutil.which(tool):
        fail(tool + " not found. Install ffmpeg (it brings ffprobe): "
             "macOS: brew install ffmpeg | Debian/Ubuntu: sudo apt install ffmpeg | "
             "Windows: winget install Gyan.FFmpeg", 4)


def run(cmd):
    p = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    if p.returncode != 0:
        print("Failed: " + " ".join(cmd), file=sys.stderr)
        print(p.stderr.strip()[-3000:], file=sys.stderr)
        sys.exit(1)
    return p.stdout


def probe(path):
    need("ffprobe")
    if not os.path.isfile(path):
        fail("not a file: " + path, 2)
    return json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                           "-show_chapters", "-of", "json", path]))


def is_cover(s):
    return s.get("disposition", {}).get("attached_pic") == 1


def streams(info, kind):
    return [s for s in info.get("streams", []) if s.get("codec_type") == kind and not is_cover(s)]


def seconds(value):
    value = str(value)
    if ":" in value:
        h, m, s = value.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    return float(value)


def duration(info):
    """Longest audio or video stream. The container's duration can lie
    (chapters past the end once made a 60 s file report 570 s)."""
    best = 0.0
    for s in streams(info, "video") + streams(info, "audio"):
        d = s.get("duration") or s.get("tags", {}).get("DURATION")
        if d:
            try:
                best = max(best, seconds(d))
            except ValueError:
                pass
    return best or float(info.get("format", {}).get("duration", 0) or 0)


def video_fits(s, keep_hevc):
    """True when the video stream can be copied into an mp4 that plays everywhere."""
    pix = s.get("pix_fmt", "")
    if s.get("codec_name") == "h264":
        return pix in ("yuv420p", "yuvj420p") and s.get("profile") in (
            "Baseline", "Constrained Baseline", "Main", "High")
    if s.get("codec_name") == "hevc" and keep_hevc:
        return pix in ("yuv420p", "yuv420p10le")
    return False


def interlaced(s):
    return s.get("field_order") not in (None, "", "progressive", "unknown")


def audio_encoder():
    """Apple's AAC encoder on macOS, ffmpeg's own elsewhere."""
    enc = run(["ffmpeg", "-hide_banner", "-encoders"])
    return "aac_at" if " aac_at " in enc else "aac"


def aac_rate(s):
    ch = int(s.get("channels") or 2)
    return "96k" if ch == 1 else "160k" if ch == 2 else "384k"


def three_letter(lang):
    """mp4 keeps only ISO 639-2 codes: a two-letter 'ru' is dropped silently."""
    two = {"en": "eng", "ru": "rus", "uk": "ukr", "de": "deu", "fr": "fra", "es": "spa", "it": "ita",
           "pt": "por", "pl": "pol", "ja": "jpn", "zh": "zho", "ko": "kor", "tr": "tur", "ar": "ara"}
    return two.get(lang, lang)


def cmd_info(paths):
    for path in paths:
        info = probe(path)
        fm = info["format"]
        print(f"{path}: {fm.get('format_name')}, {duration(info):.1f} s, "
              f"{int(fm.get('size', 0)) / 1e6:.1f} MB, {len(info.get('chapters', []))} chapters")
        for s in info["streams"]:
            kind, codec = s.get("codec_type"), s.get("codec_name", "?")
            lang = s.get("tags", {}).get("language", "")
            if kind == "video" and is_cover(s):
                print(f"  #{s['index']} cover picture ({codec})")
            elif kind == "video":
                ok = video_fits(s, False)
                note = "plays everywhere" if ok else "needs re-encoding for everywhere"
                if s.get("color_transfer") in HDR_TRANSFERS:
                    note += ", HDR"
                if interlaced(s):
                    note += ", interlaced"
                print(f"  #{s['index']} video {codec} {s.get('profile', '')} {s.get('width')}x{s.get('height')} "
                      f"{s.get('pix_fmt')} {s.get('avg_frame_rate')} fps: {note}")
            elif kind == "audio":
                note = "plays everywhere" if codec in UNIVERSAL_AUDIO else "becomes AAC"
                print(f"  #{s['index']} audio {codec} {s.get('channels')} ch {lang}: {note}")
            elif kind == "subtitle":
                note = "kept as mp4 text" if codec in TEXT_SUBS else "picture subtitles: cannot go into mp4"
                print(f"  #{s['index']} subtitle {codec} {lang}: {note}")
            else:
                print(f"  #{s['index']} {kind} {codec}: dropped")


def free_out(out):
    if os.path.abspath(out) != out and not os.path.dirname(out):
        out = os.path.join(".", out)
    if os.path.exists(out):
        fail("output exists, choose another name: " + out, 2)
    return out


def cmd_play(src, out, keep_hevc, crf):
    need("ffmpeg")
    info = probe(src)
    out = free_out(out)
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-i", src]
    maps, codecs, notes = [], [], []
    vids = streams(info, "video")
    if len(vids) > 1:
        notes.append(f"{len(vids) - 1} extra video track(s) dropped")
    if vids:
        v = vids[0]
        maps += ["-map", f"0:{v['index']}"]
        if video_fits(v, keep_hevc):
            codecs += ["-c:v", "copy"]
            if v["codec_name"] == "hevc":
                codecs += ["-tag:v", "hvc1"]  # hev1 plays on a Mac but not on an iPhone
            notes.append("video copied")
        else:
            filters = ["bwdif"] if interlaced(v) else []
            filters.append("scale=trunc(iw/2)*2:trunc(ih/2)*2")  # H.264 4:2:0 needs even sides
            codecs += ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
                       "-pix_fmt", "yuv420p", "-vf", ",".join(filters)]
            notes.append(f"video {v.get('codec_name')} re-encoded to H.264 (crf {crf})")
            if v.get("color_transfer") in HDR_TRANSFERS:
                notes.append("HDR source: colours may look flat in H.264; "
                             "--keep-hevc keeps HDR for Apple devices")
    aenc = None
    for i, a in enumerate(streams(info, "audio")):
        maps += ["-map", f"0:{a['index']}"]
        if a.get("codec_name") in UNIVERSAL_AUDIO:
            codecs += [f"-c:a:{i}", "copy"]
        else:
            aenc = aenc or audio_encoder()
            codecs += [f"-c:a:{i}", aenc, f"-b:a:{i}", aac_rate(a)]
            if int(a.get("channels") or 2) > 6:
                codecs += [f"-ac:a:{i}", "6"]
            notes.append(f"audio #{a['index']} {a.get('codec_name')} to AAC")
        lang = a.get("tags", {}).get("language")
        if lang:
            codecs += [f"-metadata:s:a:{i}", "language=" + three_letter(lang)]
    n = 0
    for s in streams(info, "subtitle"):
        if s.get("codec_name") in TEXT_SUBS:
            maps += ["-map", f"0:{s['index']}"]
            codecs += [f"-c:s:{n}", "mov_text"]
            lang = s.get("tags", {}).get("language")
            if lang:
                codecs += [f"-metadata:s:s:{n}", "language=" + three_letter(lang)]
            n += 1
        else:
            notes.append(f"subtitle #{s['index']} is a picture format and was dropped "
                         "(burn it in with -filter_complex overlay if needed)")
    if not maps:
        fail("no audio or video in " + src)
    cmd += maps + codecs + ["-map_metadata", "0", "-map_chapters", "0", "-movflags", "+faststart", out]
    try:
        run(cmd)
    except SystemExit:
        if os.path.exists(out):
            os.remove(out)
        raise
    report = check(info, out)
    print("Done: " + out + " (" + report + ")")
    for line in notes:
        print("  " + line)


def parse_size(text):
    t = text.strip().upper().replace("B", "")
    mult = {"K": 1e3, "M": 1e6, "G": 1e9}.get(t[-1:], 1)
    try:
        return float(t[:-1] if t[-1:] in "KMG" else t) * mult
    except ValueError:
        fail("size must look like 25M, 8.5MB or 2G: " + text, 2)


def cmd_size(target_text, src, out):
    need("ffmpeg")
    target = parse_size(target_text)
    info = probe(src)
    out = free_out(out)
    if os.path.getsize(src) <= target:
        print(f"Nothing to do: {src} is already {os.path.getsize(src) / 1e6:.1f} MB")
        sys.exit(3)
    dur = duration(info)
    if not dur:
        fail("cannot read the duration of " + src)
    vids, auds = streams(info, "video"), streams(info, "audio")
    if not vids:
        fail("no video in " + src + "; for sound only, lower the audio bitrate instead", 2)
    v = vids[0]
    w, h = int(v.get("width") or 1280), int(v.get("height") or 720)
    fps = 30.0
    try:
        num, den = (v.get("avg_frame_rate") or "30/1").split("/")
        fps = float(num) / float(den) or 30.0
    except (ValueError, ZeroDivisionError):
        pass
    total_kbps = target * 8 / dur / 1000
    audio_kbps = 0 if not auds else (128 if total_kbps > 600 else 64)
    aenc = audio_encoder() if auds else None
    factor = 0.96
    tmp = tempfile.mkdtemp(prefix="avsize-")
    try:
        for attempt in range(3):
            video_kbps = int(total_kbps * factor - audio_kbps)
            if video_kbps < 50:
                fail(f"{target_text} is too small for {dur:.0f} s of video", 2)
            # below about 0.04 bits per pixel the picture falls apart: step down to a common height
            height = h
            for step in [x for x in (1080, 720, 540, 480, 360) if x < h]:
                if video_kbps * 1000 / (w * height / h * height * fps) >= 0.04:
                    break
                height = step
            vf = ["-vf", f"scale=-2:{height}"] if height != h else []
            base = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", src, "-map", f"0:{v['index']}"] + vf + [
                "-c:v", "libx264", "-preset", "slow", "-b:v", f"{video_kbps}k", "-pix_fmt", "yuv420p",
                "-passlogfile", os.path.join(tmp, "pass")]
            run(base + ["-pass", "1", "-an", "-f", "mp4", os.devnull])
            audio = ["-map", f"0:{auds[0]['index']}", "-c:a", aenc, "-b:a", f"{audio_kbps}k"] if auds else []
            part = os.path.join(tmp, "out.mp4")
            run(base + ["-pass", "2"] + audio + ["-movflags", "+faststart", part])
            size = os.path.getsize(part)
            if size <= target:
                shutil.move(part, out)
                report = check(info, out, ignore_extra=True)
                print(f"Done: {out} ({report}, target {target / 1e6:.1f} MB, height {height})")
                if len(auds) > 1:
                    print(f"  kept the first of {len(auds)} audio tracks")
                return
            factor *= target / size * 0.97
        fail(f"could not get under {target_text} in 3 tries")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check(src_info, out, ignore_extra=False):
    """Raise SystemExit when OUT is shorter or lost tracks; return a short status."""
    info = probe(out)
    a, b = duration(src_info), duration(info)
    if a and abs(a - b) > max(0.5, a * 0.005):
        fail(f"{out}: {b:.2f} s long, the source is {a:.2f} s")
    for kind in ("video", "audio"):
        want, got = len(streams(src_info, kind)), len(streams(info, kind))
        if kind == "video":
            want = min(want, 1)
        if got < (1 if ignore_extra and want else want):
            fail(f"{out}: {got} {kind} track(s), the source has {want}")
    return f"{b:.1f} s, {os.path.getsize(out) / 1e6:.1f} MB"


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__.strip())
        return
    cmd, rest = argv[0], argv[1:]
    if cmd == "info" and rest:
        cmd_info(rest)
    elif cmd == "play" and len([r for r in rest if not r.startswith("--")]) >= 2:
        keep = "--keep-hevc" in rest
        crf = 23
        if "--crf" in rest:
            i = rest.index("--crf")
            try:
                crf = int(rest[i + 1])
            except (IndexError, ValueError):
                fail("--crf needs a number, 18 (bigger, better) to 28 (smaller)", 2)
            rest = rest[:i] + rest[i + 2:]
        files = [r for r in rest if r != "--keep-hevc"]
        cmd_play(files[0], files[1], keep, crf)
    elif cmd == "size" and len(rest) == 3:
        cmd_size(*rest)
    elif cmd == "check" and len(rest) == 2:
        print("OK: " + check(probe(rest[0]), rest[1]))
    else:
        fail("unknown or incomplete command; run av.py --help", 2)


if __name__ == "__main__":
    main(sys.argv[1:])
