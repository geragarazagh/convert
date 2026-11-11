---
name: convert
description: "Converts a file into another format, size or form and checks the result: video and audio (play on a phone or TV, compress to a size, cut, join, GIF, extract sound), photos (HEIC to JPEG), PDF (merge, split, compress, OCR to searchable), DjVu, Word, Excel and PowerPoint to PDF, e-books, archives, subtitles, garbled letters and wrong text encodings, JSON, YAML, CSV. Use whenever a file has to become another file or be fixed."
license: MIT
compatibility: "Needs an assistant that can run commands: a terminal agent on the person's computer, or a chat app with code execution for uploaded files. Uses ffmpeg, ImageMagick, LibreOffice, pandoc and similar tools where installed."
---

# Convert

First, before any command: if you do not yet know this person's language
and how they like answers, your first reply is the two questions of «Before
the first job» and nothing else.

A conversion is done only by running a program on the person's own file. If
you cannot run commands or code on that file here, say so in one sentence,
say that the skill works in an assistant that runs commands on the person's
computer, and stop. Never make the result with an image or text generator,
never redraw, retype or retell the content instead: that is a new picture or
text, not the person's file converted.

Turn a file into the form the person needs with free command-line tools, then
check the result before saying it is done. `scripts/av.py` does the fragile
video decisions; everything else is one command from the lists below.

`scripts/av.py` lives in this skill's own folder, the folder that holds this
file, not in the person's folder. Call it by its full path, for example
`python3 /path/to/convert/scripts/av.py info video.mkv`; below it is written
short as `av.py`. It needs Python 3 and ffmpeg.

## Before the first job

Look at what you already know about this person: memory, a profile, custom
instructions, earlier messages of this conversation. If that tells you which
language to use and how short the answers should be, skip this section.

If it does not, do not start the job yet. Your first reply is only these two
questions, in the language of the person's message:

1. Which language should I answer in, and do you want short answers or the
   steps explained?
2. Where should I save results? Default: next to the original, under a new
   name.

Add that «go» accepts the defaults. Start the job after the answer. Keep the
answers for the rest of the conversation; store them nowhere else unless the
person asks.

## Every job

1. Find the input file: in the current folder first; if it is not there,
   ask for its path rather than search the whole disk. Never change, move or
   overwrite it, even when the request says «fix this file» or «make it
   searchable»: the result is always a new file beside it.
2. Look at it first. Media: `av.py info FILE`. Anything else:
   `file FILE`; PDF: `pdfinfo FILE`.
3. Pick the tool from the table. Copy instead of re-encoding whenever the
   target format allows it: copying is fast and loses nothing.
4. Write a new file: the same name with the new extension. If that name is
   taken, add « (2)», « (3)» before the extension.
5. Check the result (section «Check»). Fix and check again until it passes.
6. Delete the temporary files you made (test frames, copies, logs).
7. Report in two or three lines: where the file is, its size, what changed,
   and anything that was lost or dropped.

A request with two possible readings: take the likelier one and say which in
one line. Ask only what changes the result and cannot be guessed.

Usual meanings:
- «for a phone», «won't play», «for the TV», «for the web»: an mp4 that plays
  everywhere, `av.py play`.
- «for email»: under 25 MB. «for a messenger»: ask the limit if the file is
  large; many accept up to 2 GB.
- «smaller», «compress»: keep the format and lower the quality a little; give
  the old and new sizes.

## Tools

| Files | Tool | Check that it is there |
|---|---|---|
| video, audio, subtitles, GIF | ffmpeg | `ffmpeg -version` |
| photos and pictures | ImageMagick 7 | `magick -version` |
| SVG to picture | resvg | `resvg --version` |
| PDF | qpdf, poppler, Ghostscript, img2pdf, ocrmypdf | `qpdf --version`, `pdfinfo -v`, `gs -v` |
| DjVu | djvulibre | `ddjvu --help` |
| Word, Excel, PowerPoint, OpenDocument | LibreOffice | `soffice --version` |
| Markdown, HTML, docx, epub | pandoc | `pandoc --version` |
| e-books (fb2, epub, mobi, azw3) | calibre | `ebook-convert --version` |
| archives (zip, 7z, rar, iso) | 7-Zip | `7zz` or `7z` |
| text encodings | uchardet, iconv | `uchardet --version` |
| json, yaml, xml, csv | yq (mikefarah, v4) | `yq --version` |

When a tool is missing, name it, give the install command for this system and
wait. Install only after the person agrees.

