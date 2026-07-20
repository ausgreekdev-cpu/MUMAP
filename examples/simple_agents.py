"""
Example 1: Simple Agent Usage
=============================
This example shows how to:
1. Create custom agents
2. Register them with an orchestrator
3. Create and run tasks

Run this example:
    python examples/simple_agents.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import Agent, AgentRole, Orchestrator, Task, TaskPriority
from src.agent import AgentConfig


# ============================================================
# STEP 1: Create your first custom agent
# ============================================================

class MathAgent(Agent):
    """An agent that can do math calculations."""
    
    def __init__(self, name: str = "MathBot"):
        config = AgentConfig(
            name=name,
            role=AgentRole.WORKER,
            capabilities=["math", "calculation"],
        )
        super().__init__(config)
    
    def process_task(self, task: Task) -> dict:
        """Process math tasks."""
        print(f"  [{self.name}] Working on: {task.name}")
        
        operation = task.input_data.get("operation", "add")
        numbers = task.input_data.get("numbers", [0, 0])
        
        if operation == "add":
            result = sum(numbers)
        elif operation == "multiply":
            result = 1
            for n in numbers:
                result *= n
        elif operation == "average":
            result = sum(numbers) / len(numbers) if numbers else 0
        else:
            result = f"Unknown operation: {operation}"
        
        print(f"  [{self.name}] Result: {result}")
        return {"operation": operation, "result": result}


class GreetingAgent(Agent):
    """An agent that creates personalized greetings."""
    
    def __init__(self, name: str = "GreeterBot"):
        config = AgentConfig(
            name=name,
            role=AgentRole.WORKER,
            capabilities=["greeting", "text"],
        )
        super().__init__(config)
    
    def process_task(self, task: Task) -> dict:
        """Create a greeting."""
        print(f"  [{self.name}] Working on: {task.name}")
        
        name = task.input_data.get("name", "World")
        style = task.input_data.get("style", "formal")
        
        greetings = {
            "formal": f"Good day, {name}. Welcome to our platform.",
            "casual": f"Hey {name}! What's up?",
            "funny": f"Yo {name}! Did you code today or did code code you?",
        }
        
        greeting = greetings.get(style, f"Hello, {name}!")
        print(f"  [{self.name}] Created greeting!")
        return {"greeting": greeting, "style": style}


# ============================================================
# STEP 2: Set up the orchestrator
# ============================================================

def main():
    print("="*60)
    print("EXAMPLE 1: Simple Agent Usage")
    print("="*60)
    
    # Create the orchestrator (the boss!)
    orchestrator = Orchestrator()
    
    # Create agents
    math_agent = MathAgent("MathBot")
    greeting_agent = GreetingAgent("GreeterBot")
    
    # Register agents with orchestrator
    orchestrator.register_agent(math_agent)
    orchestrator.register_agent(greeting_agent)
    
    print("\n" + "-"*40)
    print("Running Tasks")
    print("-"*40)
    
    # Task 1: Math calculation
    result1 = orchestrator.create_and_run_task(
        name="Calculate sum",
        description="Add some numbers together",
        required_capabilities=["math"],
        input_data={"operation": "add", "numbers": [10, 20, 30, 40]},
    )
    print(f"\nTask 1 Result: {result1}")
    
    # Task 2: Math calculation
    result2 = orchestrator.create_and_run_task(
        name="Calculate average",
        description="Find the average",
        required_capabilities=["math"],
        input_data={"operation": "average", "numbers": [10, 20, 30]},
    )
    print(f"\nTask 2 Result: {result2}")
    
    # Task 3: Greeting
    result3 = orchestrator.create_and_run_task(
        name="Create greeting",
        description="Say hello to Alice",
        required_capabilities=["greeting"],
        input_data={"name": "Alice", "style": "funny"},
    )
    print(f"\nTask 3 Result: {result3}")
    
    # Print final status
    orchestrator.print_status()


if __name__ == "__main__":
    main()
