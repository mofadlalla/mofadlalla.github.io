---
layout: post
title: 'The Evil of Optional Parameters: When Having too Many Options is Self Destructing'
description: 'How optional parameters in function signatures lead to impossible states, hidden coupling, and fragile APIs—and better design alternatives.'
date: 2026-10-09 20:50:00 -0400
---

You are the main developer of agents.com, an app that lets an organization manage an army of AI agents. You’re designing an admin page where an admin within an org can see each agent and the skills associated with them. You write this beautiful, simple function that takes an `orgId` and `agentId` and returns a list of skills:

```typescript
function getAgentSkills(orgId: string, agentId: string): AgentSkill[] {
  // fetches all of the skills from the server
}
```

The skills page needs to show some metadata along with the list of skills. For example, we need to show the name of the agent, the date they were created, and their specialties. Because of this, we make a small change to the return type of this function:

```typescript
interface AgentSkillsResponse {
  agent: Agent;
  skills: Skill[];
}

function getAgentSkills(orgId: string, agentId: string): AgentSkillsResponse {
  // Some API calls
}
```

So far, so good! The page looks great, and admins are happy tracking their agents' contributions.
<br/>
### The Original Sin of Convenience
The agent section contains more than just a list of skills. You have independent pages for tasks, relations, and a high-level overview page. On the overview page, you want to show the top five agent skills.

However, you really don't want to return the `agent` object with the response here because you already have the agent information handy in the state, and you want to save yourself a heavy database join in your backend.

So, what do you do? You commit the first sin. You add a boolean optional parameter `includeAgent`. It defaults to true, and the overview page caller can just set it to false. Here is how your function looks now:
```typescript
function getAgentSkills(
  orgId: string,
  agentId: string,
  includeAgent?: boolean = true
): AgentSkillsResponse {
  // fetches skills and includes agent conditionally
}
```
But wait, you also need to update the function return type because the agent is now optional:
```typescript
interface AgentSkillsResponse {
  agent?: Agent;
  skills: Skill[];
}
```
Not bad, right? We'll see.
<br/>
### Descending Deeper: The Second Offense
Months later, your app is doing great. You are getting feature requests left and right. You need help, so you hire a new developer.

The first feature they work on is the UI for "deleted" agents. When an agent is deleted, you free up their username so new agents can use it. But new agents can be deleted as well! Your backend has a clever solution for this: you store a `deletionTimeStamp` to identify multiple agents deleted with the exact same username.

Your new developer wants to support showing skills for deleted agents on the skills page. What do they do? They pass a `deletedAt` param into your existing function. Because of data retention regulations, you don't store a lot of information about deleted agents, so the response shape is a bit different.
```typescript
interface AgentSkillsResponse {
  agent?: Agent;
  deletedAgent?: DeletedAgent;
  skills: Skill[];
}

function getAgentSkills(
  orgId: string,
  agentId: string,
  includeAgent?: boolean = true,
  deletedAt?: DateTime,
): AgentSkillsResponse {
  // fetches skills and includes agent conditionally
}
```
Look closely at this function. The good news is that it returns a list of skills. But does it include an active agent or a deleted agent? Only God knows. Even worse, an agent cannot be active and deleted at the same time. What happens when someone passes `includeAgent=true` and `deletedAt=Date(SOME_DATE)` ? The function signature allows an impossible state.
<br/>

### Knocking on Hell's Door
As your business grows, you start allowing users to have more control over agents. However, this feature is only rolled out to an allowlisted set of users for A/B testing. You call this feature `AgentControl`.

When this feature is enabled, you expect the agent object to include more attributes—for example, `allowed_tools`, `memory_config`, and `guardrail_profile_id`. So, you add another optional parameter.

```typescript
function getAgentSkills(
  orgId: string,
  agentId: string,
  includeAgent?: boolean = true,
  deletedAt?: DateTime,
  isAgentControlEnabled: boolean = false,
): AgentSkillsResponse {
  // fetches skills and includes agent conditionally
}
```

Keep in mind, the `isAgentControlEnabled` param is only relevant when fetching active agents. Deleted agents will always return the minimum response. This function already looks terrible, but there's no turning back now.

