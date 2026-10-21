from __future__ import annotations
import json


def build_tool_results(calls: list[dict], handler) -> dict:
    """Build exactly one Vapi response entry per incoming tool-call ID.

    handler(call) must return (result_dict_or_None, error_string_or_None).
    result is always a JSON-encoded string, per the booking contract.
    """
    results = []
    for call in calls:
        tool_call_id = call.get("toolCallId", "")
        result, error = handler(call)
        if error is not None:
            results.append({"toolCallId": tool_call_id, "error": str(error)})
        else:
            results.append({"toolCallId": tool_call_id, "result": json.dumps(result or {})})
    return {"results": results}
