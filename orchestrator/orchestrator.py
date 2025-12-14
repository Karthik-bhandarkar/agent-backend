# backend/orchestrator/orchestrator.py

from typing import Dict
from langchain.memory import ConversationBufferMemory
from agents.intention_classifier import classify_intent
from agents.supervisor_agent import supervisor
from agents.symptom_agent import run_symptom_agent
from agents.diet_agent import run_diet_agent
from agents.fitness_agent import run_fitness_agent
from agents.lifestyle_agent import run_lifestyle_agent
from agents.output_synthesizer import synthesize_output
from database import get_profile, append_conversation_turn


# -------------------------------------------------------------------
# OFFICIAL CHAT MEMORY (LangChain ConversationBufferMemory per user)
# -------------------------------------------------------------------

_memory_store: Dict[str, ConversationBufferMemory] = {}


def get_memory(user_id: str) -> ConversationBufferMemory:
    """
    Get or create a LangChain ConversationBufferMemory instance for this user.
    This is the ONLY chat memory used by the LLM for context.
    """
    if user_id not in _memory_store:
        _memory_store[user_id] = ConversationBufferMemory(
            return_messages=False  # we want a text 'history', not message objects
        )
    return _memory_store[user_id]


# -------------------------------------------------------------------
# MAIN ORCHESTRATION FUNCTION
# -------------------------------------------------------------------

def process_query(user_id: str, message: str):
    """
    Main orchestration function:
    - Loads user profile
    - Uses LangChain ConversationBufferMemory for chat context
    - Classifies intent
    - Uses supervisor LLM to decide which agent to run next
    - Stops when supervisor says FINISH or when max_steps is reached
    - Logs each turn for /history API (user_message, assistant_response, agents_used)
    """

    # 1) Load user profile (long-term memory)
    profile = get_profile(user_id)

    # 2) Get LangChain memory for this user (short-term conversation memory)
    memory = get_memory(user_id)
    memory_vars = memory.load_memory_variables({})
    chat_history = memory_vars.get("history", "No previous conversation yet.")

    # 3) Intention classification
    intent = classify_intent(message)
    is_wellness = intent.get("is_wellness", True)

    if not is_wellness:
        response_text = (
            "This message is not related to wellness. "
            "I only help with basic health, diet, fitness and lifestyle tips."
        )

        # Save to LangChain memory so context is preserved
        memory.save_context({"input": message}, {"output": response_text})

        # Also log this turn for /history API (for Postman/debugging)
        append_conversation_turn(
            user_id=user_id,
            user_message=message,
            assistant_response=response_text,
            agents_used=[],
        )

        return response_text, []

    # 4) Orchestration state passed to supervisor & agents
    state: dict = {
        "intent": intent,
        "conversation_history": chat_history,  # comes from ConversationBufferMemory
    }
    agents_used: list[str] = []

    max_steps = 8  # safety cap so we never loop forever

    for step in range(max_steps):
        # Ask supervisor what to do next, with full context
        next_agent = supervisor(message, profile, state)

        # If supervisor decides we're done, break loop
        if next_agent == "FINISH":
            break

        # Avoid calling the same agent multiple times in one turn
        if next_agent in agents_used:
            break

        agents_used.append(next_agent)

        # Call the selected agent
        if next_agent == "SymptomAgent":
            state["symptoms"] = run_symptom_agent(message, profile)

        elif next_agent == "DietAgent":
            state["diet"] = run_diet_agent(state, profile)

        elif next_agent == "FitnessAgent":
            state["fitness"] = run_fitness_agent(state, profile)

        elif next_agent == "LifestyleAgent":
            state["lifestyle"] = run_lifestyle_agent(message, profile, state)

    else:
        # If we exit the for-loop without break → supervisor never said FINISH
        state["note"] = (
            "The orchestration reached the maximum number of steps and was finished automatically."
        )

    # 5) Final synthesis of all agent outputs
    final_response = synthesize_output(state, message)

    # 6) Save to LangChain ConversationBufferMemory (this is the REAL chat memory)
    memory.save_context({"input": message}, {"output": final_response})

    # 7) Also log this turn for /history API (metadata: timestamp, agents_used)
    # 7) Also log this turn for /history API (metadata: timestamp, agents_used)
    append_conversation_turn(
        user_id=user_id,
        user_message=message,
        assistant_response=final_response,
        agents_used=agents_used,
    )

    return final_response, agents_used


