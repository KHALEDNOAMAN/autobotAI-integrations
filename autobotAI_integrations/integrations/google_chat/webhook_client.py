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

        btns = []
        if buttons and isinstance(buttons, list):
            for button in buttons:
                btns.append(
                    {
                        "text": button["name"],
                        "onClick": {
                            "openLink": {"url": button.get("link", button.get("url"))}
                        },
                    }
                )

        bot_message = {
            "cardsV2": [
                {
                    "cardId": "c1",
                    "card": {
                        "header": {"title": self.header},
                        "sections": [
                            {
                                "header": title,
                                "uncollapsibleWidgetsCount": 1,
                                "widgets": [
                                    {"textParagraph": {"text": body}},
                                    {"buttonList": {"buttons": btns}},
                                ],
                            }
                        ],
                    },
                }
            ]
        }

        byte_encoded = json.dumps(bot_message).encode("utf-8")
        req = request.Request(
            self.url,
            data=byte_encoded,
        )
        req.add_header("Content-Type", "application/json; charset=UTF-8")
        resp = request.urlopen(req)
        return resp
