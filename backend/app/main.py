import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from .services.plagiarism.plagiarism_analyzer import PlagiarismAnalyzer
from .services.report_generator import generate_report


BASE_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "data" / "plagiarismai.db"))
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-development-secret")
ALGORITHM = "HS256"
TOKEN_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "60"))

app = FastAPI(title="PlagiarismAI API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5175",
        "http://localhost:5173",
        "http://localhost:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class TextAnalysisRequest(BaseModel):
    text: str = Field(min_length=1)
    options: dict[str, bool] = {}


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            text TEXT NOT NULL,
            file_hash TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    document_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(documents)").fetchall()
    }
    if "file_hash" not in document_columns:
        connection.execute("ALTER TABLE documents ADD COLUMN file_hash TEXT")
    for row in connection.execute(
        "SELECT id, text FROM documents WHERE file_hash IS NULL"
    ).fetchall():
        connection.execute(
            "UPDATE documents SET file_hash = ? WHERE id = ?",
            (hashlib.sha256(row["text"].encode("utf-8")).hexdigest(), row["id"]),
        )
    if "content_hash" not in document_columns:
        connection.execute("ALTER TABLE documents ADD COLUMN content_hash TEXT")
    for row in connection.execute(
        "SELECT id, text FROM documents WHERE content_hash IS NULL"
    ).fetchall():
        connection.execute(
            "UPDATE documents SET content_hash = ? WHERE id = ?",
            (hashlib.sha256(row["text"].encode("utf-8")).hexdigest(), row["id"]),
        )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            document_name TEXT,
            status TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    existing_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(analyses)").fetchall()
    }
    for column, definition in (
        ("document_id", "TEXT"),
        ("file_hash", "TEXT"),
        ("report_path", "TEXT"),
        ("report_created_at", "TEXT"),
    ):
        if column not in existing_columns:
            connection.execute(f"ALTER TABLE analyses ADD COLUMN {column} {definition}")
    connection.commit()
    return connection


def hash_password(password: str, salt: bytes | None = None) -> str:
    password_salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), password_salt, 120_000)
    return f"{password_salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded_password: str) -> bool:
    try:
        salt_hex, digest_hex = encoded_password.split("$", maxsplit=1)
        expected = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), 120_000
        ).hex()
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(expected, digest_hex)


def create_access_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)


def user_response(user: sqlite3.Row) -> dict:
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


def current_user(authorization: str | None = Header(default=None)) -> sqlite3.Row:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = jwt.decode(authorization[7:], SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from error

    connection = get_connection()
    try:
        user = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        connection.close()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return user


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/auth/register")
def register(payload: RegisterRequest) -> dict:
    name = payload.name.strip()
    email = str(payload.email).strip().lower()
    if not name:
        raise HTTPException(status_code=422, detail="Name is required")

    connection = get_connection()
    try:
        if connection.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            raise HTTPException(status_code=409, detail="An account with this email already exists")
        cursor = connection.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name, email, hash_password(payload.password), datetime.now(timezone.utc).isoformat()),
        )
        connection.commit()
        user = connection.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    finally:
        connection.close()

    return {"access_token": create_access_token(user["id"]), "token_type": "bearer", "user": user_response(user)}


@app.post("/auth/login")
def login(payload: LoginRequest) -> dict:
    email = str(payload.email).strip().lower()
    connection = get_connection()
    try:
        user = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        connection.close()
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": create_access_token(user["id"]), "token_type": "bearer", "user": user_response(user)}


@app.get("/dashboard")
def dashboard(user: sqlite3.Row = Depends(current_user)) -> dict:
    connection = get_connection()
    try:
        documents = connection.execute("SELECT COUNT(*) FROM documents WHERE user_id = ?", (user["id"],)).fetchone()[0]
        completed = connection.execute(
            "SELECT COUNT(*) FROM analyses WHERE user_id = ? AND status = 'COMPLETED'", (user["id"],)
        ).fetchone()[0]
    finally:
        connection.close()
    return {
        "user": user_response(user),
        "total_documents": documents,
        "total_analyses": completed,
        "recent_analyses": [],
    }


@app.get("/analyses")
def analyses(user: sqlite3.Row = Depends(current_user)) -> list:
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT id, document_name, status, created_at, result_json FROM analyses WHERE user_id = ? ORDER BY created_at DESC",
            (user["id"],),
        ).fetchall()
    finally:
        connection.close()
    return [
        {
            "id": row["id"],
            "document_name": row["document_name"],
            "status": row["status"],
            "created_at": row["created_at"],
            **json.loads(row["result_json"]),
        }
        for row in rows
    ]


