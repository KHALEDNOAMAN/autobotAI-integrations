import requests
import json


class CoralogixClient():
    def __init__(self, api_url: str, api_key: str) -> None:
        self.api_url = api_url
        self.api_key = api_key

    def run_query(self, query: str = None, metadata: dict = None) -> dict:
        """
        Run a query against the Coralogix API.

        :param query: The query to run.
        :param metadata: Metadata to include in the query.
        :return: The result of the query.
        """
        if not query:
            raise ValueError("Query is required")

        body = {
            "query": str(query)
        }

        if metadata:
            body["metadata"] = metadata

        response = requests.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            data=json.dumps(body)
        )

        if response.status_code == 200:
            try:
                result = response.json()
                return result
            except requests.exceptions.JSONDecodeError:
                return {"success": True, "message": "No data returned"}
        elif response.status_code == 400:
            raise ValueError(f"Bad request error: {response.text} Failed with status code: {response.status_code}")
        elif response.status_code == 403:
            raise ValueError(f"Forbidden error: {response.text} Failed with status code: {response.status_code}")
        else:
            raise ValueError(f"Unexpected error: {response.text} Failed with status code: {response.status_code}")
