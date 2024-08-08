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
                response_content = response.content.decode("utf-8")
                # JSON objects are separated by a newline character
                json_strings = response_content.split('\n')

                # Convert each JSON string into a Python dictionary
                json_results = [json.loads(json_string) for json_string in json_strings if json_string.strip()]
                # Final response
                output_data = []
                for result in json_results:
                    if 'result' in result and 'results' in result.get('result'):
                        data_packet = result.get('result').get('results')
                        output_data.extend(data_packet)
                    if 'error' in result:
                        output_data.extend(result.items())
                return {"results": output_data}
            except requests.exceptions.JSONDecodeError:
                if not response.text.strip():
                    return {"success": True, "message": "No data returned"}
                else:
                    return {"success": False, "message": f"{response.text}"}
        elif response.status_code == 400:
            raise ValueError(f"Bad request error: {response.text} Failed with status code: {response.status_code}")
        elif response.status_code == 403:
            raise ValueError(f"Forbidden error: {response.text} Failed with status code: {response.status_code}")
        else:
            raise ValueError(f"Unexpected error: {response.text} Failed with status code: {response.status_code}")
