# app/schemas/llm_parse_sim.py

import json
from pydantic import ValidationError
from app.schemas.Patients import Patient
from app.schemas.Medical_Records import MedicalRecord

# -------------------------------------------------------------------
# Simulating what an LLM returns — a raw string that looks like JSON.
# In production, this comes from response.choices[0].message.content
# or from Claude's text block. It's always a string first.
# -------------------------------------------------------------------

# Scenario 1: Perfect response — everything valid
llm_output_valid = """
{
    "patient": {
        "age": 34,
        "status": "active",
        "height": 170.5,
        "discharged": false
    },
    "diagnosis": "Viral fever",
    "treatment": "Rest and hydration"
}
"""

# Scenario 2: LLM gets the type wrong — age comes back as a string
llm_output_wrong_type = """
{
    "patient": {
        "age": "thirty four",
        "status": "active",
        "height": 170.5,
        "discharged": false
    },
    "diagnosis": "Viral fever",
    "treatment": "Rest and hydration"
}
"""

# Scenario 3: LLM omits a required field — discharged is missing
llm_output_missing_field = """
{
    "patient": {
        "age": 34,
        "status": "active",
        "height": 170.5
    },
    "diagnosis": "Viral fever",
    "treatment": "Rest and hydration"
}
"""

# Scenario 4: LLM hallucinates a field that doesn't exist in your schema
llm_output_hallucinated_field = """
{
    "patient": {
        "age": 34,
        "status": "active",
        "height": 170.5,
        "discharged": false,
        "insurance_provider": "HDFC Ergo"
    },
    "diagnosis": "Viral fever",
    "treatment": "Rest and hydration"
}
"""


def parse_llm_output(raw: str, scenario_name: str):
    print(f"\n{'='*50}")
    print(f"Scenario: {scenario_name}")
    print(f"{'='*50}")

    try:
        # Step 1: Parse the raw string into a Python dict
        # This is where you'd catch malformed JSON from the LLM
        data = json.loads(raw)

        # Step 2: Validate the dict against your Pydantic schema
        # model_validate is the correct v2 method for this — not the constructor
        record = MedicalRecord.model_validate(data)

        print("SUCCESS — parsed record:")
        print(record.model_dump(mode='json'))

    except json.JSONDecodeError as e:
        # LLM returned something that isn't even valid JSON
        print(f"JSON PARSE ERROR: {e}")

    except ValidationError as e:
        # Valid JSON, but doesn't match your schema
        print(f"VALIDATION ERROR — {e.error_count()} error(s):")
        for error in e.errors():
            print(f"  Field : {' -> '.join(str(l) for l in error['loc'])}")
            print(f"  Issue : {error['msg']}")
            print(f"  Got   : {error.get('input')}")


# Run all scenarios
parse_llm_output(llm_output_valid, "Valid LLM response")
parse_llm_output(llm_output_wrong_type, "Wrong type (age as string)")
parse_llm_output(llm_output_missing_field, "Missing required field (discharged)")
parse_llm_output(llm_output_hallucinated_field, "Hallucinated field (insurance_provider)")