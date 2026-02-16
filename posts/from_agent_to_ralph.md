Title: From Zero to Agent: Building a CLI AI Coding Assistant in 100 Lines
Author: Vilson Vieira
Date: 2026-02-10 18:25:00
Public: True

Let's build an AI coding agent from scratch. No frameworks, no abstractions—just the core loop that makes agents work.

We'll use TypeScript with Bun and OpenRouter to call any LLM. In about 100 lines, you'll have a working agent that can read files, execute commands, and help you code.

## The Agentic Loop

Every AI agent follows the same pattern:

1. Send messages to the LLM
2. Get a response (text or tool calls)
3. If there are tool calls, execute them
4. Add the results back to the conversation
5. Repeat until done

That's it.

## Setup

```bash
mkdir ai-agent
cd ai-agent
bun init -y
bun add openai
```

We'll use the OpenAI SDK because OpenRouter is API-compatible.

Create `agent.ts` and let's go.

## Step 1: The Basic Client

First, configure the OpenRouter client:

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY,
});

const MODEL = "anthropic/claude-3.5-sonnet";
```

Simple. OpenRouter handles routing to any model.

## Step 2: Define Tools

An agent needs tools. Let's give it two: read files and execute shell commands.

```typescript
const tools = [
  {
    type: "function" as const,
    function: {
      name: "read_file",
      description: "Read contents of a file",
      parameters: {
        type: "object",
        properties: {
          path: { type: "string", description: "File path to read" },
        },
        required: ["path"],
      },
    },
  },
  {
    type: "function" as const,
    function: {
      name: "execute_command",
      description: "Execute a shell command",
      parameters: {
        type: "object",
        properties: {
          command: { type: "string", description: "Command to execute" },
        },
        required: ["command"],
      },
    },
  },
];
```

These JSON schemas tell the LLM what it can do.

## Step 3: Implement the Tools

Now the actual functions:

```typescript
import { readFileSync } from "fs";
import { execSync } from "child_process";

async function executeTool(name: string, args: any): Promise<string> {
  try {
    if (name === "read_file") {
      return readFileSync(args.path, "utf-8");
    } else if (name === "execute_command") {
      return execSync(args.command, { encoding: "utf-8", maxBuffer: 10 * 1024 * 1024 });
    }
    return "Unknown tool";
  } catch (error: any) {
    return `Error: ${error.message}`;
  }
}
```

Read files, run commands, catch errors. That's all we need.

## Step 4: The Agentic Loop

Here's where it gets interesting:

```typescript
async function runAgent(userMessage: string) {
  const messages: any[] = [
    {
      role: "system",
      content: "You are a helpful coding assistant. Use tools to help the user.",
    },
    { role: "user", content: userMessage },
  ];

  while (true) {
    const response = await client.chat.completions.create({
      model: MODEL,
      messages,
      tools,
    });

    const message = response.choices[0].message;
    messages.push(message);

    // If no tool calls, we're done
    if (!message.tool_calls || message.tool_calls.length === 0) {
      console.log(message.content);
      break;
    }

    // Execute each tool call
    for (const toolCall of message.tool_calls) {
      const args = JSON.parse(toolCall.function.arguments);
      const result = await executeTool(toolCall.function.name, args);

      console.log(`[${toolCall.function.name}] ${JSON.stringify(args)}`);

      messages.push({
        role: "tool",
        tool_call_id: toolCall.id,
        content: result,
      });
    }
  }
}
```

This is the heart of the agent:
- Call the LLM with current messages
- If it responds with text, print and exit
- If it makes tool calls, execute them
- Add results to messages
- Loop until done

## Step 5: CLI Interface

Make it usable:

```typescript
const prompt = process.argv.slice(2).join(" ");

if (!prompt) {
  console.log("Usage: bun agent.ts <your request>");
  process.exit(1);
}

runAgent(prompt);
```

## Running It

```bash
export OPENROUTER_API_KEY="your-key-here"
bun agent.ts "read package.json and tell me what dependencies I have"
```

The agent will:
1. Read package.json
2. Analyze the contents
3. Report back

That's an AI agent.

## The Complete Code

Here's everything together:

```typescript
import OpenAI from "openai";
import { readFileSync } from "fs";
import { execSync } from "child_process";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY,
});

