# 12-Factor Micro-Tools Examples
*Following Official HumanLayer 12-Factor Agents Structure*

## Understanding the 12-Factor Agent Framework

The 12-factor agents framework from [HumanLayer](https://github.com/humanlayer/12-factor-agents) is a methodology for building production-ready AI agent systems. This examples folder demonstrates how to structure individual tools following their official conventions.

### What is a "Tool" in 12-Factor Agents?

A **tool** in this framework is:
> "Structured outputs from your LLM that trigger deterministic code"

**Key Characteristics:**
- ✅ **Single Purpose**: Does one thing extremely well
- ✅ **Structured I/O**: Clear input/output contracts using BAML schemas
- ✅ **Stateless**: No memory between calls
- ✅ **Configurable**: Behavior controlled by environment variables
- ✅ **Testable**: Deterministic logic that's easy to test

### Official 12-Factor Structure

Each tool follows the [official structure](https://github.com/humanlayer/12-factor-agents/discussions/61):

```
tool-name/
├── README.md              # Tool documentation
├── .env                   # Environment configuration (Factor 3)
├── 12factors.toml         # Tool metadata and compliance tracking
├── pyproject.toml         # Dependencies and build config
├── baml_src/              # BAML schemas and AI definitions
│   ├── tool_schema.baml   # Input/output definitions
│   ├── clients.baml       # LLM client configurations
│   └── generators.baml    # Code generation settings
└── app/                   # Implementation code
    ├── __init__.py
    ├── tool_main.py       # Core tool logic
    ├── agent.py           # LLM integration (optional)
    ├── server.py          # HTTP service (Factor 7)
    └── main.py            # Entry point
```

## Learning Path for New Programmers

### 🟢 Start Here: Basic Concepts

**1. [bmf-filter-tool/](./bmf-filter-tool/)**
**Difficulty**: Beginner
**Learn**: Data filtering, database queries, environment configuration
**12-Factor Focus**: Factor 3 (Config), Factor 4 (Structured I/O), Factor 6 (Stateless)

This tool filters IRS nonprofit data based on criteria. Perfect for understanding:
- How tools receive structured input (BAML schemas)
- How environment variables control behavior
- How stateless processing works
- Basic HTTP service structure

### 🟡 Intermediate: External Services

**2. [ai-heavy-tool/](./ai-heavy-tool/)**
**Difficulty**: Intermediate
**Learn**: External API integration, cost tracking, error handling
**12-Factor Focus**: Factor 4 (Backing Services), Factor 9 (Disposability), Factor 11 (Logs)

This tool integrates with OpenAI for AI analysis. Shows how to:
- Treat external APIs as backing services
- Handle API failures gracefully
- Track costs and usage
- Structure complex AI prompts

**3. [government-scorer-tool/](./government-scorer-tool/)**
**Difficulty**: Intermediate
**Learn**: Business logic algorithms, weighted scoring, batch processing
**12-Factor Focus**: Factor 6 (Stateless), Factor 3 (Config), Factor 11 (Logs)

This tool scores funding opportunities. Demonstrates:
- Pure business logic as tools
- Configurable scoring weights
- Deterministic algorithms
- Auditable results with explanations

## Key 12-Factor Principles in Action

### Factor 3: Config from Environment
```bash
# .env file controls tool behavior
SCORING_WEIGHTS_ELIGIBILITY=0.30
SCORING_WEIGHTS_GEOGRAPHIC=0.20
AI_MODEL=gpt-4
BMF_CACHE_ENABLED=true
```

### Factor 4: Tools are Structured Outputs
```baml
// BAML defines clear input/output contracts
class ToolIntent {
    intent "tool_name"
    input_data InputSchema
    preferences ConfigOptions?
}

class ToolResult {
    intent "tool_result"
    output_data OutputSchema
    metadata ExecutionData
}
```

### Factor 6: Stateless Processes
```python
# Tools are pure functions - same input = same output
async def execute(self, intent: ToolIntent) -> ToolResult:
    # Everything needed is in the intent
    # No hidden state or memory
    return process_intent(intent)
```

### Factor 7: Port Binding
```python
# Each tool can run as independent HTTP service
@app.post("/execute")
async def execute_tool(intent: ToolIntent):
    tool = MyTool()
    return await tool.execute(intent)

# Tool runs on its own port
uvicorn.run(app, host="0.0.0.0", port=8001)
```

## How to Use These Examples

### 1. Start Simple
Begin with `bmf-filter-tool/` - read the README, look at the code, run the examples.

### 2. Understand the Pattern
Notice how each tool has the same structure:
- **Input**: Clearly defined data coming in
- **Process**: One specific function
- **Output**: Clearly defined data going out

### 3. See the Connections
Look at how tools connect together in workflows:
```
Tool A Output → Tool B Input → Tool C Input → Final Result
```

### 4. Practice
Try modifying the examples:
- Change filter criteria in BMF Filter Tool
- Add new validation rules to Profile Validator
- Adjust scoring weights in Government Scorer

### 5. Build Your Own
Once you understand the pattern, create your own tools following the same structure.

## Common Beginner Questions

**Q: Why not just put everything in one big function?**
A: It's like asking "why not put your entire kitchen in one giant appliance?" Tools are specialized for good reasons.

**Q: How do tools communicate?**
A: Through clearly defined inputs and outputs, like passing notes between people.

**Q: What if I need to share data between tools?**
A: Pass it as input/output, or use external storage (database, cache) that tools can access.

**Q: How do I know what tools to create?**
A: Look at your current big functions and ask: "What are the distinct steps here?" Each step becomes a tool.

**Q: This seems like more work - why do it?**
A: Like organizing your toolbox - more work upfront, but much easier to maintain and grow over time.

## Next Steps

1. Read through each tool example in order
2. Run the example code to see how it works
3. Try modifying examples to understand the concepts
4. Look at how tools combine in the main WORKFLOWS.md document
5. Start planning how to break your own code into tools

---

Remember: The goal isn't to make things complicated - it's to make complex systems **maintainable** by breaking them into simple, understandable pieces.