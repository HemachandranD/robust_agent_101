import sympy
from langchain_core.tools import Tool


# Math (sympy)
def calculate(expression: str):
    try:
        result = sympy.sympify(expression).evalf()
        return {"result": float(result)}
    except Exception as e:
        return {"error": f"Calculation failed: {str(e)}"}

tools = [
    Tool(name="Calculator", func=calculate, description="Evaluate math expressions.")
]