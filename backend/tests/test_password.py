import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-chars!!")
os.environ.setdefault("TESTING", "true")

from app.auth.password import hash_password, verify_password


def test_hash_differs_from_plaintext():
    assert hash_password("mysecretpassword") != "mysecretpassword"


def test_verify_correct():
    h = hash_password("correct-password-12")
    assert verify_password("correct-password-12", h) is True


def test_verify_wrong():
    h = hash_password("correct-password-12")
    assert verify_password("wrong-password-12!", h) is False
