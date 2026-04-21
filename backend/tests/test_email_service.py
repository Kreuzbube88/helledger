import pytest
from app.services.email import _build_reset_email, _build_invite_email


def test_reset_email_de():
    subj, body_text, body_html = _build_reset_email("de", "https://app.example.com/#/reset?token=abc")
    assert "abc" in body_text
    assert "Passwort" in subj


def test_reset_email_en():
    subj, body_text, body_html = _build_reset_email("en", "https://app.example.com/#/reset?token=abc")
    assert "abc" in body_text
    assert "Password" in subj


def test_invite_email_de():
    subj, body_text, body_html = _build_invite_email("de", "Test Haushalt", "https://app.example.com/#/register?invite=xyz")
    assert "xyz" in body_text
    assert "Haushalt" in body_text


def test_invite_email_en():
    subj, body_text, body_html = _build_invite_email("en", "Test Household", "https://app.example.com/#/register?invite=xyz")
    assert "xyz" in body_text
    assert "Household" in body_text
