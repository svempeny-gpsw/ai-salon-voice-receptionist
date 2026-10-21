import json

from app.services.vapi_envelope import build_tool_results


def test_one_entry_per_tool_call_id_and_string_result():
    calls = [{"toolCallId": "a", "function": "check_availability"},
             {"toolCallId": "b", "function": "book_appointment"}]

    def handler(call):
        if call["toolCallId"] == "a":
            return ({"available": True}, None)
        return (None, "Calendar booking is temporarily unavailable.")

    envelope = build_tool_results(calls, handler)
    assert [r["toolCallId"] for r in envelope["results"]] == ["a", "b"]
    assert isinstance(envelope["results"][0]["result"], str)
    assert json.loads(envelope["results"][0]["result"])["available"] is True
    assert envelope["results"][1]["error"]
