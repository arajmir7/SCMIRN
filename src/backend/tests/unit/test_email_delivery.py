import http.client
import ssl

import pytest

from app.infrastructure.external import email_delivery


class _Response:
    def __init__(self, status=202, message_id="synthetic-message-id"):
        self.status = status
        self.message_id = message_id

    def getheader(self, name):
        assert name == "X-Message-Id"
        return self.message_id


class _Connection:
    instances = []
    response = _Response()
    request_error = None

    def __init__(self, host, *, timeout, context):
        self.host = host
        self.timeout = timeout
        self.context = context
        self.request_args = None
        self.closed = False
        self.instances.append(self)

    def request(self, method, path, *, body, headers):
        self.request_args = (method, path, body, headers)
        if self.request_error:
            raise self.request_error

    def getresponse(self):
        return self.response

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def reset_fake_connection(monkeypatch):
    _Connection.instances = []
    _Connection.response = _Response()
    _Connection.request_error = None
    monkeypatch.setattr(email_delivery.http.client, "HTTPSConnection", _Connection)


def _send():
    return email_delivery._send_via_sendgrid(
        api_key="synthetic-test-token",
        from_email="sender@example.test",
        recipient="citizen@example.test",
        subject="Synthetic test message",
        body_text="No real message is sent by this test.",
        attachment_bytes=None,
        attachment_filename=None,
    )


def test_sendgrid_uses_fixed_tls_origin_and_non_redirecting_https_connection():
    assert _send() == "synthetic-message-id"

    connection = _Connection.instances[0]
    assert connection.host == "api.sendgrid.com"
    assert connection.timeout == 20
    assert isinstance(connection.context, ssl.SSLContext)
    assert connection.context.verify_mode == ssl.CERT_REQUIRED
    assert connection.context.check_hostname is True
    method, path, _body, headers = connection.request_args
    assert (method, path) == ("POST", "/v3/mail/send")
    assert headers["Authorization"] == "Bearer synthetic-test-token"
    assert connection.closed


def test_sendgrid_rejects_redirect_or_error_status_without_reflecting_provider_body():
    _Connection.response = _Response(status=302)

    with pytest.raises(email_delivery.EmailDeliveryError, match="status 302") as error:
        _send()

    assert "citizen@example.test" not in str(error.value)
    assert _Connection.instances[0].closed


def test_sendgrid_connection_errors_are_sanitized_and_closed():
    _Connection.request_error = OSError("synthetic network detail")

    with pytest.raises(email_delivery.EmailDeliveryError, match="connectivity error") as error:
        _send()

    assert "synthetic network detail" not in str(error.value)
    assert _Connection.instances[0].closed
