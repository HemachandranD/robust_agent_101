from typing import Literal
import asyncio
import json
from pathlib import Path
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_groq import ChatGroq # or langchain_anthropic import ChatAnthropic

# Import your custom modules
from src.memory import memory
from src.guardrails import validate_input, validate_output
from src.tools import tools
from src.mcp_tools import mcp_tools


# Load configuration from prompts.json
config_path = Path(__file__).parent.parent / 'config' / 'prompts.json'
with open(config_path, 'r') as f:
    config = json.load(f)

# Initialize LLM from config
llm_config = config['llm']
llm = ChatGroq(
    model=llm_config['model'],
    temperature=llm_config['temperature']
)

# Combine all tools
tools = tools + mcp_tools
# Create a tools dictionary for easy lookup
tools_by_name = {tool.name: tool for tool in tools}

# With binding (efficient)
llm_with_tools = llm.bind_tools(tools)



def validate_input_node(state: MessagesState):
    """Validate user input using guardrails"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # Only validate if it's a human message
    if isinstance(last_message, HumanMessage):
        is_valid, result = validate_input(last_message.content)
        
        if not is_valid:
            # If invalid, add error message and mark for early exit
            return {
                "messages": [AIMessage(content=f"⚠️ Input validation failed: {result}")],
                "input_valid": False
            }
        else:
            # If valid, update with sanitized input
            sanitized_message = HumanMessage(content=result)
            messages[-1] = sanitized_message
            return {
                "messages": messages,
                "input_valid": True
            }
    
    return {"messages": messages, "input_valid": True}


def load_memory_node(state: MessagesState):
    """Load chat history from memory"""
    # Load previous conversation history
    history = memory.load_history()
    
    # Combine history with current messages
    # Keep the current message (last one) and prepend history
    current_messages = state["messages"]
    
    # If we have history, insert it before the current message
    if history:
        all_messages = history + current_messages
    else:
        all_messages = current_messages
    
    return {"messages": all_messages}

def llm_call_node(state: MessagesState):
    """LLM decides whether to call a tool or respond directly"""
    # Compose system prompt from persona, tone, and instructions
    system_prompt_template = config['system_prompt']
    composed_prompt = system_prompt_template.format(
        persona=config.get('persona', ''),
        tone=config.get('tone', ''),
        instructions=config.get('instructions', '')
    )
    
    system_prompt = SystemMessage(content=composed_prompt)
    
    messages_to_send = [system_prompt] + state["messages"]
    response = llm_with_tools.invoke(messages_to_send)
    
    return {"messages": [response]}

def tool_node(state: MessagesState):
    """Execute tool calls from the LLM"""
    last_message = state["messages"][-1]
    tool_results = []
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        # Get the tool and invoke it
        tool = tools_by_name[tool_name]
        
        try:
            observation = tool.invoke(tool_args)
            tool_results.append(
                ToolMessage(
                    content=str(observation),
                    tool_call_id=tool_call["id"]
                )
            )
        except Exception as e:
            tool_results.append(
                ToolMessage(
                    content=f"Error executing tool: {str(e)}",
                    tool_call_id=tool_call["id"]
                )
            )
    
    return {"messages": tool_results}

def validate_output_node(state: MessagesState):
    """Validate LLM output using guardrails"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # Only validate AI messages (not tool messages)
    if isinstance(last_message, AIMessage) and not last_message.tool_calls:
        # Get the original user input (search backwards for last HumanMessage)
        user_input = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_input = msg.content
                break
        
        is_valid, result = validate_output(last_message.content, user_input)
        
        if not is_valid:
            # Replace with safe response
            validated_message = AIMessage(content=result)
            messages[-1] = validated_message
        
        return {"messages": messages}
    
    return {"messages": messages}

def save_memory_node(state: MessagesState):
    """Save the conversation to memory"""
    messages = state["messages"]
    
    # Find the user message and AI response to save
    user_message = None
    ai_message = None
    
    for msg in messages:
        if isinstance(msg, HumanMessage) and not user_message:
            user_message = msg.content
        elif isinstance(msg, AIMessage) and not msg.tool_calls and not ai_message:
            ai_message = msg.content
    
    # Save to memory
    if user_message:
        memory.add_user_message(user_message)
    if ai_message:
        memory.add_ai_message(ai_message)
    
    return {"messages": messages}

def should_continue_after_validation(state: MessagesState) -> Literal["load_memory", END]:
    """Check if input validation passed"""
    # If input_valid exists and is False, go to END
    if "input_valid" in state and not state["input_valid"]:
        return END
    return "load_memory"


def should_continue_after_llm(state: MessagesState) -> Literal["tool_node", "validate_output"]:
    """Decide if we should call tools or validate output"""
    last_message = state["messages"][-1]
    
    # If the LLM made tool calls, route to tool execution
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tool_node"
    
    # Otherwise, validate the output
    return "validate_output"

# Create the graph
workflow = StateGraph(MessagesState)

# Add all nodes
workflow.add_node("validate_input", validate_input_node)
workflow.add_node("load_memory", load_memory_node)
workflow.add_node("llm_call", llm_call_node)
workflow.add_node("tool_node", tool_node)
workflow.add_node("validate_output", validate_output_node)
workflow.add_node("save_memory", save_memory_node)

# Add edges
workflow.add_edge(START, "validate_input")

# Conditional edge after input validation
workflow.add_conditional_edges(
    "validate_input",
    should_continue_after_validation,
    {
        "load_memory": "load_memory",
        END: END
    }
)

workflow.add_edge("load_memory", "llm_call")

# Conditional edge after LLM call
workflow.add_conditional_edges(
    "llm_call",
    should_continue_after_llm,
    {
        "tool_node": "tool_node",
        "validate_output": "validate_output"
    }
)

# Tool node loops back to LLM
workflow.add_edge("tool_node", "llm_call")

# After output validation, save memory
workflow.add_edge("validate_output", "save_memory")

# After saving memory, end
workflow.add_edge("save_memory", END)

# Compile the agent
agent = workflow.compile()