- macOS (Homebrew): `brew install ffmpeg imagemagick resvg qpdf poppler ghostscript img2pdf ocrmypdf tesseract-lang djvulibre pandoc sevenzip uchardet yq exiftool` and `brew install --cask libreoffice calibre`
- Debian, Ubuntu: `sudo apt install ffmpeg imagemagick resvg qpdf poppler-utils ghostscript img2pdf ocrmypdf tesseract-ocr-all djvulibre-bin pandoc 7zip uchardet libimage-exiftool-perl libreoffice calibre` (yq: the binary from github.com/mikefarah/yq)
- Windows: `winget install Gyan.FFmpeg ImageMagick.ImageMagick JohnMacFarlane.Pandoc 7zip.7zip TheDocumentFoundation.LibreOffice calibre.calibre MikeFarah.yq`

In a chat app with code execution, work on the uploaded file inside the
sandbox and hand the result back as a download. Sandboxes often lack ffmpeg or
LibreOffice; Python libraries (Pillow, pypdf) may still cover pictures and
PDFs. If the job cannot be done there, say so plainly.

## Video and audio

- Plays everywhere (phones, computers, TVs, browsers):
  `av.py play IN OUT.mp4`. It copies H.264 and AAC/MP3 as they
  are, re-encodes the rest to H.264 + AAC, keeps every audio track with its
  language and turns text subtitles into mp4 subtitles. `--keep-hevc` keeps
  HEVC (smaller, HDR kept; plays on Apple devices and most new phones).
  `--crf 20` for better quality, `--crf 26` for a smaller file.
- Fit a size: `av.py size 25M IN OUT.mp4` (two passes; lowers
  the resolution when the size leaves too few bits for it).
- Only another container: `ffmpeg -i IN.mkv -map 0 -c copy -c:s mov_text OUT.mp4`.
  If it fails, the codecs don't fit mp4: use `av.py play`. The copy plays
  everywhere only if `av.py info` said so for every track.
- Cut without re-encoding: `ffmpeg -ss 00:01:00 -to 00:01:30 -i IN -c copy OUT`
  (starts at the keyframe before 1:00; for an exact start leave out `-c copy`).
- Join files of the same format: a list file with lines `file '/full/path'`,
  then `ffmpeg -f concat -safe 0 -i list.txt -c copy OUT`.
- Sound out of a video: `ffmpeg -i IN -vn -c:a copy OUT.m4a` when the audio
  is AAC; otherwise `-c:a aac -b:a 192k OUT.m4a`, or `-c:a libmp3lame -q:a 2 OUT.mp3`.
- Audio format: `ffmpeg -i IN.flac -c:a libmp3lame -q:a 2 OUT.mp3`;
  `-c:a flac OUT.flac`; `-c:a pcm_s16le OUT.wav`.
- GIF from 5 seconds at 0:10:
  `ffmpeg -ss 10 -t 5 -i IN -vf "fps=12,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a" OUT.gif`.
  An animated WebP looks the same and is about ten times smaller:
  `magick OUT.gif -quality 70 OUT.webp`.
- Rotate without re-encoding (ffmpeg 7 or newer):
  `ffmpeg -display_rotation 90 -i IN -map 0 -c copy OUT`.
- Burn subtitles into the picture: `ffmpeg -i IN -vf "subtitles=SUBS.srt" -c:a copy OUT.mp4`.
- Even loudness for speech: `ffmpeg -i IN -af loudnorm=I=-16:TP=-1.5:LRA=11 OUT`.

## Pictures

- HEIC, PNG, WebP, AVIF to JPEG: `magick IN -quality 90 OUT.jpg`. To WebP:
  `-quality 85 OUT.webp`; to AVIF: `-quality 60 OUT.avif`.
- Longest side 2048 pixels: `magick IN -resize 2048x2048\> OUT` (`\>` only
  shrinks, never enlarges).
- Many files: `magick mogrify -path OUTDIR -format jpg -quality 90 *.heic`.
- SVG to PNG: `resvg -w 1024 IN.svg OUT.png`. Icon: `magick IN.png -define icon:auto-resize=256,64,48,32,16 OUT.ico`.
- Remove location before sending to someone, on the copy:
  `exiftool -gps:all= -xmp:geotag= -overwrite_original COPY.jpg`.
- macOS also has `sips -s format jpeg IN.heic --out OUT.jpg` built in.

## PDF and scans

- Merge: `qpdf --empty --pages a.pdf b.pdf -- OUT.pdf`. Pages 3 to 7:
  `qpdf IN.pdf --pages . 3-7 -- OUT.pdf`. Rotate page 1: `qpdf IN.pdf OUT.pdf --rotate=+90:1`.