const MODEL = "anthropic/claude-3.5-sonnet";

const tools = [
  {
    type: "function" as const,
    function: {
      name: "read_file",
      description: "Read contents of a file",
      parameters: {
        type: "object",
        properties: {
          path: { type: "string", description: "File path to read" },
        },
        required: ["path"],
      },
    },
  },
  {
    type: "function" as const,
    function: {
      name: "execute_command",
      description: "Execute a shell command",
      parameters: {
        type: "object",
        properties: {
          command: { type: "string", description: "Command to execute" },
        },
        required: ["command"],
      },
    },
  },
];

async function executeTool(name: string, args: any): Promise<string> {
  try {
    if (name === "read_file") {
      return readFileSync(args.path, "utf-8");
    } else if (name === "execute_command") {
      return execSync(args.command, { encoding: "utf-8", maxBuffer: 10 * 1024 * 1024 });
    }
    return "Unknown tool";
  } catch (error: any) {
    return `Error: ${error.message}`;
  }
}

async function runAgent(userMessage: string) {
  const messages: any[] = [
    {
      role: "system",
      content: "You are a helpful coding assistant. Use tools to help the user.",
    },
    { role: "user", content: userMessage },
  ];

  while (true) {
    const response = await client.chat.completions.create({
      model: MODEL,
      messages,
      tools,
    });

    const message = response.choices[0].message;
    messages.push(message);

    if (!message.tool_calls || message.tool_calls.length === 0) {
      console.log(message.content);
      break;
    }

    for (const toolCall of message.tool_calls) {
      const args = JSON.parse(toolCall.function.arguments);
      const result = await executeTool(toolCall.function.name, args);

      console.log(`[${toolCall.function.name}] ${JSON.stringify(args)}`);

      messages.push({
        role: "tool",
        tool_call_id: toolCall.id,
        content: result,
      });
    }
  }
}

const prompt = process.argv.slice(2).join(" ");

if (!prompt) {
  console.log("Usage: bun agent.ts <your request>");
  process.exit(1);
}

runAgent(prompt);
```

## What's Next?

This is minimal but functional. You could add:
- Streaming responses for better UX
- More tools (write files, search, etc.)
- Better error handling
- Conversation history
- Token usage tracking

But you don't need any of that to understand how agents work. It's just a loop.

The LLM decides what to do. You execute it. Repeat.

---

## Going Deeper: The Ralph Loop

But there's a problem with our agent. It stops when the LLM *thinks* it's done. Not when the work is actually complete.

What if the tests fail? What if the build breaks? The agent just shrugs and exits.

What if wrap the agent in one more loop? That's the **Ralph Loop**.

### What is the Ralph Loop?

Named after Ralph Wiggum from The Simpsons (yes, the "I'm in danger" kid), the Ralph Loop is a technique that's exploded in popularity in early 2026. Originally coined by Geoffrey Huntley, it's beautifully simple:

```bash
while :; do cat PROMPT.md | <ANY_CODING_AGENT> ; done
```

That's it. Just keep running the agent until the task is actually complete.

### The Philosophy

Traditional agents stop when the LLM says "I'm done." Ralph Loop stops when **external verification** confirms success. Don't trust the LLM, verify.

### How It Works

Wrap your agent in an outer loop that:
1. Runs the agent
2. Checks if the objective is met (via external verification)
3. If not, injects feedback and runs again
4. Repeats until success (or max iterations)

Think of it as `while (true)` for AI autonomy.

### Implementing Ralph Loop

Let's wrap our agent. Create `ralph.ts`:

```typescript
import { readFileSync, writeFileSync } from "fs";
import { execSync } from "child_process";

const MAX_ITERATIONS = 10;
const PROMPT_FILE = "PROMPT.md";
const TASK_FILE = "TASK.md";

async function verifyCompletion(): Promise<{ complete: boolean; feedback?: string }> {
  try {
    // Example: check if tests pass
    execSync("npm test", { stdio: "pipe" });
    return { complete: true };
  } catch (error: any) {
    return {
      complete: false,
      feedback: `Tests failed:\n${error.stdout?.toString() || error.message}`,
    };
  }
}

