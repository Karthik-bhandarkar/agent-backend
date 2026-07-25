"""
Latency benchmark: measures end-to-end response time for the orchestrator
by simulating what the WebSocket endpoint does.
Does NOT require a live server - calls the same orchestrator code directly.
Requires: GROQ_API_KEY and MONGODB_URI in a .env file or environment.

Run: python latency_benchmark.py
"""

import time
import sys
import os

# ---- Test queries covering all 4 domains ----
TEST_QUERIES = [
    ("I have been having severe headaches for the past 3 days", "SymptomAgent"),
    ("Give me a vegetarian diet plan for weight loss", "DietAgent"),
    ("I want a beginner workout routine for building muscle", "FitnessAgent"),
    ("I am always stressed and cannot sleep at night", "LifestyleAgent"),
    ("My back hurts a lot after sitting at my desk all day", "SymptomAgent"),
    ("What foods should I eat to reduce inflammation?", "DietAgent"),
    ("My Vitamin D is 15 ng/ml and I feel very tired all the time", "SymptomAgent"),
    ("Plan a 7-day high protein meal plan", "DietAgent"),
    ("I want to improve my stamina and endurance", "FitnessAgent"),
    ("How can I reduce screen time and improve my sleep routine?", "LifestyleAgent"),
    ("I feel bloated and have stomach pain after meals", "SymptomAgent"),
    ("What is the best post-workout meal?", "DietAgent"),
    ("I want to lose belly fat with exercise", "FitnessAgent"),
    ("I feel burnt out from work, how do I recover?", "LifestyleAgent"),
    ("My knees hurt when I climb stairs", "SymptomAgent"),
]

def run_benchmark():
    try:
        from orchestrator.orchestrator import process_query
    except Exception as e:
        print(f"[ERROR] Cannot import orchestrator: {e}")
        print("Make sure GROQ_API_KEY and MONGODB_URI are set and dependencies are installed.")
        return

    latencies = []
    routing_results = []
    correct_routes = 0

    print(f"\n{'='*60}")
    print(f"Running {len(TEST_QUERIES)} test queries...")
    print(f"{'='*60}\n")

    for i, (query, expected_agent) in enumerate(TEST_QUERIES, 1):
        print(f"[{i:02d}/{len(TEST_QUERIES)}] Query: {query[:60]}...")
        t0 = time.perf_counter()
        try:
            response, agents_used = process_query("benchmark_user_001", query)
            elapsed = time.perf_counter() - t0
            latencies.append(elapsed)
            primary_agent = agents_used[0] if agents_used else "NONE"
            is_correct = primary_agent == expected_agent
            if is_correct:
                correct_routes += 1
            routing_results.append({
                "query": query[:60],
                "expected": expected_agent,
                "got": primary_agent,
                "all_agents": agents_used,
                "correct": is_correct,
                "latency_s": round(elapsed, 2)
            })
            status = "[OK]" if is_correct else "[FAIL]"
            print(f"  {status} Expected={expected_agent}, Got={primary_agent}, All={agents_used}")
            print(f"  Latency: {elapsed:.2f}s\n")
        except Exception as e:
            elapsed = time.perf_counter() - t0
            print(f"  [ERROR] {e} (after {elapsed:.2f}s)\n")
            routing_results.append({
                "query": query[:60],
                "expected": expected_agent,
                "got": "ERROR",
                "all_agents": [],
                "correct": False,
                "latency_s": round(elapsed, 2)
            })

    if latencies:
        avg = sum(latencies) / len(latencies)
        mn = min(latencies)
        mx = max(latencies)
        accuracy = (correct_routes / len(TEST_QUERIES)) * 100
        print(f"\n{'='*60}")
        print(f"BENCHMARK RESULTS")
        print(f"{'='*60}")
        print(f"Total queries:      {len(TEST_QUERIES)}")
        print(f"Successful runs:    {len(latencies)}")
        print(f"Avg latency:        {avg:.2f}s")
        print(f"Min latency:        {mn:.2f}s")
        print(f"Max latency:        {mx:.2f}s")
        print(f"Routing accuracy:   {correct_routes}/{len(TEST_QUERIES)} = {accuracy:.1f}%")
        print(f"\nDetailed routing table:")
        for r in routing_results:
            tick = "[OK]" if r["correct"] else "[FAIL]"
            print(f"  {tick} [{r['latency_s']:5.2f}s] {r['expected']:15s} -> {r['got']:15s} | {r['query']}")
    else:
        print("[NO RESULTS] All queries failed. Cannot compute stats.")

if __name__ == "__main__":
    run_benchmark()
