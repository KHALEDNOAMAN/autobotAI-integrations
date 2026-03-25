import json
import re


async def executor(context):
    sample_json = """
    {
        "name": "string (matches unique resource 'name' field)",
        "action_required": "Boolean",
        "probability_score": "int (1-100)",
        "confidence_score": "int (0-100)",
        "reason": "string (explanation for scores)",
        "fields_evaluated": ["field1", "field2", "field3", ..., "fieldN"]
    }
    """

    user_prompt = f"""Generate JSON output based on the following field descriptions and instructions:
    
    1. **name**: The unique name of the resource being evaluated. It should match exactly with the resource 'name' field value.
    2. **action_required**: A Boolean indicating whether action is advisable for the resource. Determine this based on `probability_score` and `confidence_score`. Return `true` if action is recommended; otherwise, return `false`.
    3. **probability_score**: An integer (1-100) representing the likelihood of a specific outcome occurring. Higher scores suggest automation or action; lower scores suggest manual intervention or no action.
    4. **confidence_score**: An integer (0-100) reflecting the confidence in the evaluation's accuracy. Lower scores imply that more assumptions were needed to reach the result.
    5. **reason**: A textual explanation justifying the `action_required` value, based on the `probability_score` and `confidence_score`.
    6. **fields_evaluated**: A list of the field names considered in determining the above values.

    Return JSON strictly in the format of this example: {sample_json} for each prompt JSON provided. No extra text or symbols; respond with JSON output only.
    """

    agent_factory = context["clients"]["Agent"]
    prompt = context["params"]["prompt"]
    model = context["params"]["model"]

    resources = json.loads(json.dumps(context["params"]["resources"], default=str))

    MAX_TOKEN = 8192

    if not isinstance(resources, list):
        resources = [resources]

    # Handling max token limit here
    parsable_resources_count = 0
    try:
        current_words_length = 2300 + len(prompt)  # prompt length
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
        resources = resources[: min(parsable_resources_count, 10)]

    system_instruction = (
        f"You are an AI evaluator that returns decision-making JSON data only. "
        f"Given the prompt and resource list, evaluate each resource according to: {user_prompt}. "
        f"Return only a JSON array with one JSON object per resource, structured for direct parsing "
        f"using `json.loads(response)` in Python. No other text should be included."
    )

    # Build the agent using the Agent factory client (pydantic-ai pattern)
    agent = agent_factory(model, system_prompt=system_instruction)

    user_message = f"Resources: {resources}\nPrompt: {prompt}"

    count = 0
    results = None
    pattern = r"```(?:json)?(.*?)```"

    while count < 3:
        response = await agent.run(user_message)
        generated_text = str(response.output)

        try:
            try:
                results = json.loads(generated_text)
            except json.decoder.JSONDecodeError as e:
                # Search for the first occurrence of text inside triple backticks
                match = re.search(pattern, generated_text, re.DOTALL)
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
                "evaluated-response": str(generated_text),
            }
        except Exception as e:
            results = {
                "error": str(e),
                "evaluated-response": str(generated_text),
            }
        count += 1

    print(f"Evaluated on {count} iterations.")
    return results


def combine_resources_with_decision(resources, decisions):
    results = []
    if isinstance(decisions, dict):
        decisions = [decisions]
    for resource in resources:
        for decision in decisions:
            if resource["name"] == decision["name"]:
                resource["decision"] = decision
                results.append(resource)
                break
    if results:
        return results
    else:
        raise Exception("Something Went Wrong, Please try again.")
