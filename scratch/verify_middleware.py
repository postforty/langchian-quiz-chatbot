import os
os.environ["GOOGLE_API_KEY"] = "dummy"

from src.guardrails import student_safety_middleware, education_guardrail, answer_leakage_guardrail
from src.utils.guardrails_wrapper import input_guardrail_node, output_guardrail_node
from src.core.state import AgentState
from langchain_core.messages import HumanMessage, AIMessage

# Mock state
state: AgentState = {
    "messages": [HumanMessage(content="Hello 010-1234-5678")],
    "mode": "질문하기",
    "pdf_context": "test",
    "pdf_processed": True,
    "current_question": None,
    "wrong_answers": [],
    "next_node": None,
    "guardrail_response": None
}

print("Testing input_guardrail_node...")
try:
    res = input_guardrail_node(state)
    print(f"Success! result: {res}")
except Exception as e:
    print(f"Failed with error: {e}")
    import traceback
    traceback.print_exc()

state["messages"].append(AIMessage(content="여기 정답입니다."))
print("\nTesting output_guardrail_node...")
try:
    res = output_guardrail_node(state)
    print(f"Success! result: {res}")
except Exception as e:
    # This might fail because it calls the model, but we want to check for TypeError first
    if "API key required" in str(e):
         print("Model call failed as expected, but no TypeError!")
    else:
         print(f"Failed with error: {e}")
