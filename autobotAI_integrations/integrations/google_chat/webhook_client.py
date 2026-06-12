import json
from urllib import request


class GoogleChatWebhookClient:
    def __init__(self, url, header):
        self.url = url
        self.header = header

    def send_raw(self, message):
        byte_encoded = json.dumps(message).encode("utf-8")
        req = request.Request(
            self.url,
            data=byte_encoded,
        )
        req.add_header("Content-Type", "application/json; charset=UTF-8")
        resp = request.urlopen(req)

    def send(self, title, body, buttons=[]):
        # NOTE: Google Chat Incoming Webhooks do NOT support `cardsV2`.
        # cardsV2 is only for OAuth Chat App API calls.
        # Webhooks support plain `text` or the legacy `cards` format.

        btns = []
        if buttons and isinstance(buttons, str):
            try:
                buttons = json.loads(buttons)
            except Exception as e:
                raise ValueError(f"Failed to parse 'buttons'. Expected a valid JSON string or list. Error: {str(e)}")

        if buttons:
            if not isinstance(buttons, list):
                raise TypeError(f"'buttons' parameter must be a list, but received {type(buttons).__name__}")
            for button in buttons:
                if not isinstance(button, dict):
                    continue
                url = button.get("link") or button.get("url")
                if not url:
                    continue
                label = button.get("name") or button.get("text") or button.get("label") or "Click"
                btns.append(
                    {
                        "textButton": {
                            "text": label,
                            "onClick": {"openLink": {"url": url}},
                        }
                    }
                )

        # Use legacy `cards` format — `cardsV2` is NOT supported by Incoming Webhooks.
        widgets = [{"textParagraph": {"text": body}}]
        if btns:
            widgets.append({"buttons": btns})

        bot_message = {
            "cards": [
                {
                    "header": {"title": self.header if self.header else title},
                    "sections": [
                        {
                            "header": title,
                            "widgets": widgets,
                        }
                    ],
                }
            ]
        }

        byte_encoded = json.dumps(bot_message).encode("utf-8")
        req = request.Request(
            self.url,
            data=byte_encoded,
        )
        req.add_header("Content-Type", "application/json; charset=UTF-8")
        try:
            resp = request.urlopen(req)
            return resp
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, "read"):
                error_msg += f". Details: {e.read().decode('utf-8')}"
            raise Exception(f"Failed to send Google Chat message: {error_msg}")
