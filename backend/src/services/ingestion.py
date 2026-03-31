"""Módulo de ingestão e chunking semântico de logs.

Recebe arquivos de log (.log, .txt, .json), executa limpeza de ruído,
sanitização de PII e chunking semântico preservando stack traces completos.
"""

import json
import re
from typing import Optional

from fastapi import UploadFile

from backend.src.core.security import sanitize_pii
from backend.src.models.schemas import Chunk, ChunkMetadata, LogLevel

# Padrão para linhas de log com timestamp e nível
_LOG_LINE_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+"
    r"(?:\[?([A-Z]+)\]?)\s+"
    r"(.*)",
    re.MULTILINE,
)

# Padrão para detectar início de stack trace
_STACK_TRACE_START = re.compile(
    r"^(Traceback \(most recent call last\)|Exception in thread|"
    r"Caused by:|java\.\w+\.\w+Exception|"
    r"at\s+[\w.$]+\([\w.]+:\d+\)|"
    r"\w+Error:|\w+Exception:)",
    re.MULTILINE,
)

# Padrão para linhas de continuação de stack trace
_STACK_TRACE_CONTINUATION = re.compile(
    r"^\s+(File |at |\.{3}\s*\d+\s*more|Caused by:|\w+Error:|\w+Exception:|\S+\.\S+\()",
)

# Ruído: IDs de sessão únicos, UUIDs isolados, tokens hexadecimais longos
_SESSION_ID_PATTERN = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
_HEX_TOKEN_PATTERN = re.compile(r"\b[0-9a-fA-F]{32,}\b")

_VALID_LOG_LEVELS = {level.value for level in LogLevel}


def _clean_noise(text: str) -> str:
    """Remove ruído como UUIDs de sessão e tokens hexadecimais longos."""
    text = _SESSION_ID_PATTERN.sub("[SESSION_ID]", text)
    text = _HEX_TOKEN_PATTERN.sub("[TOKEN]", text)
    return text


def _detect_log_level(text: str) -> LogLevel:
    """Detecta o nível de log a partir do texto."""
    for level in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"):
        if level in text.upper():
            return LogLevel(level)
    return LogLevel.UNKNOWN


def _extract_timestamp(text: str) -> Optional[str]:
    """Extrai o primeiro timestamp encontrado no texto."""
    match = re.search(
        r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?",
        text,
    )
    return match.group(0) if match else None


def _is_stack_trace_start(line: str) -> bool:
    """Verifica se a linha inicia um stack trace."""
    stripped = line.strip()
    if not stripped:
        return False
    return bool(_STACK_TRACE_START.match(stripped))


def _is_stack_trace_continuation(line: str, in_stack_trace: bool) -> bool:
    """Verifica se a linha faz parte de um stack trace em andamento."""
    if not in_stack_trace:
        return False
    stripped = line.strip()
    if not stripped:
        return False
    # Explicit continuation patterns
    if _STACK_TRACE_CONTINUATION.match(line):
        return True
    # Indented lines inside a stack trace (code context lines)
    if line.startswith("    ") or line.startswith("\t"):
        return True
    # Error/Exception final lines (e.g. "ValueError: bad value")
    if _STACK_TRACE_START.match(stripped):
        return True
    return False


def _chunk_log_lines(lines: list[str], filename: str) -> list[Chunk]:
    """Divide linhas de log em chunks semânticos preservando stack traces."""
    chunks: list[Chunk] = []
    current_lines: list[str] = []
    in_stack_trace = False

    for line in lines:
        is_st_start = _is_stack_trace_start(line)
        is_st_cont = _is_stack_trace_continuation(line, in_stack_trace)

        if is_st_start or is_st_cont:
            in_stack_trace = True
            current_lines.append(line)
            continue

        if in_stack_trace:
            # Stack trace ended — check what this line is
            in_stack_trace = False
            stripped = line.strip()
            if not stripped:
                # Blank line after stack trace — include it and close chunk
                current_lines.append(line)
                continue
            # New log entry — flush current chunk, start new one
            if _LOG_LINE_PATTERN.match(line):
                _flush_chunk(current_lines, filename, chunks)
                current_lines = [line]
                continue
            # Other non-stack-trace line — flush and start new
            _flush_chunk(current_lines, filename, chunks)
            current_lines = [line]
            continue

        # Outside stack trace: new log entry starts a new chunk
        if _LOG_LINE_PATTERN.match(line) and current_lines:
            _flush_chunk(current_lines, filename, chunks)
            current_lines = [line]
        else:
            current_lines.append(line)

    # Flush remaining
    if current_lines:
        _flush_chunk(current_lines, filename, chunks)

    return chunks


