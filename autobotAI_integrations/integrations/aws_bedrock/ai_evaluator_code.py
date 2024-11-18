import json
import re


def executor(context):
    sample_json = """
    {
        "name": "string (matches unique resource name)",
        "action_required": "Boolean",
        "probability_score": "int (1-100)",
        "confidence_score": "int (0-100)",
        "reason": "string (explanation for scores)",
        "fields_evaluated": ["field1", "field2", "field3", ..., "fieldN"]
    }
    """

    user_prompt = f"""Generate JSON output based on the following field descriptions and instructions:
    
    1. **action_required**: Boolean. Return `true` or `false` to indicate if automation is feasible based on `probability_score` and `confidence_score`.
    2. **probability_score**: Integer (1-100). Represents the likelihood of a successful automation based on process mining. Higher scores favor automation; lower scores suggest manual handling.
    3. **confidence_score**: Integer (0-100). Reflects how confidently assumptions were minimized; lower scores mean more assumptions were necessary.
    4. **reason**: Textual explanation detailing the basis for `probability_score` and `confidence_score`.
    5. **fields_evaluated**: List of field names (only) evaluated from the provided data.

    Return JSON strictly in the format of this example: {sample_json} for each prompt JSON provided. No extra text or symbols; respond with JSON output only.
    """

    client = context["clients"]["bedrock-runtime"]
    prompt = context["params"]["prompt"]
    model = context["params"]["model"]
    resources = json.loads(json.dumps(context["params"]["resources"], default=str))

    MAX_TOKEN = 8192  # for meta llama 70b
    if context["params"].get("MAX TOKEN"):
        MAX_TOKEN = int(context["params"].get("MAX TOKEN"))

    if not isinstance(resources, list):
        resources = [resources]

    # Handling max token limit here
    parsable_resources_count = 0
    try:
        current_words_length = 1800  # prompt length
        for resource in resources:
            resource_len = len(str(resource))
            if resource_len + current_words_length < MAX_TOKEN * 3:
                parsable_resources_count += 1
                current_words_length += resource_len
                continue
            break
    except:
        pass
    else:
        resources = resources[:parsable_resources_count]

    final_prompt = f"""
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an AI evaluator that returns decision-making JSON data only. Given the
prompt and resource list, evaluate each resource according to: {user_prompt}.
Return only a JSON array with one JSON object per resource, structured for
direct parsing using `json.loads(response)` in Python. No other text should be
included.

<|eot_id|><|start_header_id|>user<|end_header_id|>

Resources: {resources}

Prompt: {prompt}

<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

    native_request = {
        "prompt": final_prompt,
        "max_gen_len": 2048,
    }

    request = json.dumps(native_request)
    count = 0
    results = None
    pattern = r"```(.*?)```"

    while count < 3:
        response = client.invoke_model(modelId=model, body=request)
        model_output = json.loads(response["body"].read())
        try:
            try:
                results = json.loads(model_output["generation"])
            except json.decoder.JSONDecodeError as e:
                # Search for the first occurrence of text inside triple backticks
                match = re.search(pattern, model_output["generation"], re.DOTALL)
                # If a match is found, try to parse it as JSON
                if match:
                    json_content = match.group(1).strip()
                    results = json.loads(json_content)
                else:
                    raise e
            return combine_resources_with_decision(resources, results)
        except json.decoder.JSONDecodeError as e:
            results = {
                "error": "Response too large or invalid JSON format.",
                "response": str(model_output["generation"]),
            }
        except Exception as e:
            results = {
                "error": str(e),
                "response": json.loads(model_output["generation"]),
            }
        count += 1
    print(f"Evaluated on {count} iterations.")
    return results


def combine_resources_with_decision(resources, decisions):
    if len(decisions) != len(resources):
        raise Exception(
            f"Number of decisions: {len(decisions)} and resources: {len(resources)} are not equal"
        )
    if isinstance(resources, dict):
        resources = [resources]
    for resource in resources:
        for decision in decisions:
            if resource["name"] == decision["name"]:
                resource["decision"] = decision
                break
    return resources
