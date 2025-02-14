import requests

class HTTPRequestClient:
    def __init__(self, api_url: str, headers_json: dict, ignore_ssl: bool = False):
        self.api_url = api_url.rstrip('/')
        self.headers_json = headers_json
        self.ignore_ssl = ignore_ssl
        self.session = requests.Session()

    def request(self, method: str, endpoint: str, headers: dict = dict(), **kwargs):
        url = f"{self.api_url}/{endpoint.lstrip('/')}"

        preset_keys = self.headers_json.keys()
        combined_headers = {}
        for i in self.headers_json:
            combined_headers[i] = self.headers_json[i]
        
        for i in headers:
            if i not in preset_keys:
                combined_headers[i] = headers[i]

        response = self.session.request(method, url, headers=combined_headers,verify=self.ignore_ssl,**kwargs)
        return response