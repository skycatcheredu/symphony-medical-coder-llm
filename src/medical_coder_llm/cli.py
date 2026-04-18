from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import httpx
from dotenv import load_dotenv

from medical_coder_llm.config.models import LlmProvider, resolve_model_config
from medical_coder_llm.llm.client import build_llm_client
from medical_coder_llm.ontology.loader import load_ontology_entries
from medical_coder_llm.output.format import format_result_as_json
from medical_coder_llm.pipeline.orchestrator import run_coding_pipeline


def _print_help() -> None:
    text = "\n".join(
        [
            "Medical Coder CLI (Python)",
            "",
            "Usage:",
            "  medical-coder-llm [inputPath] [options]",
            "",
            "Options:",
            "  -i, --input <path>       Input patient note file (default: input.txt)",
            "  -o, --output <path>      Write output JSON to a file (default: stdout)",
            "  --provider <name>        LLM provider: openai | gemini",
            "  --model <name>           Model override",
            "  --ontology <path>        Ontology CSV path (default: data/ontology/codes.csv)",
            "  -h, --help               Show this help message",
            "",
            "Environment variables:",
            "  OPENAI_API_KEY           Required when provider=openai",
            "  GEMINI_API_KEY           Required when provider=gemini",
        ]
    )
    print(text)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("positional_input", nargs="?", default=None)
    parser.add_argument("-i", "--input", dest="input_opt", default=None)
    parser.add_argument("-o", "--output", dest="output_path", default=None)
    parser.add_argument("--provider", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--ontology", default="data/ontology/codes.csv")
    parser.add_argument("-h", "--help", action="store_true")
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None) -> None:
    load_dotenv()
    try:
        args = _parse_args(sys.argv[1:] if argv is None else argv)

        if args.help:
            _print_help()
            raise SystemExit(0)

        input_path = args.input_opt or args.positional_input or "input.txt"
        ontology_path = args.ontology

        provider: LlmProvider | None = None
        if args.provider is not None:
            if args.provider not in ("openai", "gemini"):
                print("Error: Unsupported provider. Use openai or gemini.", file=sys.stderr)
                raise SystemExit(1)
            provider = args.provider  # type: ignore[assignment]

        model_config = resolve_model_config(provider=provider, model=args.model)

        path = Path(input_path)
        if not path.is_file():
            print(f"Error: Input file not found: {input_path}", file=sys.stderr)
            raise SystemExit(1)
        note_text = path.read_text(encoding="utf-8").strip()
        if not note_text:
            print(f"Error: Input file is empty: {input_path}", file=sys.stderr)
            raise SystemExit(1)

        try:
            ontology_entries = load_ontology_entries(ontology_path)
        except (OSError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            raise SystemExit(1)

        with httpx.Client(timeout=120.0) as http:
            llm = build_llm_client(model_config, http)
            result = run_coding_pipeline(
                note_text=note_text,
                llm=llm,
                ontology_entries=ontology_entries,
            )

        output_json = format_result_as_json(result)
        if args.output_path:
            out = Path(args.output_path)
            out.write_text(output_json + "\n", encoding="utf-8")
            print(f"Wrote coding output to {args.output_path}")
            return

        print(output_json)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
