# medical-coder-llm (Python)

This repository is a Python implementation of **Symphony for Medical Coding** — the agentic, explainable medical coding approach described in [*Symphony for Medical Coding: A Next-Generation Agentic System for Scalable and Explainable Medical Coding*](https://arxiv.org/abs/2603.29709) (Edin et al., arXiv:2603.29709). [PDF](https://arxiv.org/pdf/2603.29709)

Symphony reasons over clinical narratives with access to the coding ontology (rather than predicting from a fixed label set), so predictions can adapt to different coding systems and are grounded in span-level evidence. This project mirrors that idea with a staged LLM workflow (aligned with the TypeScript reference in `with-bun/`):

1. Evidence extraction
2. Index navigation
3. Tabular validation
4. Code reconciliation

Supports OpenAI and Gemini. Configure defaults in `src/medical_coder_llm/config/models.py`.

## Install

```bash
uv sync
# or: pip install -e .
```

## Standalone executables (PyInstaller)

Build two one-file binaries locally (CLI + web):

```bash
uv sync --group dev
uv run pyinstaller medical-coder-llm-bundle.spec
```

Outputs land in `dist/` (`medical-coder-llm` and `medical-coder-llm-web`; on Windows, `.exe`). For the default ontology path **`data/ontology/codes.csv`**, if that file is missing from the current working directory the app uses a **bundled copy** shipped inside the package (so frozen binaries work without copying `data/`). Override with **`--ontology`** (CLI) or **`ontology`** in the API body. **`.env` / environment variables** still load from the environment like the normal install.

Pushes to **`main`** run [`.github/workflows/release-binaries.yml`](.github/workflows/release-binaries.yml), which builds Linux, macOS, and Windows binaries and uploads them to a **prerelease** on GitHub Releases (tag `v<version>-main.<run id>`).

## API keys

Set one of:

- `OPENAI_API_KEY` (provider `openai`)
- `GEMINI_API_KEY` (provider `gemini`)

`python-dotenv` loads `.env` from the current working directory.

## Input and ontology

- Default input: `input.txt`
- Default ontology: `data/ontology/codes.csv` (if that path is missing, the built-in sample ontology in the package is used instead)

CSV columns: `code`, `description`, `codingSystem`, `category`, `searchTerms`

## Run

```bash
uv run medical-coder-llm
python -m medical_coder_llm
```

```bash
uv run medical-coder-llm --input data/input.sample.txt -o output.json
uv run medical-coder-llm --provider gemini --model gemini-2.5-flash
uv run medical-coder-llm --ontology data/ontology/codes.csv
```

## Web UI (browser)

Start the local server from the project directory (so paths like `data/ontology/codes.csv` resolve correctly):

```bash
uv run medical-coder-llm-web
```

The terminal prints a URL, typically `http://127.0.0.1:8765`. Open that address in your browser (Safari, Chrome, or Edge), paste a clinical note, and click **Generate codes**.

Optional flags: `--host` and `--port` (defaults: `127.0.0.1` and `8765`).

The same process also exposes `POST /api/code` with JSON body `{ "note": "...", "ontology": "...", "provider": null, "model": null }` for programmatic use.

## Output

Structured JSON: `patientSummary`, `diagnosisCodes`, `procedureCodes`, `stageTrace`, `provider`, `model`, `generatedAt`.
