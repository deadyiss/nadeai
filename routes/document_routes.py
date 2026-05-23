import json
import os
import uuid
from pathlib import Path

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

import config
from core.document_processor import get_document_processor
from core.vector_store import get_vector_store
from models import get_session, Document
from routes import require_auth
from utils.file_validator import sanitize_filename, FileValidationError
from utils.logger import get_logger
from utils.response_builder import success_response, error_response
from utils.text_cleaner import chunk_text

logger = get_logger(__name__)

doc_bp = Blueprint("documents", __name__, url_prefix="/api")


def _user_upload_dir(user_id: int) -> Path:
    p = Path(config.UPLOAD_FOLDER) / str(user_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


@doc_bp.route("/upload", methods=["POST"])
@require_auth
def upload(current_user):
    if "file" not in request.files:
        body, status = error_response("No file uploaded (field 'file' required)", status_code=400)
        return jsonify(body), status

    f = request.files["file"]
    if not f or not f.filename:
        body, status = error_response("Empty filename", status_code=400)
        return jsonify(body), status

    is_shared = request.form.get("is_shared", "false").lower() == "true"
    # Only admin can upload shared docs
    if is_shared and current_user.get("role") != "admin":
        body, status = error_response("Only admin can upload shared documents",
                                       code="FORBIDDEN", status_code=403)
        return jsonify(body), status

    # Save to temp first
    safe_original = sanitize_filename(secure_filename(f.filename))
    storage_name = f"{uuid.uuid4().hex}_{safe_original}"

    user_dir = _user_upload_dir(current_user["id"])
    final_path = user_dir / storage_name
    temp_path = Path(config.TEMP_UPLOAD_FOLDER) / storage_name
    temp_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        f.save(str(temp_path))
    except Exception as e:
        body, status = error_response(f"Failed to save upload: {e}", status_code=500)
        return jsonify(body), status

    # Process
    try:
        processor = get_document_processor()
        result = processor.process(str(temp_path), original_filename=safe_original)
    except FileValidationError as e:
        temp_path.unlink(missing_ok=True)
        body, status = error_response(str(e), code="INVALID_FILE", status_code=400)
        return jsonify(body), status
    except Exception as e:
        temp_path.unlink(missing_ok=True)
        logger.exception(f"Document processing failed")
        body, status = error_response(f"Processing failed: {e}", status_code=500)
        return jsonify(body), status

    # Move to permanent location
    try:
        temp_path.replace(final_path)
    except Exception as e:
        temp_path.unlink(missing_ok=True)
        body, status = error_response(f"Failed to store file: {e}", status_code=500)
        return jsonify(body), status

    # Split into chunks
    chunks = chunk_text(result["text"], chunk_size=300, overlap=50)
    if not chunks:
        chunks = [result["text"]]
    chunk_total = len(chunks)

    # Save to DB + index (one row per chunk)
    try:
        store = get_vector_store()
        first_doc = None
        with get_session() as s:
            for idx, chunk in enumerate(chunks):
                doc = Document(
                    user_id=current_user["id"],
                    filename=safe_original,
                    filepath=str(final_path),
                    text=chunk,
                    word_count=len(chunk.split()),
                    dates=json.dumps(result["dates"]) if idx == 0 else json.dumps([]),
                    is_shared=is_shared,
                    chunk_index=idx,
                    chunk_total=chunk_total,
                )
                s.add(doc)
                s.commit()
                s.refresh(doc)
                store.add(doc, s)
                s.commit()
                if idx == 0:
                    first_doc = doc.to_dict()

            return jsonify(success_response(
                data={
                    "document": first_doc,
                    "word_count": result["word_count"],
                    "chunks": chunk_total,
                    "dates": result["dates"],
                    "ocr_confidence": result.get("ocr_confidence"),
                },
                message=f"Document uploaded and indexed ({chunk_total} chunk{'s' if chunk_total > 1 else ''})",
            ))
    except Exception as e:
        final_path.unlink(missing_ok=True)
        logger.exception("DB insert failed")
        body, status = error_response(f"Indexing failed: {e}", status_code=500)
        return jsonify(body), status


@doc_bp.route("/documents", methods=["GET"])
@require_auth
def list_documents(current_user):
    with get_session() as s:
        if current_user.get("role") == "admin":
            docs = (s.query(Document)
                    .filter(Document.chunk_index == 0)
                    .order_by(Document.created_at.desc()).all())
        else:
            docs = (
                s.query(Document)
                .filter(
                    Document.chunk_index == 0,
                    (Document.user_id == current_user["id"]) | (Document.is_shared == True)
                )
                .order_by(Document.created_at.desc())
                .all()
            )
        return jsonify(success_response(data={
            "documents": [d.to_dict() for d in docs],
            "count": len(docs),
        }))


@doc_bp.route("/document/<int:doc_id>", methods=["DELETE"])
@require_auth
def delete_document(current_user, doc_id):
    with get_session() as s:
        doc = s.query(Document).filter(Document.id == doc_id).one_or_none()
        if doc is None:
            body, status = error_response("Document not found", status_code=404)
            return jsonify(body), status
        # Permission: owner OR admin
        is_owner = doc.user_id == current_user["id"]
        is_admin = current_user.get("role") == "admin"
        if not (is_owner or is_admin):
            body, status = error_response("Not authorized", code="FORBIDDEN", status_code=403)
            return jsonify(body), status

        filepath = doc.filepath
        store = get_vector_store()

        # Delete all chunks of this file
        all_chunks = s.query(Document).filter(Document.filepath == filepath).all()
        for chunk_doc in all_chunks:
            store.remove(chunk_doc.id, s)
            s.delete(chunk_doc)
        s.commit()

        # Delete file from disk
        try:
            Path(filepath).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to remove file {filepath}: {e}")

        return jsonify(success_response(message=f"Document {doc_id} deleted"))