# Building Gas Town: Orchestrating Multiple AI Agents

In the [last post](./001_from_agent_to_ralph.md), we built a single AI coding agent. It worked. But what if you need to build a complex feature that requires multiple agents working in parallel?

You need orchestration.

Enter **Gas Town** — Steve Yegge's multi-agent workspace manager that coordinates 20-30 concurrent AI agents, each playing specialized roles. Released on January 1, 2026, it's an orchestrator for getting multiple agents to work together toward a common goal.

Let's build a minimal version in TypeScript.

## The Gas Town Architecture

Gas Town has three core components:

### 1. The Mayor
The central coordinator. A Claude Code instance with full context about your workspace. You tell the Mayor what you want, and it breaks the work down into tasks.

### 2. Workers
Regular coding agents, each with a specialized role:
- **Architect**: Designs system structure
- **Developer**: Implements features
- **Tester**: Writes and runs tests
- **Reviewer**: Reviews code quality
- **Debugger**: Fixes bugs
- **Documenter**: Writes documentation
- **DevOps**: Handles deployment

### 3. Beads
A Git-backed work tracking system. Each task is a "bead" — a TOML file storing work state. Workers pick up beads, complete them, and update the state.

The genius: **Everything persists in Git**. Agents can crash, restart, and pick up where they left off.

## Why This Matters

Traditional coding agents are single-threaded. One agent, one task, sequential execution.

Gas Town is parallel. Multiple agents, each specialized, all working simultaneously on different parts of the same project.

**Old way**: "Build a user auth system" → 1 agent does everything sequentially

**Gas Town way**: "Build a user auth system" → Mayor splits it → Architect designs schema → Developer implements API → Tester writes tests → All happening in parallel

It's like going from a single-core CPU to multi-core.

## Our Minimal Implementation

We'll build a stripped-down Gas Town with:
- 1 Mayor (task coordinator)
- 3 Worker types (developer, tester, reviewer)
- Simple file-based Beads (no Git, just JSON)

Let's go.

## Step 1: Define the Bead Structure

A Bead is a unit of work. Create `bead.ts`:

```typescript
export type BeadStatus = "pending" | "in_progress" | "completed" | "failed";
export type WorkerRole = "developer" | "tester" | "reviewer";

export interface Bead {
  id: string;
  title: string;
  description: string;
  role: WorkerRole;
  status: BeadStatus;
  assignedTo?: string;
  result?: string;
  error?: string;
  createdAt: number;
  updatedAt: number;
}
```

This is our work tracking. Simple, serializable, persistent.

## Step 2: The Bead Store

We need to read/write beads. Create `bead-store.ts`:

```typescript
import { readFileSync, writeFileSync, existsSync, mkdirSync, readdirSync } from "fs";
import { join } from "path";
import type { Bead } from "./bead";

const BEADS_DIR = ".beads";

export class BeadStore {
  constructor() {
    if (!existsSync(BEADS_DIR)) {
      mkdirSync(BEADS_DIR, { recursive: true });
    }
  }

  save(bead: Bead): void {
    const path = join(BEADS_DIR, `${bead.id}.json`);
    writeFileSync(path, JSON.stringify(bead, null, 2));
  }

  get(id: string): Bead | null {
    const path = join(BEADS_DIR, `${id}.json`);
    if (!existsSync(path)) return null;
    return JSON.parse(readFileSync(path, "utf-8"));
  }

  list(): Bead[] {
    const files = readdirSync(BEADS_DIR).filter((f) => f.endsWith(".json"));
    return files.map((f) => {
      const content = readFileSync(join(BEADS_DIR, f), "utf-8");
      return JSON.parse(content);
    });
  }

  listByStatus(status: Bead["status"]): Bead[] {
    return this.list().filter((b) => b.status === status);
  }

  listByRole(role: Bead["role"]): Bead[] {
    return this.list().filter((b) => b.role === role);
  }
}
```

Persistent work tracking in 40 lines.

## Step 3: The Mayor

The Mayor breaks down high-level goals into specific beads. Create `mayor.ts`:

```typescript
import OpenAI from "openai";
import { BeadStore } from "./bead-store";
import type { Bead, WorkerRole } from "./bead";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY,
});

const MODEL = "anthropic/claude-3.5-sonnet";

export class Mayor {
  private store = new BeadStore();

  async planWork(goal: string): Promise<void> {
    console.log("🏛️  Mayor: Planning work...\n");

    const response = await client.chat.completions.create({
      model: MODEL,
      messages: [
        {
          role: "system",
          content: `You are the Mayor, a task coordinator. Break down user goals into specific tasks.

