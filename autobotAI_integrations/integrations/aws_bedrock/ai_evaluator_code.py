from pydantic import BaseModel, Field
from typing import List
import json, re
from pydantic_ai.settings import ModelSettings



async def executor(context):
    agent = context["clients"]["Agent"]
    prompt = context["params"]["prompt"]
    model = context["params"]["model"]
    resources = json.loads(json.dumps(context["params"]["resources"], default=str))
    MAX_TOKEN = context['params'].get('output_token') or 8192

    if model.startswith("meta.llama3"):
        MAX_TOKEN = 2048

    if not isinstance(resources, list):
        resources = [resources]
    
    parsable_resources_count = 0
    try:
        current_words_length = 2300 + len(prompt) # prompt length
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
        resources = resources[: min(parsable_resources_count, 20)]
    class ResourceEvaluation(BaseModel):
        name: str = Field(..., description="Matches unique resource 'name' field")
        action_required: bool = Field(..., description="Whether action is required")
        probability_score: int = Field(..., ge=1, le=100, description="Probability score between 1 and 100")
        confidence_score: int = Field(..., ge=0, le=100, description="Confidence score between 0 and 100")
        reason: str = Field(..., description="Explanation for the scores")
        fields_evaluated: List[str] = Field(..., description="List of fields that were evaluated")


    system_prompt = f"""You are an AI evaluator that returns decision-making JSON data only.Given the prompt and resource list, evaluate each resource based on the following field descriptions:\n
    1. **name**: The unique name of the resource being evaluated. It should match exactly with the resource 'name' field value.\n
    2. **action_required**: A Boolean indicating whether action is advisable for the resource. Determine this based on `probability_score` and `confidence_score`. Return `true` if action is recommended; otherwise, return `false`.\n
    3. **probability_score**: An integer (1-100) representing the likelihood of a specific outcome occurring. Higher scores suggest automation or action; lower scores suggest manual intervention or no action.\n
    4. **confidence_score**: An integer (0-100) reflecting the confidence in the evaluation's accuracy. Lower scores imply that more assumptions were needed to reach the result.\n
    5. **reason**: A textual explanation justifying the `action_required` value, based on the `probability_score` and `confidence_score`.\n
    6. **fields_evaluated**: A list of the field names considered in determining the above values.\n

    Your response must be a JSON array with one object per resource, strictly following this schema: {ResourceEvaluation.model_json_schema()}

    Rules:\n
    - Return only a JSON array, structured for direct parsing using `json.loads(response)` in Python.\n
    - No extra text, symbols, or markdown.\n
    - Each object must contain all required fields."""

    user_prompt = f"""
    Resources: {resources}
    Prompt: {prompt}"""

    agent_instance = agent(model,system_prompt=system_prompt,model_settings=ModelSettings(max_tokens=MAX_TOKEN))

    # Execute agent
    result = await agent_instance.run(user_prompt)

    generated_text = result.output
    try:
        try:
            results = json.loads(generated_text)
        except json.decoder.JSONDecodeError as e:
            # Search for the first occurrence of text inside triple backticks
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", generated_text, re.DOTALL)
            if match:
                results = json.loads(match.group(1).strip())
            else:
                raise e
        return combine_resources_with_decision(resources, results)
    except Exception as e:
        return {
            "error": str(e),
            "evaluated-response": str(generated_text),
        }

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


    