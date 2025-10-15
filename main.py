from src.helpers import run_agent, visualize_agent
from src.memory import memory


def interactive_mode():
    """Run agent in interactive mode"""
    print("🤖 Robust Agent - Interactive Mode")
    print("Type 'quit' to exit, 'clear' to clear memory\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == 'quit':
            print("Goodbye! 👋")
            break
        elif user_input.lower() == 'clear':
            memory.clear()
            print("✅ Memory cleared!")
            continue
        elif user_input.lower() == 'display':
            visualize_agent()
            print("✅ Agent graph displayed!")
            continue
        elif not user_input:
            continue
        
        run_agent(user_input)


if __name__ == "__main__":
    print("🤖 Robust Agent 101 - Starting...")
    print("=" * 60)
    
    # # Test 1: Simple calculation
    # run_agent("What is 5 + 3?")
    
    # # Test 2: Tool-requiring calculation
    # run_agent("Calculate the result of (15 * 4) + (20 / 5)")
    
    # # Test 3: Conversational
    # run_agent("Hello! How are you?")
    
    # # Test 4: Test input validation (profanity - will fail)
    # run_agent("This is some shit content")
    
    # # Test 5: Test output length (should work)
    # run_agent("Explain quantum computing")

    # Test 6: Stock quote (MCP tool)
    # run_agent("What's the current stock price of Apple?")

    # Test 7: Web search (MCP tool)
    # run_agent("latest AI news")

    # Test 8: ASCII art (MCP tool)
    # run_agent("Create ASCII art that says 'LOL'")
    
    print("\n" + "="*60)
    # print("✅ Agent testing complete!")
    interactive_mode()
    print("="*60)
    
    # Optional: Visualize the graph
    # visualize_agent()