async function runRalphLoop() {
  const originalPrompt = readFileSync(PROMPT_FILE, "utf-8");

  for (let iteration = 1; iteration <= MAX_ITERATIONS; iteration++) {
    console.log(`\n=== Ralph Iteration ${iteration}/${MAX_ITERATIONS} ===\n`);

    // Run the agent we just built
    try {
      execSync(`bun agent.ts "$(cat ${TASK_FILE})"`, { stdio: "inherit" });
    } catch (error) {
      console.log("Agent execution failed, continuing...");
    }

    // Verify completion
    const { complete, feedback } = await verifyCompletion();

    if (complete) {
      console.log("\n✓ Task completed successfully!");
      break;
    }

    // Inject feedback for next iteration
    console.log(`\n✗ Not complete yet. Feedback:\n${feedback}\n`);

    const updatedTask = `${originalPrompt}\n\n## Previous Attempt Feedback\n${feedback}\n\nPlease fix the issues above.`;
    writeFileSync(TASK_FILE, updatedTask);

    if (iteration === MAX_ITERATIONS) {
      console.log("\n⚠ Max iterations reached. Manual intervention needed.");
    }
  }
}

runRalphLoop();
```

Now create `PROMPT.md`:

```markdown
# Task: Implement User Authentication

Create a simple user authentication system with:
- Login endpoint at POST /login
- Registration endpoint at POST /register
- Tests that verify both endpoints work
- All tests must pass

Use the tools available to read existing code, write new files, and run tests.
```

Run it:

```bash
cp PROMPT.md TASK.md
bun ralph.ts
```

### What Happens

1. **Iteration 1**: Agent creates login/register endpoints, writes tests
2. Verification fails: tests don't pass (forgot password hashing)
3. **Iteration 2**: Feedback injected: "Tests failed: password comparison failing"
4. Agent fixes password hashing
5. Verification succeeds: all tests pass
6. Loop exits

The agent keeps going until it **actually works**.

### Real-World Ralph Loop

In practice, verification can be anything:
- `docker build && docker run --health-check`
- `git diff --exit-code` (no uncommitted changes)
- Custom health checks, API responses, file existence
- Multiple verification steps in sequence

Example with multiple checks:

```typescript
async function verifyCompletion(): Promise<{ complete: boolean; feedback?: string }> {
  // Check 1: Build succeeds
  try {
    execSync("npm run build", { stdio: "pipe" });
  } catch (error: any) {
    return { complete: false, feedback: `Build failed:\n${error.message}` };
  }

  // Check 2: Tests pass
  try {
    execSync("npm test", { stdio: "pipe" });
  } catch (error: any) {
    return { complete: false, feedback: `Tests failed:\n${error.message}` };
  }

  // Check 3: Lint passes
  try {
    execSync("npm run lint", { stdio: "pipe" });
  } catch (error: any) {
    return { complete: false, feedback: `Lint failed:\n${error.message}` };
  }

  return { complete: true };
}
```

### Why This Works

The secret is that **progress lives in your files, not in the LLM's context**.

When the agent runs again:
- It reads the files it just modified
- It sees the test output
- It gets feedback on what failed
- It tries a different approach

Fresh context, persistent progress.

### The 2026 Movement

Ralph Loop has exploded in 2026. There are now:
- An official [Anthropic Claude Code plugin](https://github.com/anthropics/claude-code)
- [Vercel's ralph-loop-agent](https://github.com/vercel-labs/ralph-loop-agent) for AI SDK
- Implementations in Google ADK, Cursor, and more

### A Word of Caution

Ralph Loop is powerful but dangerous. It gives the AI full control over your terminal. Security experts strictly advise:

1. **Always use sandboxed environments** (Docker, VMs, isolated containers)
2. **Set strict max-iterations** (don't let it run forever)
3. **Monitor API costs** (infinite loops cost infinite money)
4. **Review generated code** (autonomy ≠ correctness)

### The Complete Ralph Pattern

Here's the full implementation with safety checks:

```typescript
import { readFileSync, writeFileSync, existsSync } from "fs";
import { execSync } from "child_process";

const MAX_ITERATIONS = 10;
const PROMPT_FILE = "PROMPT.md";
const TASK_FILE = "TASK.md";
const STATE_FILE = ".ralph-state.json";

interface RalphState {
  iteration: number;
  startTime: number;
  totalCost: number;
}