@app.get("/analyses/{analysis_id}")
def analysis(analysis_id: str, user: sqlite3.Row = Depends(current_user)) -> dict:
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM analyses WHERE id = ? AND user_id = ?", (analysis_id, user["id"])
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} was not found")
    result = {"id": row["id"], "document_name": row["document_name"], **json.loads(row["result_json"])}
    if row["document_id"]:
        connection = get_connection()
        try:
            document = connection.execute(
                "SELECT text FROM documents WHERE id = ? AND user_id = ?", (row["document_id"], user["id"])
            ).fetchone()
        finally:
            connection.close()
        result["document_text"] = document["text"] if document else None
    return result


def _available_sources(
    connection: sqlite3.Connection,
    user_id: int,
    current_document_id: str | None = None,
    current_file_hash: str | None = None,
    current_content_hash: str | None = None,
) -> list[dict]:
    rows = connection.execute(
        "SELECT id, name, text, file_hash, content_hash FROM documents WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "text": row["text"],
            "file_hash": row["file_hash"],
            "content_hash": row["content_hash"],
        }
        for row in rows
        if row["id"] != current_document_id
        and (not current_file_hash or row["file_hash"] != current_file_hash)
        and (not current_content_hash or row["content_hash"] != current_content_hash)
    ]


def _save_analysis(
    user_id: int,
    document_name: str | None,
    text: str,
    options: dict[str, bool],
    document_id: str | None = None,
    file_hash: str | None = None,
    content_hash: str | None = None,
    metadata: dict | None = None,
) -> dict:
    connection = get_connection()
    try:
        result = PlagiarismAnalyzer().analyze(
            text,
            _available_sources(connection, user_id, document_id, file_hash, content_hash),
            options,
            current_document_id=document_id,
            current_file_hash=file_hash,
            current_content_hash=content_hash,
        )
        analysis_id = str(uuid.uuid4())
        result["id"] = analysis_id
        result["document_name"] = document_name
        result["created_at"] = datetime.now(timezone.utc).isoformat()
        result["document_metadata"] = {
            "word_count": len(text.split()),
            "character_count": len(text),
            **(metadata or {}),
        }
        result["matching_passages"] = [
            {
                "source": source.get("source_document_name"),
                "text": match.get("text", ""),
                "source_text": match.get("source_text"),
                "score": match.get("score"),
                "match_type": match.get("match_type"),
            }
            for source in result.get("source_documents", [])
            for match in source.get("exact_matches", []) + source.get("near_duplicate_matches", [])
        ]
        result["source_categories"] = {
            "internet_sources": [],
            "publications": [],
            "submitted_works": [],
            "uploaded_documents": [
                {
                    "name": source.get("source_document_name"),
                    "source_id": source.get("source_document_id"),
                    "passage_count": len(source.get("exact_matches", [])) + len(source.get("near_duplicate_matches", [])),
                }
                for source in result.get("source_documents", [])
            ],
        }
        result["match_groups"] = {
            "not_cited_or_quoted": None,
            "missing_quotations": None,
            "missing_citation": None,
            "cited_and_quoted": None,
            "availability": "Unavailable: citation and quotation analysis is not configured.",
        }
        result["filters"] = {
            "bibliography": False,
            "quoted_text": False,
            "cited_text": False,
            "small_matches": False,
            "applied": [],
        }
        result["integrity_flags"] = _integrity_flags(text)
        connection.execute(
            "INSERT INTO analyses (id, user_id, document_id, document_name, status, result_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (analysis_id, user_id, document_id, document_name, result["status"], json.dumps(result), result["created_at"]),
        )
        connection.commit()
    finally:
        connection.close()
    return result


def _integrity_flags(text: str) -> list[dict]:
    mixed_script = any("\u0400" <= character <= "\u04FF" for character in text) and any(
        "A" <= character <= "z" for character in text
    )
    if not mixed_script:
        return []
    return [{
        "category": "Mixed-script characters",
        "severity": "review",
        "location": "Document text",
        "description": "The extracted text contains both Latin and Cyrillic characters.",
        "evidence": "Character-level inspection detected mixed scripts.",
    }]


