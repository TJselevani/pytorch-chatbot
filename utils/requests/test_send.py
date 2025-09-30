# test_send_mock.py
from account_service import AccountService
from unittest.mock import patch, MagicMock

svc = AccountService("APIKEY", "https://sms.fake", "SENDER")

fake_resp = MagicMock()
fake_resp.status_code = 200
fake_resp.json.return_value = {"ok": True}

with patch("account_service.requests.post", return_value=fake_resp) as mock_post:
    result = svc.send_otp("+254700000000")
    print(result["message"])
    print("Sent payload:", result["sent_payload"])
    mock_post.assert_called_once()