async function verifyCompletion(): Promise<{ complete: boolean; feedback?: string }> {
  try {
    execSync("npm test", { stdio: "pipe" });
    return { complete: true };
  } catch (error: any) {
    return {
      complete: false,
      feedback: `Tests failed:\n${error.stdout?.toString() || error.message}`,
    };
  }
}

function loadState(): RalphState {
  if (existsSync(STATE_FILE)) {
    return JSON.parse(readFileSync(STATE_FILE, "utf-8"));
  }
  return { iteration: 0, startTime: Date.now(), totalCost: 0 };
}

function saveState(state: RalphState) {
  writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

async function runRalphLoop() {
  const originalPrompt = readFileSync(PROMPT_FILE, "utf-8");
  const state = loadState();

  // Safety: max runtime check (4 hours)
  const MAX_RUNTIME_MS = 4 * 60 * 60 * 1000;
  const elapsed = Date.now() - state.startTime;
  if (elapsed > MAX_RUNTIME_MS) {
    console.log("⚠ Max runtime exceeded. Stopping.");
    return;
  }

  for (let iteration = state.iteration + 1; iteration <= MAX_ITERATIONS; iteration++) {
    console.log(`\n=== Ralph Iteration ${iteration}/${MAX_ITERATIONS} ===`);
    console.log(`Elapsed: ${Math.round(elapsed / 1000 / 60)} minutes\n`);

    state.iteration = iteration;
    saveState(state);

    try {
      execSync(`bun agent.ts "$(cat ${TASK_FILE})"`, { stdio: "inherit" });
    } catch (error) {
      console.log("Agent execution failed, continuing...");
    }

    const { complete, feedback } = await verifyCompletion();

    if (complete) {
      console.log("\n✓ Task completed successfully!");
      execSync(`rm ${STATE_FILE}`); // Clean up
      break;
    }

    console.log(`\n✗ Not complete. Feedback:\n${feedback}\n`);

    const updatedTask = `${originalPrompt}\n\n## Iteration ${iteration} Feedback\n${feedback}\n\nFix the issues and try again.`;
    writeFileSync(TASK_FILE, updatedTask);

    if (iteration === MAX_ITERATIONS) {
      console.log("\n⚠ Max iterations reached.");
    }
  }
}

runRalphLoop();
```

### The Future

Ralph Loop represents a shift in how we think about AI coding agents:

**Old way**: "Run the agent, check the output, manually iterate"

**New way**: "Define success criteria, let the agent iterate until it's actually done"

It's autonomous in the truest sense. You write the goal, define verification, and walk away.

When you come back, it's either done or you know exactly why it failed.

---

## Sources

- [2026 - The year of the Ralph Loop Agent](https://dev.to/alexandergekov/2026-the-year-of-the-ralph-loop-agent-1gkj)
- [Ralph Loop for Deep Agents: Building Autonomous AI That Just Keeps Going](https://medium.com/ai-artistry/ralph-loop-for-deep-agents-building-autonomous-ai-that-just-keeps-going-cb4da3a09b37)
- [GitHub - snarktank/ralph](https://github.com/snarktank/ralph)
- [Ralph Loop with Google ADK: AI Agents That Verify, Not Guess](https://medium.com/google-cloud/ralph-loop-with-google-adk-ai-agents-that-verify-not-guess-b41f71c0f30f)
- [GitHub - vercel-labs/ralph-loop-agent](https://github.com/vercel-labs/ralph-loop-agent)
- [Ralph Mode: Why AI Agents Should Forget](https://medium.com/byte-sized-brainwaves/ralph-mode-why-ai-agents-should-forget-9f98bec6fc91)
- [Inventing the Ralph Wiggum Loop](https://devinterrupted.substack.com/p/inventing-the-ralph-wiggum-loop-creator)
- [How Ralph Wiggum went from 'The Simpsons' to the biggest name in AI right now](https://venturebeat.com/technology/how-ralph-wiggum-went-from-the-simpsons-to-the-biggest-name-in-ai-right-now)
- [From ReAct to Ralph Loop: A Continuous Iteration Paradigm for AI Agents](https://www.alibabacloud.com/blog/from-react-to-ralph-loop-a-continuous-iteration-paradigm-for-ai-agents_602799)
- [Claude Code Ralph Wiggum Plugin](https://github.com/anthropics/claude-code/blob/main/plugins/ralph-wiggum/README.md)
