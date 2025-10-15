from IPython.display import Image, display
from langchain_core.messages import HumanMessage, AIMessage
from src.agent import agent


def run_agent(user_input: str):
    """Run the agent with a user input"""
    try:
        print(f"\n{'='*60}")
        print(f"USER: {user_input}")
        print(f"{'='*60}\n")
        
        # Create initial message
        initial_message = HumanMessage(content=user_input)
        
        # Invoke the agent
        result = agent.invoke({"messages": [initial_message]})
        
        # Extract and print ONLY the LAST AI response (not all history)
        for message in reversed(result["messages"]):
            if isinstance(message, AIMessage) and not message.tool_calls:
                print(f"ASSISTANT: {message.content}\n")
                break  # Only print the most recent response
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def visualize_agent():
    """Visualize the agent graph"""
    try:
        display(Image(agent.get_graph(xray=True).draw_mermaid_png()))
    except Exception as e:
        print(f"Visualization not available: {e}")
        print("Install graphviz and IPython for visualization")