For each task, specify:
1. A clear title
2. Detailed description
3. The role needed (developer, tester, or reviewer)

Return tasks as JSON array:
[
  {
    "title": "Task title",
    "description": "What to do",
    "role": "developer"
  }
]`,
        },
        { role: "user", content: goal },
      ],
    });

    const content = response.choices[0].message.content || "[]";
    const tasks = JSON.parse(content);

    for (const task of tasks) {
      const bead: Bead = {
        id: `bead-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
        title: task.title,
        description: task.description,
        role: task.role as WorkerRole,
        status: "pending",
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };

      this.store.save(bead);
      console.log(`📋 Created: [${bead.role}] ${bead.title}`);
    }

    console.log(`\n✓ Created ${tasks.length} beads\n`);
  }

  listWork(): void {
    const beads = this.store.list();
    console.log("📊 Work Status:\n");

    const byStatus = {
      pending: beads.filter((b) => b.status === "pending"),
      in_progress: beads.filter((b) => b.status === "in_progress"),
      completed: beads.filter((b) => b.status === "completed"),
      failed: beads.filter((b) => b.status === "failed"),
    };

    for (const [status, items] of Object.entries(byStatus)) {
      console.log(`${status.toUpperCase()}: ${items.length}`);
      items.forEach((b) => console.log(`  - [${b.role}] ${b.title}`));
    }
  }
}
```

The Mayor uses an LLM to intelligently break down goals into actionable beads.

## Step 4: Workers

Workers pick up beads and execute them. Create `worker.ts`:

```typescript
import OpenAI from "openai";
import { BeadStore } from "./bead-store";
import { readFileSync } from "fs";
import { execSync } from "child_process";
import type { Bead, WorkerRole } from "./bead";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY,
});

const MODEL = "anthropic/claude-3.5-sonnet";

const ROLE_PROMPTS: Record<WorkerRole, string> = {
  developer: "You are a Developer. Write clean, functional code. Use tools to create/modify files.",
  tester: "You are a Tester. Write comprehensive tests. Use tools to create test files and run them.",
  reviewer: "You are a Reviewer. Review code for quality, bugs, and best practices. Provide actionable feedback.",
};

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

export class Worker {
  private store = new BeadStore();
  private workerId: string;

  constructor(private role: WorkerRole) {
    this.workerId = `${role}-${Math.random().toString(36).slice(2, 9)}`;
  }

  async work(): Promise<boolean> {
    const beads = this.store.listByRole(this.role).filter((b) => b.status === "pending");

    if (beads.length === 0) {
      return false; // No work available
    }

    const bead = beads[0]; // Take first pending bead
    console.log(`\n👷 ${this.workerId}: Starting [${bead.title}]`);

    // Mark as in progress
    bead.status = "in_progress";
    bead.assignedTo = this.workerId;
    bead.updatedAt = Date.now();
    this.store.save(bead);

    try {
      const result = await this.executeTask(bead);

      bead.status = "completed";
      bead.result = result;
      bead.updatedAt = Date.now();
      this.store.save(bead);

      console.log(`✓ ${this.workerId}: Completed [${bead.title}]`);
      return true;
    } catch (error: any) {
      bead.status = "failed";
      bead.error = error.message;
      bead.updatedAt = Date.now();
      this.store.save(bead);

      console.log(`✗ ${this.workerId}: Failed [${bead.title}] - ${error.message}`);
      return true;
    }
  }

  private async executeTask(bead: Bead): Promise<string> {
    const messages: any[] = [
      {
        role: "system",
        content: ROLE_PROMPTS[this.role],
      },
      {
        role: "user",
        content: `Task: ${bead.title}\n\nDescription: ${bead.description}\n\nComplete this task using the available tools.`,
      },
    ];

    let finalResponse = "";

    for (let i = 0; i < 10; i++) {
      // Max 10 iterations
      const response = await client.chat.completions.create({
        model: MODEL,
        messages,
        tools,
      });

      const message = response.choices[0].message;
      messages.push(message);

      if (!message.tool_calls || message.tool_calls.length === 0) {
        finalResponse = message.content || "Task completed";
        break;
      }

      for (const toolCall of message.tool_calls) {
        const args = JSON.parse(toolCall.function.arguments);
        const result = await executeTool(toolCall.function.name, args);

        console.log(`  [${toolCall.function.name}] ${JSON.stringify(args)}`);

        messages.push({
          role: "tool",
          tool_call_id: toolCall.id,
          content: result,
        });
      }
    }

    return finalResponse;
  }
}
```

Workers are autonomous agents with specialized system prompts based on their role.

## Step 5: The Orchestrator

Tie it all together. Create `gastown.ts`:

```typescript
import { Mayor } from "./mayor";
import { Worker } from "./worker";
import type { WorkerRole } from "./bead";

