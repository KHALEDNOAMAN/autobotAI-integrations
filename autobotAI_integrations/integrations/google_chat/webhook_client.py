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
        if buttons and isinstance(buttons, str):
            try:
                import json
                buttons = json.loads(buttons)
            except:
                pass

        if buttons and isinstance(buttons, list):
            for button in buttons:
                if not isinstance(button, dict):
                    continue
                # Extract URL, checking multiple possible keys
                url = button.get("link") or button.get("url")
                if not url:
                    continue
                    
                # Extract label, checking multiple possible keys
                label = button.get("name") or button.get("text") or button.get("label") or "Click"
                
                btns.append(
                    {
                        "text": label,
                        "onClick": {
                            "openLink": {"url": url}
                        },
                    }
                )

        widgets = []
        if body:
            widgets.append({"textParagraph": {"text": body}})
        
        if btns:
            widgets.append({"buttonList": {"buttons": btns}})
            
        if not widgets:
            raise ValueError("Both message body and buttons are empty. Google Chat requires at least one widget.")

        section = {
            "uncollapsibleWidgetsCount": 1,
            "widgets": widgets,
        }
        if title:
            section["header"] = title

        bot_message = {
            "cardsV2": [
                {
                    "cardId": "c1",
                    "card": {
                        "header": {"title": self.header},
                        "sections": [section],
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
        
        try:
            resp = request.urlopen(req, timeout=10)
            return {
                "success": True,
                "status_code": resp.getcode(),
                "data": json.loads(resp.read().decode("utf-8"))
            }
        except request.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise Exception(f"Google Chat HTTP {e.code}: {e.reason}. Details: {error_body}")
        except Exception as e:
            raise Exception(f"Google Chat Webhook Error: {str(e)}")
