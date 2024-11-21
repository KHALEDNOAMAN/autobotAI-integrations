import json
import traceback


def executor(context):
    openai = context["clients"]["openai"]
    prompt = context["params"]["prompt"]
    model = context["params"]["model"]
    resources = json.loads(json.dumps(context["params"]["resources"], default=str))

    # Based on model this increases or decreases i.e for gpt-4o it's 128000
    # Here we are taking safe value to support most model
    MAX_TOKEN = 8192

    if context['params'].get('MAX TOKEN'):
        if context['params'].get('MAX TOKEN') < 800:
            raise Exception("The Input Token Should be greater than 800.")
        MAX_TOKEN = int(context['params'].get('MAX TOKEN'))

    if not isinstance(resources, list):
        resources = [resources]

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
    
    1. **name**: The unique name of the resource being evaluated. It should match exactly with the resource name.
    2. **action_required**: A Boolean indicating whether action is advisable for the resource. Determine this based on `probability_score` and `confidence_score`. Return `true` if action is recommended; otherwise, return `false`.
    3. **probability_score**: An integer (1-100) representing the likelihood of a specific outcome occurring. Higher scores suggest automation or action; lower scores suggest manual intervention or no action.
    4. **confidence_score**: An integer (0-100) reflecting the confidence in the evaluation's accuracy. Lower scores imply that more assumptions were needed to reach the result.
    5. **reason**: A textual explanation justifying the `action_required` value, based on the `probability_score` and `confidence_score`.
    6. **fields_evaluated**: A list of the field names considered in determining the above values.

    Return JSON strictly in the format of this example: {sample_json} for each prompt JSON provided. No extra text or symbols; respond with JSON output only.
    """
    # Initializing prompts with an explanatory prompt for the model
    prompts = [
        {
            "role": "system",
            "content": f"You are an AI evaluator that returns decision-making JSON data only. Given the prompt and resource list, evaluate each resource according to: {user_prompt}. Return only a JSON array with one JSON object per resource, structured for direct parsing using `json.loads(response)` in Python. No other text should be included.",
        },
    ]
    prompts.append(
        {
            "role": "user",
            "content": f"Resources: ",
        }
    )
    prompts.append(
        {
            "role": "user",
            "content": f"Prompt: {prompt}",
        }
    )

    # Adding individual resources to prompts
    current_prompt_len = 1800 # for prompts
    parsable_resource_count = 0
    for resource in enumerate(resources):
        resource_len = len(str(resource))
        if current_prompt_len + resource_len < MAX_TOKEN * 3:
            prompts.append(
                {
                    "role": "user",
                    "content": json.dumps(resource, default=str),
                }
            )
            current_prompt_len += resource_len
            parsable_resource_count += 1
            continue
        break

    resources = resources[:min(parsable_resource_count, 10)]

    # Final signal to process resources
    prompts.append(
        {
            "role": "user",
            "content": "All resources are provided; return a JSON array of results for each resource in order.",
        }
    )

    # Retry mechanism to handle transient issues
    counter = 0
    results = None
    while counter < 3:  # 3 Retries
        chat_completion = openai.chat.completions.create(
            messages=prompts,
            model=model,
        )
        try:
            message_content = chat_completion.choices[0].message.content
            print(message_content)
            if message_content:
                if message_content.startswith('```json') and message_content.endswith('```'):
                    message_content = message_content.strip('```').strip('json')
                results = json.loads(message_content)
                return combine_resources_with_decision(resources, results)
        except json.decoder.JSONDecodeError as e:
            results = {
                "error": "Response too large or invalid JSON format.",
                "evaluated-response": str(message_content),
            }
        except Exception as e:
            results = {
                "error": str(e),
                "evaluated-response": json.loads(message_content),
            }
        counter += 1
    print("Completed Evaluation with ", counter, "tries.")
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
