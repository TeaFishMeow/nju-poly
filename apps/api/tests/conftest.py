import pytest

import app.auth.service as auth_service
from app.auth.email import EmailDelivery


@pytest.fixture(autouse=True)
def mock_email_delivery(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_service, "send_verification_email", lambda *, email, code: EmailDelivery.LOCAL_DEV)