const WORKER_POOL: WorkerRole[] = ["developer", "developer", "tester", "reviewer"];

async function runGastown(goal: string) {
  const mayor = new Mayor();

  // Step 1: Mayor plans the work
  await mayor.planWork(goal);
  mayor.listWork();

  // Step 2: Spawn workers
  const workers = WORKER_POOL.map((role) => new Worker(role));

  console.log(`\n🏭 Spawned ${workers.length} workers\n`);

  // Step 3: Run workers until all work is done
  let activeWork = true;

  while (activeWork) {
    const promises = workers.map((w) => w.work());
    const results = await Promise.all(promises);

    // If no worker found work, we're done
    activeWork = results.some((r) => r === true);

    if (activeWork) {
      await new Promise((resolve) => setTimeout(resolve, 1000)); // Small delay between rounds
    }
  }

  console.log("\n🎉 All work completed!\n");
  mayor.listWork();
}

const goal = process.argv.slice(2).join(" ");

if (!goal) {
  console.log("Usage: bun gastown.ts <your goal>");
  process.exit(1);
}

runGastown(goal);
```

## Step 6: Running It

```bash
export OPENROUTER_API_KEY="your-key-here"
bun gastown.ts "Build a REST API for a todo list with CRUD operations and tests"
```

### What Happens:

1. **Mayor** receives the goal
2. **Mayor** breaks it down into beads:
   - `[developer]` Create Express server with CRUD endpoints
   - `[developer]` Implement data persistence
   - `[tester]` Write integration tests
   - `[reviewer]` Review API implementation
3. **Workers** spawn and start picking up beads
4. **Two developers** work in parallel on different parts
5. **Tester** writes tests once code exists
6. **Reviewer** checks everything
7. **All work completes** automatically

Workers run in parallel. Multiple developers can implement different endpoints simultaneously. The tester waits for code to exist before testing. The reviewer checks everything at the end.

## The Complete Code Structure

```
gastown/
├── bead.ts           # Type definitions
├── bead-store.ts     # Persistent work tracking
├── mayor.ts          # Task coordinator
├── worker.ts         # Autonomous workers
├── gastown.ts        # Orchestrator
└── .beads/           # Work state (auto-generated)
    ├── bead-xxx.json
    └── bead-yyy.json
```

## Why This Works

**Parallel Execution**: Multiple agents work simultaneously on independent tasks.

**Specialization**: Each worker has a focused role with a specialized system prompt.

**Persistent State**: Work survives crashes. If a worker dies, another picks up the bead.

**Coordination Without Coupling**: Workers don't talk to each other. They just pick up beads. The Mayor doesn't micromanage. It creates beads and walks away.

**Git-Ready**: Our file-based beads could easily be Git-backed. Commit after each bead completion. Full audit trail.

## Extending It

Want to make it production-ready? Add:

### 1. Git Integration
```typescript
function commitBead(bead: Bead) {
  execSync(`git add .beads/${bead.id}.json`);
  execSync(`git commit -m "Completed: ${bead.title}"`);
}
```

### 2. Worker Retry Logic
```typescript
if (bead.status === "failed" && bead.retryCount < 3) {
  bead.status = "pending";
  bead.retryCount++;
  this.store.save(bead);
}
```

### 3. Dependencies Between Beads
```typescript
interface Bead {
  // ... existing fields
  dependsOn?: string[]; // Array of bead IDs
}

// Worker checks dependencies before starting
const canStart = bead.dependsOn?.every(id => {
  const dep = this.store.get(id);
  return dep?.status === "completed";
});
```

### 4. More Worker Roles
```typescript
const ROLE_PROMPTS = {
  architect: "Design system architecture and data models",
  developer: "Implement features",
  tester: "Write and run tests",
  reviewer: "Review code quality",
  debugger: "Fix bugs and errors",
  documenter: "Write documentation",
  devops: "Handle deployment and infrastructure",
};
```

### 5. Streaming Progress
```typescript
// Add WebSocket server to broadcast bead updates
import { WebSocketServer } from "ws";

const wss = new WebSocketServer({ port: 8080 });

