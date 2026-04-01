"""Unit tests for core/security.py — PII sanitization."""


from src.core.security import sanitize_pii


class TestSanitizeCPF:
    """Tests for CPF masking."""

    def test_masks_single_cpf(self):
        assert sanitize_pii("CPF: 123.456.789-00") == "CPF: [CPF_MASCARADO]"

    def test_masks_multiple_cpfs(self):
        text = "user1=111.222.333-44 user2=555.666.777-88"
        result = sanitize_pii(text)
        assert result.count("[CPF_MASCARADO]") == 2
        assert "111.222.333-44" not in result
        assert "555.666.777-88" not in result

    def test_does_not_mask_partial_cpf(self):
        """Incomplete CPF patterns should remain untouched."""
        text = "code 123.456.789 is not a CPF"
        assert sanitize_pii(text) == text


class TestSanitizeEmail:
    """Tests for e-mail masking."""

    def test_masks_simple_email(self):
        assert sanitize_pii("contact: user@example.com") == "contact: [EMAIL_MASCARADO]"

    def test_masks_email_with_dots_and_plus(self):
        result = sanitize_pii("first.last+tag@sub.domain.co")
        assert result == "[EMAIL_MASCARADO]"

    def test_masks_multiple_emails(self):
        text = "from a@b.com to c@d.org"
        result = sanitize_pii(text)
        assert result.count("[EMAIL_MASCARADO]") == 2

    def test_does_not_mask_at_sign_alone(self):
        text = "value @ position 5"
        assert sanitize_pii(text) == text


class TestSanitizePassword:
    """Tests for password masking."""

    def test_masks_password_equals(self):
        result = sanitize_pii("password=s3cret123")
        assert result == "password=[SENHA_MASCARADA]"
        assert "s3cret123" not in result

    def test_masks_senha_colon(self):
        result = sanitize_pii("senha: minha_senha_forte")
        assert result == "senha: [SENHA_MASCARADA]"

    def test_masks_pwd_equals(self):
        result = sanitize_pii("pwd=abc")
        assert result == "pwd=[SENHA_MASCARADA]"

    def test_masks_secret_equals(self):
        result = sanitize_pii("SECRET=top_secret_value")
        assert result == "SECRET=[SENHA_MASCARADA]"

    def test_masks_token_equals(self):
        result = sanitize_pii("token=eyJhbGciOiJIUzI1NiJ9")
        assert result == "token=[SENHA_MASCARADA]"

    def test_case_insensitive(self):
        result = sanitize_pii("PASSWORD=MyPass")
        assert "[SENHA_MASCARADA]" in result
        assert "MyPass" not in result


class TestSanitizeMixed:
    """Tests with multiple PII types in the same text."""

    def test_masks_all_pii_types(self):
        text = (
            "User 123.456.789-00 logged in with email admin@corp.com "
            "using password=hunter2"
        )
        result = sanitize_pii(text)
        assert "[CPF_MASCARADO]" in result
        assert "[EMAIL_MASCARADO]" in result
        assert "[SENHA_MASCARADA]" in result
        assert "123.456.789-00" not in result
        assert "admin@corp.com" not in result
        assert "hunter2" not in result

    def test_no_pii_returns_unchanged(self):
        text = "2024-01-15 INFO Application started successfully"
        assert sanitize_pii(text) == text

    def test_empty_string(self):
        assert sanitize_pii("") == ""

    def test_password_value_containing_email(self):
        """When a password value looks like an email, the password pattern
        should mask the whole value first."""
        result = sanitize_pii("password=user@example.com")
        assert "user@example.com" not in result
        assert "[SENHA_MASCARADA]" in result
