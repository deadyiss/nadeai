"""
Local RAG System — Command Line Interface.

CLI bypass auth dan otomatis pakai admin user (mode maintenance).
Web tetap pakai auth penuh.

Commands:
  python3 cli.py interactive
  python3 cli.py upload <file>
  python3 cli.py query "<text>"
  python3 cli.py query "<text>" --output json
  python3 cli.py stats
  python3 cli.py users
  python3 cli.py documents
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import config
from models import init_db, get_session, User, Document, QueryHistory
from core.auth_manager import get_auth_manager
from core.document_processor import get_document_processor
from core.query_processor import get_query_processor
from core.vector_store import get_vector_store
from core.llm_engine import get_llm_engine
from utils.file_validator import sanitize_filename, FileValidationError
from utils.logger import get_logger

# Suppress logging spam in CLI (only WARN+)
import logging
logging.getLogger().setLevel(logging.WARNING)

logger = get_logger("cli")


# ---------- ANSI colors ----------
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init()
    C_OK = Fore.GREEN
    C_ERR = Fore.RED
    C_WARN = Fore.YELLOW
    C_INFO = Fore.CYAN
    C_DIM = Style.DIM
    C_RESET = Style.RESET_ALL
except ImportError:
    C_OK = C_ERR = C_WARN = C_INFO = C_DIM = C_RESET = ""


def _get_admin_user() -> dict:
    """Get the admin user that CLI runs as."""
    with get_session() as s:
        admin = s.query(User).filter(User.role == "admin").first()
        if admin is None:
            print(f"{C_ERR}No admin user found. Run app.py first to bootstrap.{C_RESET}")
            sys.exit(1)
        return admin.to_dict()


def _bootstrap():
    """Ensure DB exists and admin user is created."""
    init_db()
    get_auth_manager().ensure_admin()


# ---------- Commands ----------

def cmd_upload(args) -> int:
    _bootstrap()
    filepath = Path(args.file)
    if not filepath.exists():
        print(f"{C_ERR}File not found: {filepath}{C_RESET}")
        return 1

    admin = _get_admin_user()
    is_shared = args.shared

    # Copy ke storage dir + index
    import uuid, shutil
    safe_name = sanitize_filename(filepath.name)
    storage_name = f"{uuid.uuid4().hex}_{safe_name}"
    user_dir = Path(config.UPLOAD_FOLDER) / str(admin["id"])
    user_dir.mkdir(parents=True, exist_ok=True)
    final_path = user_dir / storage_name

    try:
        shutil.copy2(filepath, final_path)
    except Exception as e:
        print(f"{C_ERR}Failed to copy file: {e}{C_RESET}")
        return 1

    print(f"{C_INFO}Processing {safe_name}...{C_RESET}")
    try:
        processor = get_document_processor()
        result = processor.process(str(final_path), original_filename=safe_name)
    except FileValidationError as e:
        final_path.unlink(missing_ok=True)
        print(f"{C_ERR}Validation error: {e}{C_RESET}")
        return 1
    except Exception as e:
        final_path.unlink(missing_ok=True)
        print(f"{C_ERR}Processing failed: {e}{C_RESET}")
        return 1

    # Save to DB + index
    try:
        store = get_vector_store()
        with get_session() as s:
            doc = Document(
                user_id=admin["id"],
                filename=safe_name,
                filepath=str(final_path),
                text=result["text"],
                word_count=result["word_count"],
                dates=json.dumps(result["dates"]),
                is_shared=is_shared,
            )
            s.add(doc)
            s.commit()
            s.refresh(doc)
            store.add(doc, s)
            s.commit()
            doc_id = doc.id
    except Exception as e:
        final_path.unlink(missing_ok=True)
        print(f"{C_ERR}Indexing failed: {e}{C_RESET}")
        return 1

    print(f"{C_OK}Uploaded:{C_RESET} {safe_name}")
    print(f"  doc_id    : {doc_id}")
    print(f"  word_count: {result['word_count']}")
    print(f"  dates     : {result['dates']}")
    print(f"  shared    : {is_shared}")
    if result.get("ocr_confidence") is not None:
        print(f"  OCR conf  : {result['ocr_confidence']:.2f}")
    return 0


def cmd_query(args) -> int:
    _bootstrap()
    admin = _get_admin_user()

    processor = get_query_processor()
    try:
        result = processor.process(
            query=args.text,
            user_id=admin["id"],
            include_shared=True,
            top_k=args.top_k,
            save_history=True,
        )
    except Exception as e:
        print(f"{C_ERR}Query failed: {e}{C_RESET}")
        return 1

    if args.output == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    # Pretty text output
    print()
    print(f"{C_INFO}Q:{C_RESET} {result['query']}")
    print()
    print(f"{C_OK}A:{C_RESET} {result['answer']}")
    print()
    print(f"{C_DIM}--- Sources ---{C_RESET}")
    if result["sources"]:
        for src in result["sources"]:
            print(f"  [{src['doc_id']:>3}] {src['filename']} "
                  f"(similarity={src['similarity']})")
    else:
        print("  (no sources)")

    print()
    conf_pct = result["confidence"] * 100
    conf_color = (C_OK if conf_pct >= 70 else
                   C_WARN if conf_pct >= 40 else C_ERR)
    print(f"  confidence    : {conf_color}{conf_pct:.1f}%{C_RESET}")

    halluc = result["hallucination"]
    halluc_color = (C_OK if halluc["status"] == "VERIFIED" else
                     C_WARN if halluc["status"] == "NO_CLAIMS" else C_ERR)
    print(f"  hallucination : {halluc_color}{halluc['status']}{C_RESET} "
          f"(score={halluc['overall_score']})")

    if result["has_conflict"]:
        print(f"  {C_WARN}CONFLICT WARNING{C_RESET}: "
              f"{len(result['conflict_details'])} conflict(s) detected")
        for c in result["conflict_details"]:
            print(f"    - [{c['severity']}] {c['conflict_type']}: {c['description']}")

    if halluc["claims"]:
        print()
        print(f"{C_DIM}--- Claim verification ---{C_RESET}")
        for cl in halluc["claims"]:
            mark = (f"{C_OK}✓{C_RESET}" if cl["status"] == "VERIFIED"
                    else f"{C_ERR}✗{C_RESET}")
            ent = cl.get("entailment", 0)
            con = cl.get("contradiction", 0)
            print(f"  {mark} {cl['claim'][:80]}")
            print(f"      entail={ent:.2f} contradict={con:.2f} "
                  f"verdict={cl.get('verdict', '?')}")

    print()
    print(f"{C_DIM}Stages: {result['stages']} | Total: {result['execution_time_ms']}ms{C_RESET}")
    return 0


def cmd_stats(args) -> int:
    _bootstrap()
    with get_session() as s:
        user_count = s.query(User).count()
        doc_count = s.query(Document).count()
        shared_count = s.query(Document).filter(Document.is_shared == True).count()
        query_count = s.query(QueryHistory).count()
        conflict_count = s.query(QueryHistory).filter(QueryHistory.has_conflict == True).count()

    store = get_vector_store()
    vstats = store.stats()
    llm = get_llm_engine()
    llm_ok = llm.health_check()

    print(f"{C_INFO}=== System Stats ==={C_RESET}")
    print(f"  Users          : {user_count}")
    print(f"  Documents      : {doc_count} ({shared_count} shared)")
    print(f"  Queries        : {query_count} ({conflict_count} with conflict)")
    print()
    print(f"{C_INFO}=== Vector Store ==={C_RESET}")
    print(f"  Vectors        : {vstats['total_vectors']}")
    print(f"  Dimension      : {vstats['dimension']}")
    print(f"  Model          : {vstats['model']}")
    print()
    print(f"{C_INFO}=== LLM ==={C_RESET}")
    print(f"  Model          : {config.LLM_MODEL}")
    print(f"  Host           : {config.OLLAMA_HOST}")
    print(f"  Reachable      : {C_OK + 'YES' + C_RESET if llm_ok else C_ERR + 'NO' + C_RESET}")
    return 0


def cmd_users(args) -> int:
    _bootstrap()
    with get_session() as s:
        users = s.query(User).order_by(User.id).all()
        print(f"{C_INFO}=== Users ({len(users)}) ==={C_RESET}")
        for u in users:
            active = "active" if u.is_active else "DISABLED"
            print(f"  [{u.id:>3}] {u.username:<20} {u.role:<8} {active:<10} "
                  f"{u.email or '-'}")
    return 0


def cmd_documents(args) -> int:
    _bootstrap()
    with get_session() as s:
        docs = s.query(Document).order_by(Document.id).all()
        print(f"{C_INFO}=== Documents ({len(docs)}) ==={C_RESET}")
        for d in docs:
            shared = " [SHARED]" if d.is_shared else ""
            print(f"  [{d.id:>3}] user={d.user_id} {d.filename:<40} "
                  f"words={d.word_count}{shared}")
    return 0


def cmd_interactive(args) -> int:
    _bootstrap()
    admin = _get_admin_user()
    print(f"{C_INFO}=== Local RAG — Interactive Mode ==={C_RESET}")
    print(f"Logged in as: {admin['username']} ({admin['role']})")
    print(f"Type your query, or commands:")
    print(f"  /upload <file>    — upload a document")
    print(f"  /stats            — show system stats")
    print(f"  /docs             — list documents")
    print(f"  /clear            — clear screen")
    print(f"  /exit or /quit    — exit")
    print()

    processor = get_query_processor()

    while True:
        try:
            text = input(f"{C_INFO}>{C_RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text:
            continue

        if text in ("/exit", "/quit"):
            break

        if text == "/clear":
            import os as _os
            _os.system("clear" if _os.name == "posix" else "cls")
            continue

        if text == "/stats":
            cmd_stats(args)
            continue

        if text == "/docs":
            cmd_documents(args)
            continue

        if text.startswith("/upload "):
            filepath = text[len("/upload "):].strip()
            if not filepath:
                print(f"{C_ERR}Usage: /upload <file>{C_RESET}")
                continue
            sub_args = argparse.Namespace(file=filepath, shared=False)
            cmd_upload(sub_args)
            continue

        # Default: treat as query
        sub_args = argparse.Namespace(
            text=text, output="text", top_k=None,
        )
        cmd_query(sub_args)

    print(f"{C_DIM}Goodbye.{C_RESET}")
    return 0


# ---------- Argparse ----------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Local RAG System — CLI (runs as admin)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # interactive
    sub.add_parser("interactive", help="Interactive REPL mode")

    # upload
    p_up = sub.add_parser("upload", help="Upload a document")
    p_up.add_argument("file", help="Path to file (pdf/docx/image)")
    p_up.add_argument("--shared", action="store_true",
                       help="Mark as shared (admin only)")

    # query
    p_q = sub.add_parser("query", help="Ask a question")
    p_q.add_argument("text", help="Query text (quote it)")
    p_q.add_argument("--output", choices=["text", "json"], default="text")
    p_q.add_argument("--top-k", type=int, default=None,
                      help="Number of top documents to retrieve")

    # stats
    sub.add_parser("stats", help="Show system stats")

    # users
    sub.add_parser("users", help="List all users")

    # documents
    sub.add_parser("documents", help="List all documents")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "interactive": cmd_interactive,
        "upload": cmd_upload,
        "query": cmd_query,
        "stats": cmd_stats,
        "users": cmd_users,
        "documents": cmd_documents,
    }

    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    try:
        return handler(args)
    except KeyboardInterrupt:
        print(f"\n{C_WARN}Interrupted.{C_RESET}")
        return 130


if __name__ == "__main__":
    sys.exit(main())