function broadcastUpdate(bead: Bead) {
  wss.clients.forEach((client) => {
    client.send(JSON.stringify({ type: "bead_update", bead }));
  });
}
```

## Real-World Gas Town

Steve Yegge's [full Gas Town](https://github.com/steveyegge/gastown) supports:
- 20-30 concurrent workers
- 7 specialized roles
- Full Git integration via Beads
- TOML-based workflow definitions
- Crash recovery and restart
- Multi-project coordination

It's written in Go and integrates with Claude Code and other agent runtimes.

Early reports from the community show mixed results—some developers swear by it for large projects, while others find the overhead unnecessary for small tasks. One developer spent [10 hours in 48](https://medium.com/@enterprisevibecode/10-hours-with-gas-town-out-of-a-possible-48-17a6b2801a73) learning the system.

The verdict: **Gas Town shines for complex, multi-faceted projects where parallel agent execution provides real value.**

## When to Use Gas Town

**Use it when:**
- Building large features with independent sub-tasks
- Multiple specialized roles make sense (API + tests + docs)
- You need parallel execution for speed
- Work needs to survive restarts/crashes

**Don't use it when:**
- Task is simple and linear
- Single agent can handle it
- Coordination overhead exceeds benefits
- You're just starting with agents (learn single-agent first)

## The Future

Gas Town represents the next evolution:

**Phase 1**: Single coding agents (what we built in post 001)

**Phase 2**: Looping agents (Ralph Loop from post 001)

**Phase 3**: Orchestrated multi-agent systems (Gas Town)

We're moving from "one smart agent" to "teams of specialized agents working in parallel."

The question isn't whether this future arrives—it's how fast.

---

## Full Example Code

Here's everything together:

**bead.ts**:
```typescript
export type BeadStatus = "pending" | "in_progress" | "completed" | "failed";
export type WorkerRole = "developer" | "tester" | "reviewer";

export interface Bead {
  id: string;
  title: string;
  description: string;
  role: WorkerRole;
  status: BeadStatus;
  assignedTo?: string;
  result?: string;
  error?: string;
  createdAt: number;
  updatedAt: number;
}
```

**bead-store.ts**:
```typescript
import { readFileSync, writeFileSync, existsSync, mkdirSync, readdirSync } from "fs";
import { join } from "path";
import type { Bead } from "./bead";

const BEADS_DIR = ".beads";

export class BeadStore {
  constructor() {
    if (!existsSync(BEADS_DIR)) {
      mkdirSync(BEADS_DIR, { recursive: true });
    }
  }

  save(bead: Bead): void {
    const path = join(BEADS_DIR, `${bead.id}.json`);
    writeFileSync(path, JSON.stringify(bead, null, 2));
  }

  get(id: string): Bead | null {
    const path = join(BEADS_DIR, `${id}.json`);
    if (!existsSync(path)) return null;
    return JSON.parse(readFileSync(path, "utf-8"));
  }

  list(): Bead[] {
    const files = readdirSync(BEADS_DIR).filter((f) => f.endsWith(".json"));
    return files.map((f) => {
      const content = readFileSync(join(BEADS_DIR, f), "utf-8");
      return JSON.parse(content);
    });
  }

  listByStatus(status: Bead["status"]): Bead[] {
    return this.list().filter((b) => b.status === status);
  }

  listByRole(role: Bead["role"]): Bead[] {
    return this.list().filter((b) => b.role === role);
  }
}
```

**mayor.ts**, **worker.ts**, and **gastown.ts** as shown above.

## Try It

```bash
mkdir mini-gastown
cd mini-gastown
bun init -y
bun add openai

# Create all the TypeScript files above
# Then run:
bun gastown.ts "Your project goal here"
```

Watch multiple agents work in parallel toward your goal.

That's Gas Town.

---

## Sources

- [Welcome to Gas Town by Steve Yegge](https://steve-yegge.medium.com/welcome-to-gas-town-4f25ee16dd04)
- [The Future of Coding Agents by Steve Yegge](https://steve-yegge.medium.com/the-future-of-coding-agents-e9451a84207c)
- [GitHub - steveyegge/gastown](https://github.com/steveyegge/gastown)
- [Wrapping my head around Gas Town - Justin Abrahms](https://justin.abrah.ms/blog/2026-01-05-wrapping-my-head-around-gas-town.html)
- [10 hours with Gas Town (out of a possible 48)](https://medium.com/@enterprisevibecode/10-hours-with-gas-town-out-of-a-possible-48-17a6b2801a73)
- [All Gas Town, No Brakes Town](https://www.todayintabs.com/p/all-gas-town-no-brakes-town)
- [Welcome to Gas Town - Hacker News](https://news.ycombinator.com/item?id=46458936)
- [Gas Town Emergency User Manual](https://steve-yegge.medium.com/gas-town-emergency-user-manual-cf0e4556d74b)