def _extract_document_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.casefold()
    if suffix == ".txt":
        return content.decode("utf-8-sig")
    if suffix == ".pdf":
        try:
            import fitz
        except ModuleNotFoundError as error:
            raise HTTPException(status_code=503, detail="PDF extraction is unavailable. Install PyMuPDF.") from error
        return "\n".join(page.get_text() for page in fitz.open(stream=content, filetype="pdf"))
    if suffix == ".docx":
        try:
            from docx import Document
        except ModuleNotFoundError as error:
            raise HTTPException(status_code=503, detail="DOCX extraction is unavailable. Install python-docx.") from error
        import io
        return "\n".join(paragraph.text for paragraph in Document(io.BytesIO(content)).paragraphs)
    raise HTTPException(status_code=415, detail="Upload a PDF, DOCX, or TXT document")


@app.post("/analyses/text")
def analyze_text(payload: TextAnalysisRequest, user: sqlite3.Row = Depends(current_user)) -> dict:
    try:
        return _save_analysis(user["id"], None, payload.text, payload.options)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/analyses/document")
async def analyze_document(
    file: UploadFile = File(...),
    options: str = Form("{}"),
    user: sqlite3.Row = Depends(current_user),
) -> dict:
    try:
        parsed_options = json.loads(options)
        if not isinstance(parsed_options, dict):
            raise ValueError("Analysis options must be an object")
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        text = _extract_document_text(file.filename or "", content)
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if not text.strip():
            raise ValueError("The uploaded document does not contain readable text")
        page_count = None
        if Path(file.filename or "").suffix.casefold() == ".pdf":
            import fitz
            page_count = len(fitz.open(stream=content, filetype="pdf"))
        document_id = str(uuid.uuid4())
        result = _save_analysis(
            user["id"],
            file.filename,
            text,
            parsed_options,
            document_id=document_id,
            file_hash=file_hash,
            content_hash=content_hash,
            metadata={
                "file_size_bytes": len(content),
                "page_count": page_count,
                "file_format": Path(file.filename or "").suffix.casefold().lstrip("."),
            },
        )
        upload_dir = BASE_DIR / "uploads" / str(user["id"])
        upload_dir.mkdir(parents=True, exist_ok=True)
        original_path = upload_dir / f"{document_id}{Path(file.filename or '').suffix.casefold()}"
        original_path.write_bytes(content)
        result["document_metadata"]["original_file_path"] = str(original_path)
        connection = get_connection()
        try:
            connection.execute(
                "UPDATE analyses SET result_json = ? WHERE id = ? AND user_id = ?",
                (json.dumps(result), result["id"], user["id"]),
            )
            connection.commit()
        finally:
            connection.close()
        connection = get_connection()
        try:
            connection.execute(
                "INSERT INTO documents (id, user_id, name, text, file_hash, content_hash, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (document_id, user["id"], file.filename or "uploaded document", text, file_hash, content_hash, datetime.now(timezone.utc).isoformat()),
            )
            connection.commit()
        finally:
            connection.close()
        return result
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=422, detail="Analysis options must be valid JSON") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/analyses/{analysis_id}/report")
def download_report(analysis_id: str, user: sqlite3.Row = Depends(current_user)) -> FileResponse:
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM analyses WHERE id = ? AND user_id = ?", (analysis_id, user["id"])
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Analysis was not found")
        result = json.loads(row["result_json"])
        document_text = ""
        if row["document_id"]:
            document = connection.execute(
                "SELECT text FROM documents WHERE id = ? AND user_id = ?", (row["document_id"], user["id"])
            ).fetchone()
            document_text = document["text"] if document else ""
        report_path = Path(row["report_path"]) if row["report_path"] else BASE_DIR / "reports" / str(user["id"]) / f"{analysis_id}.pdf"
        if not report_path.is_absolute():
            report_path = BASE_DIR / report_path
        if not report_path.exists():
            generate_report(
                report_path,
                result,
                document_text,
                datetime.now(timezone.utc),
                source_path=Path(result.get("document_metadata", {}).get("original_file_path", "")),
            )
            connection.execute(
                "UPDATE analyses SET report_path = ?, report_created_at = ? WHERE id = ? AND user_id = ?",
                (str(report_path), datetime.now(timezone.utc).isoformat(), analysis_id, user["id"]),
            )
            connection.commit()
    finally:
        connection.close()
    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=f"plagiarismai-{analysis_id}.pdf",
    )
