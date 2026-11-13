---
name: termux-python-deps
description: Install numpy/pandas/scipy via pkg on Termux, not pip.
version: 1.0.0
author: SenseNova (curator)
license: MIT
platforms: [android]
metadata:
  hermes:
    tags: [termux, android, pkg-install, numpy, pandas, python-deps, aarch64]
    category: productivity
    related_skills: [termux-native-doc-tools]
---

# Termux Python Dependencies (Scientific / Data)

On Termux (aarch64 Android), PyPI publishes no manylinux wheels for this platform — `pip install numpy pandas` silently falls back to building from source, which chains cmake → numpy → pandas with meson/Cython/g++ and takes 20+ minutes on ARM. It looks like a hang but is genuine compilation. The reliable path is Termux's `pkg`, which ships precompiled aarch64 builds.

## When to Use

- Installing numpy, pandas, scipy, or any C/Cython-heavy Python package on Termux.
- `pip install <pkg>` is compiling a build dependency (meson, Cython, cmake) and has been running for more than a couple of minutes.
- A backgrounded pip install appears stuck with `Installing build dependencies: still running...` repeating in the log.

Not this skill for: pure-Python packages (pyyaml, tabulate, click, requests, pydantic) — those install cleanly with pip, and there is no wheel benefit to switching to `pkg`. Also not for PDF/OCR/image native tools (poppler, tesseract, imagemagick) — use `termux-native-doc-tools`.

## Setup (once, idempotent)

If `pkg` errors with `No mirror or mirror group selected` (a fresh Termux box):

```bash
echo "deb https://packages-cf.termux.dev/apt/termux-main stable main" > $PREFIX/etc/apt/sources.list
pkg update -y
```

Then install precompiled scientific packages:

```bash
pkg install -y python-numpy python-pandas
# optional if needed
pkg install -y python-scipy
```

Current termux-main versions (verify with `pkg search python-numpy`): numpy 2.4.4, pandas 3.0.6, both aarch64.

For pure-Python deps, plain pip is fine and fast (no compiler, no wheels needed):

```bash
pip install --break-system-packages pyyaml tabulate
```

**scipy and scikit-learn are also NOT installable on Termux.** `pkg search python-scipy` returns no package (only numpy and pandas are shipped), and `pip install scipy` chains numpy rebuild via `--no-build-isolation` → fails at meson's `ctanhl` C99 implicit-function-declaration error on py3.14. `pip install scikit-learn` and `bottleneck` likewise fail. This blocks any composite tool whose pip metadata lists scipy/sklearn as a hard dep (vibe-trading-ai, mlflow, statsmodels, xgboost-cpu, etc.). Cloud (Colab) is the fallback for these — do not attempt local installs.

### Composite packages that need many heavy deps

When a package like `vibe-trading-ai` bundles 25+ dependencies (numpy, pandas, scipy, sklearn, langchain, duckdb, ccxt, yfinance, ...), full install is impossible on Termux because scipy/sklearn are missing. Partial install pattern:

```bash
# 1. Precompiled core
pkg install -y python-numpy python-pandas

# 2. Pure-Python package itself (skip deps check)
pip install --no-build-isolation --no-deps vibe-trading-ai

# 3. Install what CAN install via pip (pure Python, small)
pip install --break-system-packages rich pyyaml langchain langchain-core \
    langchain-openai langgraph langgraph-checkpoint python-dotenv h2 \
    oauth-cli-kit openpyxl python-docx python-pptx pypdfium2 joblib duckdb

# 4. Accept missing scipy / scikit-learn / bottleneck — CLI won't fully work,
#    but skill DOCS and pure-Python helpers still load.
```

Verify which of a package's declared deps are actually missing before claiming it's broken:

```bash
python3 -c "import importlib.metadata as m; print('\n'.join(str(r) for r in m.distribution('<pkg>').requires))"
```

Then check each with `importlib.import_module` — most 'composite' packages lose only 2-3 C-heavy deps, not the whole stack.

**PyTorch, TensorFlow, and other ML frameworks are NOT installable on Termux** — PyPI publishes no aarch64-linux-android wheels, and PyTorch's PyPI index (`https://download.pytorch.org/whl/cpu`) also returns `No matching distribution found` for Termux. Both `pip install torch` and `pip install torch --index-url https://download.pytorch.org/whl/cpu` fail. This blocks RVC, Coqui XTTS, OpenVoice V2, GPT-SoVITS, So-VITS-SVC, and every other PyTorch-based voice-clone / ML model locally. Same for `librosa` — it chains scipy which fails to build on Termux (no manylinux wheels). For ML/voice-clone tasks, the fallback is cloud APIs (ElevenLabs, HuggingFace Inference) or pre-generated audio from `edge-tts` — do not attempt local model installs.

Verify with one call:

```bash
python3 -c "import pandas, numpy, yaml, tabulate; print(pandas.__version__, numpy.__version__)"
```

## Pitfalls

- **pandas 3.0 on Termux stores `datetime64` as microseconds, not nanoseconds.** `.astype('int64')` gives values ~1e15 (µs since epoch) instead of ~1e18 (ns). Converting to unix seconds with `// 10**9` yields a timestamp 1000x too small (looks like Jan 1970). Use `.apply(lambda x: int(x.timestamp()))` for a resolution-independent conversion, or check the value magnitude against known ranges (2026 → ~1.76e9 seconds). This bites when aggregating tick CSVs to OHLCV candles and the timestamps silently turn into 1970.
- **Do not background `pip install pandas numpy` on Termux** — the source build takes 20-40 minutes and can look indefinitely stuck. Recognize the sign: `Installing build dependencies: still running...` in the log, followed by a g++ process compiling cmake-4.x. Kill it and switch to `pkg install -y python-numpy python-pandas` instead.
- **`--only-binary=:all:` on pip is a dead end on Termux** — it returns `No matching distribution found` for numpy/pandas/scipy because no aarch64-linux-android wheels exist on PyPI. Do not chase this path.
- **`pkg` and `pip` coexist fine.** Use `pkg` for precompiled C packages, `pip --break-system-packages` for pure-Python. `pkg install python-pandas` actually shells out to pip internally to install pure-Python deps, so mixing them does not conflict.
- **`pkg install python-pandas` needs `python-numpy` installed or as a dependency resolution.** `pkg install -y python-numpy python-pandas` in one command handles ordering; running them separately also works because pkg resolves deps.
- **A previously started pip source-build that you kill may leave orphan g++ processes.** Check `ps -eo pid,args | grep -E 'g\+\+|_in_process|pip_runner'` after killing the parent, and `kill -9` the stragglers if they survive — they hold memory and slow the subsequent pkg install.
- **Write scripts to `$HOME`, not `/tmp`.** `/tmp` on this environment is read-only; write scripts to `/data/data/com.termux/files/home/` and clean up after use.
- **`which` does not exist** on Termux. Use `[ -x /data/data/com.termux/files/usr/bin/<tool> ]` for presence checks.

## Verify

```bash
python3 -c "import pandas, numpy; print('pandas', pandas.__version__, 'numpy', numpy.__version__)"
```

Both should import cleanly in under a second. If import triggers a build warning or takes more than 5 seconds, the source build is still in progress — kill and switch to `pkg`.

## Not This Skill

- PDF/OCR/image native CLI tools (poppler, tesseract, imagemagick) — `termux-native-doc-tools`.
- Docker/conda/mamba Python environments — not applicable on Termux.
- Non-Termux Linux/macOS — plain `pip install pandas numpy` works there.
