"""Property-based test for PII sanitization.

Feature: semantic-log-explorer, Property 5: Sanitização de PII remove todos os dados sensíveis

For any text containing PII patterns (CPFs in XXX.XXX.XXX-XX format, e-mail
addresses, or passwords), after sanitization the resulting text must not
contain any sensitive data in clear text and must contain the corresponding
markers ([CPF_MASCARADO], [EMAIL_MASCARADO], [SENHA_MASCARADA]).
"""

import re

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from backend.src.core.security import sanitize_pii


# ---------------------------------------------------------------------------
# Strategies — generators for PII values
# ---------------------------------------------------------------------------

_cpf_strategy = st.from_regex(r"\d{3}\.\d{3}\.\d{3}-\d{2}", fullmatch=True)

_email_user = st.from_regex(r"[a-zA-Z][a-zA-Z0-9_.+]{0,15}", fullmatch=True)
_email_domain = st.from_regex(r"[a-zA-Z][a-zA-Z0-9]{0,10}", fullmatch=True)
_email_tld = st.sampled_from(["com", "org", "net", "io", "br", "dev"])
_email_strategy = st.builds(
    lambda u, d, t: f"{u}@{d}.{t}", _email_user, _email_domain, _email_tld
)

_password_key = st.sampled_from(["password", "passwd", "pwd", "senha", "secret", "token"])
_password_sep = st.sampled_from(["=", ": ", "="])
_password_val = st.from_regex(r"[A-Za-z0-9_!@#$%]{3,20}", fullmatch=True)
_password_strategy = st.builds(
    lambda k, s, v: f"{k}{s}{v}", _password_key, _password_sep, _password_val
)

_filler = st.from_regex(r"[A-Za-z0-9 ]{0,30}", fullmatch=True)


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------

@settings(max_examples=200)
@given(
    cpf=_cpf_strategy,
    email=_email_strategy,
    password_entry=_password_strategy,
    prefix=_filler,
    middle1=_filler,
    middle2=_filler,
    suffix=_filler,
)
def test_sanitize_pii_removes_all_sensitive_data(
    cpf: str,
    email: str,
    password_entry: str,
    prefix: str,
    middle1: str,
    middle2: str,
    suffix: str,
) -> None:
    """Property 5: after sanitization no raw PII remains and markers are present."""
    text = f"{prefix} {cpf} {middle1} {email} {middle2} {password_entry} {suffix}"

    result = sanitize_pii(text)

    # CPF must be masked
    assert cpf not in result, f"CPF {cpf!r} still present in result"
    assert "[CPF_MASCARADO]" in result

    # E-mail must be masked
    assert email not in result, f"Email {email!r} still present in result"
    assert "[EMAIL_MASCARADO]" in result

    # Password value must be masked
    assert "[SENHA_MASCARADA]" in result

    # No raw CPF pattern should survive
    assert not re.search(r"\d{3}\.\d{3}\.\d{3}-\d{2}", result)
