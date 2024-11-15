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
        MAX_TOKEN = int(context['params'].get('MAX TOKEN'))
    
    if isinstance(resources, dict):
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
    
    1. **action_required**: Boolean. Return `true` or `false` to indicate if automation is feasible based on `probability_score` and `confidence_score`.
    2. **probability_score**: Integer (1-100). Represents the likelihood of a successful automation based on process mining. Higher scores favor automation; lower scores suggest manual handling.
    3. **confidence_score**: Integer (0-100). Reflects how confidently assumptions were minimized; lower scores mean more assumptions were necessary.
    4. **reason**: Textual explanation detailing the basis for `probability_score` and `confidence_score`.
    5. **fields_evaluated**: List of field names (only) evaluated from the provided data.

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
    
    resources = resources[:parsable_resource_count]

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
            results =  {
                "error": "Response too large or invalid JSON format.",
                "response": str(message_content)
            }
        except Exception as e:
            results = {
                "error": str(e),
                "response": json.loads(message_content)
            }
        counter += 1
    print("Completed Evaluation with ", counter, "tries.")
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