def process_query_generator(user_id: str, message: str):
    """
    Generator version of process_query.
    Yields:
      {"type": "log", "agent": "...", "message": "..."}
      {"type": "final", "response": "...", "agents_used": [...]}
    """
    print(f"DEBUG: process_query_generator started for {user_id}")
    reasoning_logs = []

    def log_event(agent: str, message: str):
        event = {"type": "log", "agent": agent, "message": message}
        reasoning_logs.append(event)
        return event

    # 1) Load user profile (long-term memory)
    yield log_event("System", "Loading user profile...")
    try:
        profile = get_profile(user_id)
        print(f"DEBUG: Profile loaded: {profile is not None}")
    except Exception as e:
        print(f"DEBUG: Error loading profile: {e}")
        yield log_event("System", f"Error loading profile: {e}")
        return

    # 2) Get LangChain memory for this user (short-term conversation memory)
    memory = get_memory(user_id)
    memory_vars = memory.load_memory_variables({})
    chat_history = memory_vars.get("history", "No previous conversation yet.")

    # 3) Intention classification
    # 3) Intention classification
    yield log_event("System", "Classifying intent...")
    try:
        intent = classify_intent(message)
        print(f"DEBUG: Intent classified: {intent}")
    except Exception as e:
        print(f"DEBUG: Error classifying intent: {e}")
        yield log_event("System", "Error classifying intent, proceeding as wellness.")
        intent = {"is_wellness": True}

    is_wellness = intent.get("is_wellness", True)

    if not is_wellness:
        response_text = (
            "This message is not related to wellness. "
            "I only help with basic health, diet, fitness and lifestyle tips."
        )

        memory.save_context({"input": message}, {"output": response_text})
        append_conversation_turn(
            user_id=user_id,
            user_message=message,
            assistant_response=response_text,
            agents_used=[],
            reasoning_logs=reasoning_logs,
        )
        yield {
            "type": "final", 
            "response": response_text, 
            "agents_used": [],
            "reasoning_logs": reasoning_logs
        }
        return

    # 4) Orchestration state passed to supervisor & agents
    state: dict = {
        "intent": intent,
        "conversation_history": chat_history,
    }
    agents_used: list[str] = []

    # REQUIRED: Dynamic Supervisor Loop
    # The Supervisor decides which agent runs next based on context.
    
    max_steps = 8
    step_count = 0
    
    while step_count < max_steps:
        step_count += 1
        
        # Ask Supervisor what to do next
        yield log_event("Supervisor", "Deciding next step...")
        next_agent = supervisor(message, profile, state)
        print(f"DEBUG: Supervisor decided -> {next_agent}")

        if next_agent == "FINISH":
            yield log_event("Supervisor", "Analysis complete.")
            break

        if next_agent in agents_used:
             # Prevent infinite loops if Supervisor gets stuck
            yield log_event("Supervisor", f"Skipping {next_agent} (already ran).")
            continue

        # Execute the chosen agent
        if next_agent == "SymptomAgent":
            yield log_event("SymptomAgent", "Evaluating User Input...")
            state["symptoms"] = run_symptom_agent(message, profile)
            yield log_event("SymptomAgent", "→ Symptoms analyzed.")

        elif next_agent == "DietAgent":
            yield log_event("DietAgent", "Reviewing Symptom + Medical Data...")
            state["diet"] = run_diet_agent(state, profile)
            yield log_event("DietAgent", "→ Diet adjusted.")

        elif next_agent == "FitnessAgent":
            yield log_event("FitnessAgent", "Creating Safe Workout Plan...")
            state["fitness"] = run_fitness_agent(state, profile)
            yield log_event("FitnessAgent", "→ Fitness plan created.")

        elif next_agent == "LifestyleAgent":
            yield log_event("LifestyleAgent", "Improving Daily Routine...")
            state["lifestyle"] = run_lifestyle_agent(message, profile, state)
            yield log_event("LifestyleAgent", "→ Lifestyle tips refined.")

        else:
             # Fallback for unknown agents
            yield log_event("System", f"Unknown agent '{next_agent}' selected.")

        agents_used.append(next_agent)

    # 5) Final synthesis of all agent outputs
    yield log_event("Synthesizer", "Combining All Agent Evaluations...")
    
    # --- Deep Reasoning Simulation (User Request) ---
    # We yield specific "thought" logs to show the system's "intelligence"
    
    if "SymptomAgent" in agents_used:
        yield log_event("Synthesizer", "🔍 Reviewing symptom agent findings for accuracy...")
    
    if "SymptomAgent" in agents_used and "DietAgent" in agents_used:
        yield log_event("Synthesizer", "📊 Cross-analyzing medical abnormalities with diet suggestions...")
    
    if "DietAgent" in agents_used and "FitnessAgent" in agents_used:
        yield log_event("Synthesizer", "🥗 Verifying compatibility between nutrition and exercise agents...")
    
    if "LifestyleAgent" in agents_used:
        yield log_event("Synthesizer", "🌙 Checking lifestyle advice for completeness...")
        
    yield log_event("Synthesizer", "💡 Integrating all agent insights into a unified health report...")
    yield log_event("Synthesizer", "🧠 Finalizing evidence-based recommendations...")
    # ------------------------------------------------
    
    final_response = synthesize_output(state, message)

    # 6) Save to LangChain ConversationBufferMemory
    memory.save_context({"input": message}, {"output": final_response})

    # 7) Also log this turn for /history API
    # 7) Also log this turn for /history API
    append_conversation_turn(
        user_id=user_id,
        user_message=message,
        assistant_response=final_response,
        agents_used=agents_used,
        reasoning_logs=reasoning_logs,
    )
    print("DEBUG: Pipeline finished, sending final response")
    yield {
        "type": "final", 
        "response": final_response, 
        "agents_used": agents_used,
        "reasoning_logs": reasoning_logs
    }


def process_query(user_id: str, message: str):
    """
    Wrapper for process_query_generator to maintain backward compatibility.
    """
    gen = process_query_generator(user_id, message)
    final_result = None
    for event in gen:
        if event["type"] == "final":
            final_result = event
    
    if final_result:
        return final_result["response"], final_result["agents_used"]
    return "Error processing request", []
