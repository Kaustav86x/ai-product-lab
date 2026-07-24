# Day 2 — Pydantic v2: Schema Design for Production AI Systems

## Why Pydantic in a production AI stack

In a service-company backend, validation is often an afterthought — a few `if` checks before a DB write. In an AI product, validation is structural. LLMs return probabilistic text. That text needs to be coerced into typed, constrained, predictable data before it touches any downstream system. Pydantic v2 is where that contract lives.

This session wasn't about learning a validation library. It was about understanding where business rules, data contracts, and LLM output parsing converge in a single layer.

---

## What was built

A schema layer for a healthtech context consisting of:

- A `Patient` entity with strict field-level and cross-field validation
- A `MedicalRecord` entity nesting `Patient` — demonstrating recursive validation
- An LLM response simulation harness that stress-tests the schema layer against realistic failure modes

---

## Decisions made and why

### Enums in a separate `enums.py`

Patient status (`active`, `inactive`, `discharged`) was defined as a Python `Enum` in its own file rather than inline. As the schema layer grows, enums get reused across multiple models. Keeping them isolated prevents circular imports and gives a single source of truth for valid states — a requirement in any system where status transitions carry business or clinical meaning.

### `BeforeValidator` for age — and why it must be type-defensive

Age validation uses `BeforeValidator` rather than `field_validator`. The distinction matters: `BeforeValidator` runs before Pydantic's type coercion system. This means the raw input arrives unprocessed — it could be a string, `None`, or a float depending on what the LLM returned.

The validator was initially written assuming integer input:

```python
def age_validator(age: int) -> int:
    if age < 0:
        raise ValueError(...)
```

This broke when the LLM returned `"thirty four"` — Python raised a `TypeError` on `"thirty four" < 0` because Pydantic's type system hadn't run yet. The fix was to make the validator explicitly defensive:

```python
def age_validator(age) -> int:
    if not isinstance(age, (int, float)):
        raise ValueError(f"Age must be a number, got {type(age).__name__}")
    if age < 0:
        raise ValueError("Age must be a non-negative integer.")
    return int(age)
```

Production lesson: anything that runs before type coercion must treat input as untyped. In an LLM context, this is always the case.

### `field_validator` vs `model_validator` — the boundary

`field_validator` operates on a single field in isolation. The rule is intrinsic to that field regardless of the rest of the model. Age range is a good example — it doesn't need to know anything about `status` or `discharged`.

`model_validator` operates on the fully assembled model instance. It's for rules that involve relationships between fields. In this case: if a patient's status is `active`, they cannot be marked as discharged. Neither field alone can enforce that — only the model can.

```python
@model_validator(mode='after')
def patient_status_validation(self):
    if self.status == PatientStatus.ACTIVE:
        self.discharged = False
    return self
```

The `mode='after'` means all fields are already validated and coerced before this runs. The validator overrides `discharged` based on `status` — enforcing a state consistency rule that would otherwise require application-layer logic scattered across multiple endpoints.

### Nesting `Patient` inside `MedicalRecord`

Validation is recursive by default. When `MedicalRecord.model_validate(data)` is called with a nested `patient` dict, Pydantic hands that dict off to the `Patient` model — running every `Patient` validator, including `BeforeValidator` and `model_validator`, before the `MedicalRecord` itself is considered valid.

This means the schema layer catches invalid patient data regardless of where `MedicalRecord` is instantiated — in a route handler, a background task, or an LLM output parser. The guarantee is structural, not dependent on calling code.

### `model_dump(exclude_unset=True)` — why this matters in practice

`model_dump()` by default includes every field, including those filled by defaults. `exclude_unset=True` returns only fields explicitly provided at instantiation.

This is the correct pattern for PATCH operations and for returning LLM-structured output back to a database — you don't want to overwrite existing DB values with schema defaults just because the LLM didn't mention a field. `exclude_unset` is the safeguard.

---

## LLM simulation — what was tested and what it revealed

Four scenarios were run against `MedicalRecord.model_validate()`:

**Valid response** — clean parse, recursive validation passed, `model_dump(mode='json')` returned JSON-serialisable types including enum values as strings.

**Wrong type (age as string)** — caught at `patient -> age` with a clear error message before touching any application logic. The full nested field path in the error (`patient -> age`) is what makes this debuggable in production logs.

**Missing required field** — `patient -> discharged` flagged as `Field required`. The LLM simply omitted it. The schema caught it before the record could be written anywhere.

**Hallucinated field** — `insurance_provider` was silently dropped. Parse succeeded. This is Pydantic's default `extra='ignore'` behaviour.

The hallucinated field scenario is the one that requires an active decision in production. Silent field dropping is acceptable in some contexts — but in a clinical system where an unexpected field might indicate a schema mismatch or a model responding to the wrong prompt version, `extra='forbid'` may be the safer default. This would be a configuration decision made per-model based on the risk profile of the feature.

---

## Bugs hit and what they revealed

**`@model_validator` defined outside the class** — Python executed it as a standalone decorator call at module level. The fix was indentation. The lesson: decorators in Python apply to whatever follows them in the current scope. Class method decorators must be inside the class body.

**Test instantiation code running on import** — instantiation code written at module level executed every time the schema file was imported. The fix was wrapping it in `if __name__ == "__main__"`. Schema files are contracts — they should contain definitions only. Any code that exercises those definitions belongs either in a test file or behind the `__main__` guard.

**`PatientStatus == "active"` always evaluating to `False`** — comparing the enum class itself to a string rather than comparing an instance's value. The correct form is `self.status == PatientStatus.ACTIVE`. A small syntax error with significant logical consequences — the validator was silently doing nothing.

---

## What this maps to in production

Every pattern exercised here has a direct production equivalent:

- Enum-constrained status fields → state machine integrity without application-layer enforcement
- `BeforeValidator` with type defensiveness → LLM output parsing where input type cannot be assumed
- `model_validator` for cross-field rules → business logic encoded in the contract layer, not scattered across endpoints
- Recursive model nesting → a single `model_validate` call validates an entire document graph
- `extra='ignore'` vs `extra='forbid'` → a risk-based configuration decision per feature, not a library default to accept uncritically
- `exclude_unset` → safe partial updates without clobbering existing data
