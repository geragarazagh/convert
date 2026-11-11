<img src="assets/icon.png" width="128" alt="convert icon: a sheet with one text written in three scripts">

# convert: a skill for AI assistants that converts files

A free, open source agent skill. Ask an assistant in plain words («make this video play on my phone», «turn these HEIC photos into JPEG», «make this scan searchable») and it picks a free command-line tool, converts the file, and checks the result before saying it is done.

Video, audio, subtitles, GIF, photos and pictures, SVG, PDF (merge, split, compress, OCR), DjVu, Word, Excel, PowerPoint, OpenDocument, Markdown, e-books (fb2, epub, mobi, azw3), archives (zip, 7z, rar), text encodings, JSON, YAML, XML, CSV.

Works in any assistant that can run commands: terminal agents (Claude Code, Codex, Gemini CLI and Antigravity, OpenCode, OpenClaw, Hermes and others) on the computer that holds the files, and chat apps with code execution for files uploaded there. One file, `SKILL.md`, carries the whole method; it can also be pasted into any chat as instructions.

## Install

Each way is marked by how it was checked: **run** means installed and used for real on the date in «Tested on»; **docs** means taken from the vendor's documentation on 2026-11-11 and not yet run.

### Terminal agents

One command for every agent found on the computer (needs Node.js; `-g` installs for the user, without it for the current project only) — **run**:

```sh
npx skills add geragarazagh/convert -g
```

It puts the skill into `~/.agents/skills/convert`, which Codex, Cursor, Cline, OpenCode and most other agents read, and links it into `~/.claude/skills` for Claude Code.

Claude Code, as a plugin — **run**:

```sh
claude plugin marketplace add geragarazagh/convert
claude plugin install convert@convert
```

By hand, any agent that reads the Agent Skills folder (Codex, OpenCode, OpenClaw, Hermes, Grok Build) — **docs**: copy `skills/convert` to `~/.agents/skills/convert`. Claude Code reads `~/.claude/skills/convert`; Antigravity reads `~/.gemini/config/skills/convert`.

### Chat apps

Download the files from [Releases](https://github.com/geragarazagh/convert/releases/latest):

- Claude (web, desktop, mobile): `convert.zip`. Customize → Skills → + → Upload; code execution must be on — **docs**.
- Gemini app (web, Mac, mobile): `convert.zip`, or the bare `SKILL.md` without the script. Customize → Skills → Create → Upload — **docs**.
- ChatGPT: `convert.zip`. Skills → Create → Upload — **docs**.

Chat sandboxes have no access to the files on the computer, only to uploads, and some lack ffmpeg or LibreOffice: there the skill does what the sandbox's tools allow and says when a job cannot be done.

### No skills in the app

Paste the text of [`SKILL.md`](skills/convert/SKILL.md) into the app's custom instructions or a project's instructions, or as the first message of a chat. This also works where the skill does not start by itself.

## Use

Ask for the result in plain words, in any language. To call the skill by name: `/convert` in Claude Code, Claude, Gemini and Antigravity; `$convert` in Codex; `@convert` in ChatGPT.

```
Make video.mkv play on my iPhone.
Compress this video to under 25 MB for email.
Convert all HEIC photos in this folder to JPEG.
Make a GIF from 0:10 to 0:15.
Merge these PDFs and make the scan searchable.
This subtitle file shows garbled letters, fix it.
```

On the first job the assistant asks two things, unless it already knows the person: the language and how short the answers should be, and where to save results (default: next to the original, under a new name).

## Tools it uses

Free, open source command-line programs, each only if installed: ffmpeg, ImageMagick, resvg, qpdf, poppler, Ghostscript, img2pdf, OCRmyPDF with Tesseract, DjVuLibre, LibreOffice, pandoc, calibre, 7-Zip, uchardet, iconv, yq, ExifTool. When one is missing, the assistant names it, gives the install command for the system (Homebrew, apt, winget) and waits for a yes.

`skills/convert/scripts/av.py` (Python 3, standard library, about 330 lines) holds the video decisions that are easy to get wrong: what to copy and what to re-encode for an mp4 that plays everywhere, two-pass encoding to a target size, and checking duration and tracks of the result.

## What this skill does on the computer

- Runs the tools above on the files named in the request.
- Reads only those files; writes only new files next to them or where the person said. Never overwrites, moves or deletes the original.
- Installs nothing by itself: names the install command and waits.
- Sends nothing over the network. The tools work offline. No telemetry, no accounts, no keys.
- Stores nothing about the person. The answers to the first-run questions live only in the conversation.
- The installers are other people's programs with their own rules: `npx skills` (Vercel) sends an anonymous install count unless `DISABLE_TELEMETRY=1` is set.

## Tested on

2026-11-11: Claude Haiku 5.5 (`claude-haiku-5-5`) in Claude Code 2.1.321 on macOS 27.2 (Apple M3 Pro), in a fresh Claude Code configuration with no user instructions; the skill installed with `npx skills add`; the claude.ai account it signed in with still had its own skills turned on. Nine real requests, each asked plainly and once more as `/convert …`, on real files: the Sintel trailer (Blender Foundation, CC BY 3.0) as H.264 mp4 and as VP9/Opus mkv with Windows-1251 subtitles, Chekhov's «Каштанка» (1929 Ukrainian edition, DjVu from Wikimedia Commons) and a three-page scan of it, a HEIC photo of its cover, a Word file. Requests in English, Russian and Ukrainian.

- Results: 18 of 18 right (checked by script: codecs, duration, size, pages, text layer, encoding); the original was never changed.
- The skill started by itself for 8 of the 9 plain requests; not for «make the PDF searchable», which was still done right.
- First-run questions: asked in 9 of 9 runs called as `/convert`, in 4 of 9 when the skill started by itself, and in none of 3 runs where the instructions already said the person's language and manner, as intended.
- The same nine plain requests without the skill: 8 of 9 right; the subtitle file was rewritten in place.

Not tested: other models, other agents, the chat apps, Linux and Windows.

## What it cannot do

- Files on the computer from a chat app: those apps see only uploads.
- Copy-protected media (DRM), password-protected files without the password.
- Layout-exact PDF to Word: text and simple layout only.
- OCR of old spellings Tesseract has no model for (pre-1918 Russian, for example).

## License

MIT