def _flush_chunk(lines: list[str], filename: str, chunks: list[Chunk]) -> None:
    """Cria um Chunk a partir das linhas acumuladas e adiciona à lista."""
    text = "\n".join(lines).strip()
    if not text:
        return

    timestamp = _extract_timestamp(text)
    log_level = _detect_log_level(text)

    chunks.append(
        Chunk(
            text=text,
            metadata=ChunkMetadata(
                filename=filename,
                timestamp=timestamp,
                log_level=log_level,
            ),
        )
    )


def _json_entry_to_chunk(entry: dict, filename: str) -> Chunk:
    """Convert a JSON dict entry into a sanitized Chunk with metadata.

    Args:
        entry: Parsed JSON object representing a log entry.
        filename: Source filename for metadata.

    Returns:
        Chunk with sanitized text and extracted metadata.
    """
    text = json.dumps(entry, ensure_ascii=False)
    text = _clean_noise(text)
    text = sanitize_pii(text)

    timestamp = entry.get("timestamp") or entry.get("time")
    level_str = (
        entry.get("level", "")
        or entry.get("log_level", "")
        or entry.get("severity", "")
    ).upper()
    log_level = (
        LogLevel(level_str) if level_str in _VALID_LOG_LEVELS else LogLevel.UNKNOWN
    )

    return Chunk(
        text=text,
        metadata=ChunkMetadata(
            filename=filename,
            timestamp=str(timestamp) if timestamp else None,
            log_level=log_level,
        ),
    )


def _process_json_content(content: str, filename: str) -> list[Chunk]:
    """Processa conteúdo JSON — array de objetos ou JSONL."""
    chunks: list[Chunk] = []

    # Tenta como JSON array ou objeto
    try:
        data = json.loads(content)
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    chunks.append(_json_entry_to_chunk(entry, filename))
            return chunks if chunks else _fallback_single_chunk(content, filename)
        if isinstance(data, dict):
            return [_json_entry_to_chunk(data, filename)]
    except (json.JSONDecodeError, ValueError):
        pass

    # Tenta como JSONL (uma entrada JSON por linha)
    for raw_line in content.strip().splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            entry = json.loads(raw_line)
            if isinstance(entry, dict):
                chunks.append(_json_entry_to_chunk(entry, filename))
        except (json.JSONDecodeError, ValueError):
            continue

    return chunks if chunks else _fallback_single_chunk(content, filename)


def _fallback_single_chunk(content: str, filename: str) -> list[Chunk]:
    """Cria um único chunk quando o conteúdo não pode ser dividido."""
    text = _clean_noise(content.strip())
    text = sanitize_pii(text)
    if not text:
        return []
    return [
        Chunk(
            text=text,
            metadata=ChunkMetadata(
                filename=filename,
                timestamp=_extract_timestamp(text),
                log_level=_detect_log_level(text),
            ),
        )
    ]


async def process_file(file: UploadFile) -> list[Chunk]:
    """Processa um arquivo de log: limpeza, sanitização PII e chunking semântico.

    Args:
        file: Arquivo enviado via upload (UploadFile do FastAPI).

    Returns:
        Lista de Chunk com texto sanitizado e metadados extraídos.
    """
    raw_bytes = await file.read()
    content = raw_bytes.decode("utf-8", errors="replace")
    filename = file.filename or "unknown"

    if not content.strip():
        return []

    # JSON files get special handling
    if filename.lower().endswith(".json"):
        return _process_json_content(content, filename)

    # Text/log files: clean → sanitize → chunk
    content = _clean_noise(content)
    content = sanitize_pii(content)

    lines = content.splitlines()
    chunks = _chunk_log_lines(lines, filename)

    # Se o chunking não produziu resultados, retorna como chunk único
    if not chunks:
        return _fallback_single_chunk(content, filename)

    return chunks
