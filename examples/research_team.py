"""
Example 2: Multi-Agent Research Team
=====================================
This example shows how multiple agents can work together
on a research task, passing data through shared context.

Run this example:
    python examples/research_team.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import Agent, AgentRole, Orchestrator, Task, TaskPriority
from src.agent import AgentConfig
from src.context import SharedContext


class ResearcherAgent(Agent):
    """An agent that gathers information."""
    
    def __init__(self):
        config = AgentConfig(
            name="Researcher",
            role=AgentRole.RESEARCHER,
            capabilities=["research", "data_gathering"],
        )
        super().__init__(config)
    
    def process_task(self, task: Task) -> dict:
        print(f"  [{self.name}] Researching: {task.input_data.get('topic', 'unknown')}")
        
        topic = task.input_data.get("topic", "general")
        
        # Simulate gathering research data
        research_data = {
            "python": {
                "facts": ["Created by Guido van Rossum", "First released in 1991", "Named after Monty Python"],
                "sources": ["python.org", "wikipedia.org"],
                "confidence": 0.95,
            },
            "ai": {
                "facts": ["AI can learn from data", "Neural networks are inspired by brains", "AI is transforming every industry"],
                "sources": ["deeplearning.ai", "arxiv.org"],
                "confidence": 0.90,
            },
            "general": {
                "facts": ["Research is important", "Data helps us understand"],
                "sources": ["general knowledge"],
                "confidence": 0.80,
            },
        }
        
        data = research_data.get(topic, research_data["general"])
        print(f"  [{self.name}] Found {len(data['facts'])} facts!")
        
        return {
            "topic": topic,
            "data": data,
        }


class AnalyzerAgent(Agent):
    """An agent that analyzes data and produces insights."""
    
    def __init__(self):
        config = AgentConfig(
            name="Analyzer",
            role=AgentRole.ANALYZER,
            capabilities=["analysis", "insight_generation"],
        )
        super().__init__(config)
    
    def process_task(self, task: Task) -> dict:
        print(f"  [{self.name}] Analyzing research data...")
        
        research_data = task.input_data.get("research_data", {})
        facts = research_data.get("facts", [])
        confidence = research_data.get("confidence", 0)
        
        # Simulate analysis
        insights = []
        for fact in facts:
            insights.append(f"Key insight: {fact}")
        
        score = confidence * len(facts) / 3  # Simple scoring
        
        print(f"  [{self.name}] Generated {len(insights)} insights!")
        
        return {
            "insights": insights,
            "analysis_score": round(score, 2),
            "recommendation": "High quality" if score > 1.0 else "Needs more data",
        }


class WriterAgent(Agent):
    """An agent that writes the final report."""
    
    def __init__(self):
        config = AgentConfig(
            name="Writer",
            role=AgentRole.WORKER,
            capabilities=["writing", "report_generation"],
        )
        super().__init__(config)
    
    def process_task(self, task: Task) -> dict:
        print(f"  [{self.name}] Writing report...")
        
        topic = task.input_data.get("topic", "Unknown")
        insights = task.input_data.get("insights", [])
        score = task.input_data.get("analysis_score", 0)
        
        # Generate a simple report
        report_lines = [
            f"# Research Report: {topic.title()}",
            "",
            "## Key Findings",
        ]
        for insight in insights:
            report_lines.append(f"- {insight}")
        
        report_lines.extend([
            "",
            f"## Quality Score: {score}/3.0",
            "",
            "## Conclusion",
            f"The research on {topic} reveals important information.",
        ])
        
        report = "\n".join(report_lines)
        print(f"  [{self.name}] Report complete!")
        
        return {
            "report": report,
            "word_count": len(report.split()),
        }


def main():
    print("="*60)
    print("EXAMPLE 2: Multi-Agent Research Team")
    print("="*60)
    
    # Create orchestrator
    orchestrator = Orchestrator()
    
    # Create agents
    researcher = ResearcherAgent()
    analyzer = AnalyzerAgent()
    writer = WriterAgent()
    
    # Register all agents
    orchestrator.register_agent(researcher)
    orchestrator.register_agent(analyzer)
    orchestrator.register_agent(writer)
    
    topic = "python"
    
    print("\n" + "-"*40)
    print(f"Starting Research Pipeline for: {topic}")
    print("-"*40 + "\n")
    
    # Step 1: Research
    print("STEP 1: Gathering Research Data")
    print("-"*40)
    research_result = orchestrator.create_and_run_task(
        name="Research topic",
        required_capabilities=["research"],
        input_data={"topic": topic},
    )
    
    if not research_result:
        print("Failed to complete research!")
        return
    
    # Store in shared context
    orchestrator.context.set("research_data", research_result, author="Researcher")
    print(f"\nStored research data in shared context\n")
    
    # Step 2: Analyze
    print("STEP 2: Analyzing Data")
    print("-"*40)
    analysis_result = orchestrator.create_and_run_task(
        name="Analyze research",
        required_capabilities=["analysis"],
        input_data={"research_data": research_result.get("data", {})},
    )
    
    if not analysis_result:
        print("Failed to complete analysis!")
        return
    
    orchestrator.context.set("analysis_result", analysis_result, author="Analyzer")
    print(f"\nStored analysis in shared context\n")
    
    # Step 3: Write Report
    print("STEP 3: Writing Report")
    print("-"*40)
    report_result = orchestrator.create_and_run_task(
        name="Write report",
        required_capabilities=["writing"],
        input_data={
            "topic": topic,
            "insights": analysis_result.get("insights", []),
            "analysis_score": analysis_result.get("analysis_score", 0),
        },
    )
    
    if report_result:
        print("\n" + "="*60)
        print("FINAL REPORT")
        print("="*60)
        print(report_result.get("report", "No report generated"))
        print("="*60)
    
    # Show final status
    orchestrator.print_status()
    
    # Show shared context
    print("Shared Context Contents:")
    for key in orchestrator.context.list_keys():
        metadata = orchestrator.context.get_metadata(key)
        print(f"  - {key}: written by {metadata['author']}")


if __name__ == "__main__":
    main()