### If You're Going Through Hell, Keep Going
Believe it or not, there are cases where optional parameters actually seem completely justified. Your skills service is heavily cached. When a new skill is added in the UI, or when the user clicks a manual refresh button, you want to invalidate the cache and force loading fresh data.

What do you do to our function? I think you know the answer by now.

```typescript
function getAgentSkills(
  orgId: string,
  agentId: string,
  includeAgent?: boolean = true,
  deletedAt?: DateTime,
  isAgentControlEnabled?: boolean = false,
  invalidateCache?: boolean = false
): AgentSkillsResponse {
  // fetches skills and includes agent conditionally
}
```
<br/>

### Dragging the Rest of the Team Down With You
This is one of the worst functions I have ever seen in my life. Look at what we have done to the developers consuming this API. To simply fetch a fresh list of skills for an active agent with the control features turned on, this is what the call site looks like:
```typescript
getAgentSkills('org1', 'agent1', true, undefined, true, false)
```
A string of random booleans and an `undefined` placeholder just to satisfy the TypeScript compiler.

It gets worse. Because our API is lying about its domain, consumers are forced to write defensive garbage code just to figure out what response they actually got back:

```typescript
const response = getAgentSkills(...);

if (response.agent) {
  // render active agent UI
} else if (response.deletedAgent) {
  // render deleted agent UI
} else {
  // Wait, what does this even mean? Did includeAgent fail? 
}
```
Optional parameters didn't remove complexity; they just pushed the cognitive load onto everyone else.
<br/>

### The Path to Redemption (And How Rust Forces It)
When a function accumulates optional parameters like this, it’s a massive red flag that your domain model is muddy. The function is doing too much.

Do we even need optional parameters at the language level? The creators of Rust didn't think so. In Rust, there is no such thing as an optional function argument. If you tried to write our `getAgentSkills` function in Rust, the compiler would force you to design a strictly typed struct for your configuration, or force you to pass an explicit `Option` type.

Instead of passing random booleans, Rust forces you to encapsulate the behavior. Applied to our TypeScript codebase, the virtuous approach looks like this:

1. Split the Execution Threads
Fetching an active agent and fetching a deleted agent are fundamentally different operations. They deserve distinct functions: `getActiveAgentSkills()` and `getDeletedAgentSkills()`.

2. Use an Options Object for Modifiers
For genuine behavioral modifiers, pass a single, strongly-typed configuration object instead of positional arguments.

```typescript
interface FetchSkillOptions {
  includeAgentMetadata?: boolean;
  invalidateCache?: boolean;
  enableAgentControl?: boolean;
}

function getActiveAgentSkills(
  orgId: string, 
  agentId: string, 
  options?: FetchSkillOptions
): ActiveAgentResponse { ... }
```

Now, calling it is self-documenting:
```typescript
getActiveAgentSkills('org1', 'agent1', { invalidateCache: true });
```

### The Two Golden Commandments of Optional Parameters
This isn't to say optional parameters are fundamentally evil everywhere. But if you want to keep your codebase clean, you should strictly limit them to two scenarios:

#### 1. Enriching or Formatting the Response
Use optional parameters when the core operation remains exactly the same, but the shape of the output changes. Think of CLI commands like `docker ps --format json`. The system is still listing containers; it's just handing you the data differently.

#### 2. Overriding Function Defaults
Use them to expose underlying knobs that usually don't need to be touched, like `timeout=30ms` or `retries=3`.

**The Unforgivable Sin**: You should never use an optional parameter to change the execution thread. If passing `true` makes your function hit a different database table, execute a different business rule, or return a fundamentally different entity (like switching from an Active Agent to a Deleted Agent), you don't need an optional parameter. You need a new function.
<br/>

### Conclusion: Escaping the Inferno
Optional parameters almost always start as a harmless convenience. But a parameter is rarely truly "optional"—it is a branching path in your logic. When you pile them up to control the flow of your program, you aren't making your function more flexible; you are creating a combinatorial explosion of states that you, and your team, will eventually have to debug.

Repent for your muddy domains. Write dumb functions. Keep your signatures strict. Your future self will thank you.