- To pictures: `pdftoppm -r 150 -jpeg IN.pdf page`. To text: `pdftotext -layout IN.pdf OUT.txt`.
- Pictures to PDF: `img2pdf --pagesize A4 --fit into *.jpg -o OUT.pdf`.
- Searchable scan: `ocrmypdf -l eng+rus IN.pdf OUT.pdf`. Choose the languages
  by looking at a page first (render one with `pdftoppm`); installed ones:
  `tesseract --list-langs`.
- Smaller: `gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook -dSAFER -dBATCH -dNOPAUSE -sOutputFile=OUT.pdf IN.pdf`.
- DjVu to PDF: `ddjvu -format=pdf -quality=60 IN.djvu OUT.pdf` (without
  `-quality` a page takes megabytes), then `ocrmypdf` if the text should be
  searchable. Text the DjVu already has: `djvutxt IN.djvu`.

## Documents and books

- Office to PDF: `soffice --headless --convert-to pdf --outdir OUTDIR IN.docx`
  (also xlsx, pptx, odt, doc, rtf). docx to odt or back: `--convert-to odt`.
- Markdown to Word, HTML, e-book: `pandoc IN.md -o OUT.docx` (or `.html`,
  `.epub`, `.odt`). To PDF: `pandoc IN.md -o OUT.docx`, then LibreOffice to PDF.
- E-books: `ebook-convert IN.fb2 OUT.epub` (also epub, mobi, azw3, pdf, txt, docx).

## Archives, text, data

- Unpack: `7zz x -oOUTDIR IN` (`7z` where only that one is installed). Zip a folder:
  `7zz a -tzip OUT.zip FOLDER` (no hidden macOS files inside).
- Garbled letters: `uchardet IN.txt` names the encoding, then
  `iconv -f WINDOWS-1251 -t UTF-8 IN.txt > OUT.txt` (use the name it printed).
- Data: `yq -o json IN.yaml > OUT.json`; `yq -p csv -o json IN.csv`;
  `yq -p xml -o yaml IN.xml`.

## Check

- Video and audio: `av.py check IN OUT` (duration and track
  counts). When the picture was changed (rotation, size, subtitles burned),
  look at one frame: `ffmpeg -ss 2 -i OUT -frames:v 1 frame.jpg`.
- Pictures: `magick identify OUT` (size, format); look at it once.
- PDF: `pdfinfo OUT.pdf` (pages as expected); `pdftotext OUT.pdf - | head` for
  text; render one page to look at.
- Documents and books: open or render the first page; the text is there.
- Archives: `7zz t OUT`; text files: `head OUT`.
- A smaller file must be smaller: compare sizes, keep the original if it is not.

## Known mistakes

- In a chat app, «convert this photo to JPEG» can start the app's image
  generator: it redraws the picture (another size, an invented paper
  texture, changed details) and calls it a JPEG. That is not a conversion;
  never offer it as one. Compare the result's size with the original.
- Overwriting the input with the output, or using `mogrify` without `-path`:
  it changes the originals.
- A failed ffmpeg run can leave an empty or half-written output file. Delete
  it before trying again; never hand it over.
- VP9, AV1, Opus or FLAC inside mp4 or mkv often won't play on phones, TVs or
  in QuickTime even when a computer player plays them. `av.py play` handles it.
- HEVC in mp4 must be tagged `hvc1`, not `hev1`, or iPhones refuse it.
- mp4 keeps only three-letter language codes: `ru` vanishes, `rus` stays.
- Picture subtitles (PGS, DVD) cannot go into mp4: burn them in or drop them.
- The container's duration can be wrong (chapters past the end); measure the
  longest audio or video stream instead.
- Joining mp3 files with `-c copy` breaks timestamps: re-encode.
- In loops, give ffmpeg `-nostdin`, or it eats the loop's input and files are
  cut short.
- Homebrew's `ffmpeg` on macOS has no libass (burning subtitles) and no
  libwebp; `brew install ffmpeg-full` has both (its path:
  `$(brew --prefix ffmpeg-full)/bin/ffmpeg`). Check:
  `ffmpeg -filters | grep subtitles`.
- Re-encoding an already compressed web video can make it bigger. Compare sizes.
- Ghostscript can make a text PDF bigger while it shrinks a scan. Compare and
  keep the smaller.
- Pictures with an orientation tag: some tools rotate the pixels, others keep
  the tag. Before `img2pdf`, run `magick IN -auto-orient OUT` or a portrait
  photo lands sideways on the page.
- `file -I` reports Windows-1251 Cyrillic as «iso-8859-1». Trust `uchardet`.
- Two different programs are called `yq`. The commands here are for
  mikefarah's v4; Debian's `yq` package is the other one.
- OCR has no models for old spelling (pre-1918 Russian, for example): expect
  noise and say so.
