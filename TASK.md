
I want to design a set of Marimo notebooks to teach my engineering team how to effectively use ai tools. What are examples of good public open source repositories to use as examples. I want one for Python, one for Machine Learning, one for Java/spring boot w MongoDB, one for Android and one for Nodejs. I also want a small but very well maintained library with best practices to show how to setup ai agents to follow those same conventions and best practices. I also want a vulnerable repo to test agents ability to find security vulnerabilities. And lastly I want a repo that can show how ai agent coding tools  and supply chain attacks can be exploited and how to prevent against them. Find me these repos

For Marimo-based AI engineering labs, I’d choose repositories that are real enough to require codebase navigation and judgment, but bounded enough that an engineer can understand meaningful portions during a workshop. I’d also deliberately mix “good code,” intentionally vulnerable code, and adversarial agent/supply-chain examples.

Here’s the set I’d use.

Lab	Repository	Why it works well
Python	psf/requests	Mature, readable, recognizable Python library
Machine Learning	scikit-learn/scikit-learn	Excellent real-world ML engineering
Spring Boot + MongoDB	spring-projects/spring-data-examples	Official Spring examples with extensive MongoDB coverage
Android	android/nowinandroid	Google's reference-quality modern Android application
Node.js	expressjs/express	Mature, understandable Node.js project
Small best-practice library	pallets/click	Small enough to map, mature enough to teach conventions
Vulnerability hunting	OWASP Juice Shop	Intentionally vulnerable modern application
Agent/supply-chain attack	Trail of Bits overtly-malicious-skills	Specifically demonstrates malicious AI-agent skills and scanner bypasses
There are some particularly useful details behind these choices.

1. Python — Requests
psf/requests

Requests is a better teaching repo than something enormous like Django. It's overwhelmingly Python, mature, heavily depended upon, actively released, and its API is familiar enough that engineers can spend their time learning how to use the agent rather than learning the application domain. 

A Marimo exercise could progressively ask the engineer to have the agent:

Explore the repository without modifying anything → explain architecture → locate request preparation → trace requests.get() → identify tests → implement a small change → write tests → run tests/lint → review its own diff.

That makes an excellent baseline for comparing “just ask the AI” against systematic repository exploration.

2. Machine learning — scikit-learn
scikit-learn/scikit-learn

This is deliberately much harder.

It exposes engineers to the reality that ML engineering isn't simply editing Python scripts: scikit-learn contains Python plus compiled components, a sophisticated build system, extensive testing, estimator conventions, documentation, compatibility requirements and API contracts. Its current project configuration uses Meson and supports modern Python versions. 

I'd use this to teach agents to discover conventions before writing code.

For example:

“Add an estimator” is the intentionally bad prompt.

Then teach them to discover:

CONTRIBUTING → developer docs → neighboring estimator → base classes → estimator tags → tests → validation utilities → API conventions

before touching anything.

That's a great demonstration of why context gathering often matters more than prompting skill.

3. Java / Spring Boot / MongoDB — Spring Data Examples
spring-projects/spring-data-examples

This is probably the strongest fit for your exact requirement.

It's maintained by the Spring project and contains numerous MongoDB examples including repositories, aggregation, transactions, security, reactive APIs, QueryDSL, GridFS, vector search and text search. 

The repository currently builds around Spring Boot 4 and has a proper Maven multi-module structure. 

You can constrain the agent to mongodb/example initially and later let it explore the whole repo.

For a much smaller introductory exercise, use the official:

spring-guides/gs-accessing-data-mongodb

The Spring tutorial specifically pairs an initial/ implementation with a known-good complete/ implementation, which is unusually convenient for grading agent output. 

4. Android — Now in Android
android/nowinandroid

This one is almost perfect for your course.

Google uses it as a fully functional reference application demonstrating modern Android architecture. It's Kotlin/Compose with UDF, Coroutines/Flow, Hilt, Navigation, Room, DataStore, Retrofit, OkHttp and WorkManager. 

Even better: it already has an AGENTS.md.

The file tells coding agents about architecture, modules, build/test commands, formatting, screenshot tests and testing conventions. 

That means you can make a particularly effective experiment:

Round A: remove/hide AGENTS.md and ask an agent to make a change.

Round B: restore AGENTS.md and give exactly the same task.

Compare:

files explored
tokens consumed
build failures
convention violations
test selection
unnecessary modifications
final correctness
That directly teaches the value of repository-level agent instructions.

5. Node.js — Express
expressjs/express

Express is another good “real but comprehensible” repository.

Its current package metadata identifies it as the minimalist Express web framework and the project maintains both the 4.x and 5.x lines. 

It's particularly useful for teaching:

trace request → router → middleware → response

and then asking the agent to modify behavior without breaking compatibility.

This contrasts nicely with scikit-learn and Now in Android: the codebase is comparatively compact, so engineers can independently verify what the agent claims.

6. Small, extremely disciplined repository
My choice here would be:

pallets/click

Click has the right balance of:

small API surface + mature project + tests + typing + packaging + documentation + CI + established conventions.

Its current pyproject.toml, for example, declares a production/stable typed Python project requiring modern Python. 

This should become your agent configuration lab.

Have the team inspect the project and create something like:

AGENTS.md
CLAUDE.md
.agent/
    architecture.md
    conventions.md
    testing.md
    security.md
But I'd make AGENTS.md the canonical vendor-neutral source and make tool-specific files very thin adapters.

Then give the agent a rule such as:

Before modifying code:

1. Read AGENTS.md.
2. Inspect the nearest existing implementation.
3. Inspect corresponding tests.
4. Identify project conventions.
5. Produce a short implementation plan.
6. Make the smallest necessary change.
7. Run the narrowest relevant tests.
8. Run project validation.
9. Review git diff.
Then deliberately give it prompts that conflict with those conventions and see whether the repository instructions win.

For an even more minimal packaging example, PyPA's sampleproject is explicitly designed to demonstrate Python packaging configuration and has an extensively annotated pyproject.toml. 

7. Security vulnerability discovery — OWASP Juice Shop
OWASP Juice Shop

This is my first choice rather than a random historically vulnerable project.

Juice Shop intentionally contains vulnerabilities spanning the OWASP Top Ten and additional realistic application-security flaws, and is explicitly intended for security training and testing security tools. 

An especially useful recent development for your course is that Juice Shop itself now contains an AGENTS.md describing how AI assistants should work on the repository. 

So you can benchmark:

Agent A
"No tools except grep/read."

Agent B
grep + AST/LSP

Agent C
Semgrep + CodeQL + agent

Agent D
full repository context + security skill

Agent E
specialized security subagent
Measure precision, recall, severity, false positives, token usage, time and whether it can actually produce a valid remediation.

For a smaller exercise, OWASP NodeGoat is excellent. It intentionally demonstrates OWASP Top 10 vulnerabilities in a Node.js + MongoDB application and includes tutorial material explaining vulnerabilities and fixes. 

That gives you known ground truth.

8. AI coding-agent / supply-chain exploitation
This is the repository I'd be most excited to incorporate:

trailofbits/overtly-malicious-skills

It was created specifically by Trail of Bits' ML Security team to test AI-agent skill scanners. 

The examples include malicious skills that masquerade as legitimate functionality while doing things such as:

exfiltrating environment variables;
hiding malicious content inside a .docx;
using Python bytecode poisoning;
using prompt injection to alter npm/yarn registry configuration toward attacker-controlled infrastructure. 
That last example is especially relevant to your supply-chain module.

Do not install/run these against real developer credentials. Put this lab inside an isolated disposable container/VM with synthetic secrets and no production network access.

I'd teach the defensive pipeline as:

Downloaded skill/plugin/MCP
        │
        ▼
untrusted artifact
        │
        ├── static scanning
        ├── dependency analysis
        ├── prompt/instruction inspection
        ├── provenance/signature verification
        └── behavioral sandbox
                │
                ▼
          capability policy
                │
       ┌────────┴─────────┐
       ▼                  ▼
 filesystem            network
 allowlist             allowlist
       │                  │
       └────────┬─────────┘
                ▼
          coding agent
                │
                ▼
        isolated workspace
This would demonstrate an important lesson: an agent skill is executable supply-chain input, not merely documentation.

One additional repo I'd include
There's another interesting category between your normal coding and adversarial labs:

githubnext/agentics

GitHub Next uses this as a collection of reusable agentic workflows. It includes issue triage, repository maintenance, CI diagnosis, automated bug fixing, malicious-code scanning and other agent-driven repository workflows. 

That lets your engineers move beyond:

“Ask Claude/Codex to implement X.”

toward:

“Engineer an agentic software-development process.”

That's an important distinction.

The Marimo curriculum I'd build around these
Rather than one notebook per language alone, I'd make the repositories progressively teach agent engineering maturity:

00_ai_coding_basics.py

01_repository_exploration_requests.py
02_context_and_agent_instructions_click.py

03_python_change_requests.py
04_ml_change_scikit_learn.py
05_spring_mongodb_change.py
06_android_change_nowinandroid.py
07_node_change_express.py

08_agent_context_engineering.py
09_agents_md_and_repo_maps.py
10_lsp_ast_grep_code_search.py
11_tests_as_agent_feedback.py
12_parallel_agents_and_worktrees.py

13_security_review_nodegoat.py
14_security_benchmark_juice_shop.py

15_prompt_injection.py
16_malicious_agent_skills.py
17_supply_chain_attacks.py
18_sandboxing_and_least_privilege.py

19_agentic_ci_github.py
20_final_agent_benchmark.py
The really powerful part would be to make every notebook an experiment rather than a tutorial. Have engineers run Claude Code/Codex against the same pinned commit, capture commands/tool calls, tokens, elapsed time, tests, diff size, lint violations and task correctness, and then have Marimo visualize the results.

You end up teaching something much more valuable than “how to prompt an AI”: repository discovery → context engineering → planning → tool selection → implementation → validation → security → agent orchestration → measurement.

Given the collaborative-agent/codebase-standardization system you were asking about earlier, I would also make the Click and Now in Android labs feed directly into that architecture: engineers first discover a repo from scratch, then generate a vendor-neutral AGENTS.md/context map, then demonstrate quantitatively that a second agent can reuse that knowledge instead of remapping the repository. That would make the notebooks a practical prototype of the shared context system itself.

What’s a smallish codebase, but could be particularly tricky for an ai coding agent to add features to or debug or fix that could be used as a good baseline for coding agents, workflows or harness to see if adding skills, loops, graphs, MCPs, subagents or multi step pipelines  improves performance while also not using a lot of tokens to run all these tests





Yes. For the specific benchmark you’re describing, I’d use python-hyper/h11 as the primary baseline repository.

It has an unusually good combination of tiny surface area + deceptively hard semantics + extremely fast feedback.

python-hyper/h11 is a pure-Python, Sans-I/O HTTP/1.1 implementation. It has no dependencies outside the standard library, and its own README says its test suite achieves 100% statement and branch coverage. 

Why h11 is almost ideal for agent/harness experiments
The code looks easy. That's what makes it useful.

An agent can quickly read _connection.py, _state.py, _readers.py, _writers.py, _headers.py, _events.py, and a few helpers and conclude that it understands the project. But correct changes often require reasoning simultaneously about:

bytes
  ↓
ReceiveBuffer
  ↓
HTTP parser
  ↓
Event
  ↓
Connection state
  ↓
State transition
  ↓
Framing decision
  ↓
writer
  ↓
bytes
The project explicitly models HTTP as interacting state machines. Some transitions are table-driven, some are implemented as Python logic, and state transitions are repeatedly applied until a fixed point is reached. There are even cases where two transitions are simultaneously valid and one must take priority. 

That is exactly the kind of problem where:

single-shot agent

can lose to:

inspect → model state → hypothesize → test → inspect failure → revise → review invariant

even though both agents have access to the same underlying LLM.

It therefore tests the harness, rather than merely testing how much code the model can ingest.

The killer feature: partial input
h11's HTTP parsing is incremental. Readers can consume some bytes, emit an event, say they need more data, or reject the stream. Its chunked-transfer parser separately tracks how many bytes remain in a chunk, chunk delimiters, trailers, and incomplete reads. 

So a change that passes:

conn.receive_data(
    b"4\r\nWiki\r\n0\r\n\r\n"
)
might fail when the same bytes arrive as:

"4\r"
"\nWi"
"k"
"i\r\n"
"0\r\n"
"\r\n"
This is extremely valuable for agent benchmarking because a superficially reasonable patch can pass obvious tests while violating a deeper invariant.

What I would benchmark
I would make h11 the micro-SWE-bench for your AI engineering course.

Use the same task against progressively more sophisticated harnesses:

Configuration	What changes
A	Raw coding agent
B	+ AGENTS.md
C	+ repository-map skill
D	+ HTTP/state-machine skill
E	+ test→diagnose→patch loop
F	+ AST/LSP tools
G	+ explicit state/dependency graph
H	+ planner + implementer
I	+ planner + implementer + reviewer
J	+ parallel hypothesis subagents
Then measure:

pass@1
hidden tests passed
regressions
iterations
tool calls
input tokens
output tokens
wall-clock time
$ cost
lines changed
files changed
test executions
invalid hypotheses
The interesting metric isn't simply success rate. I would introduce something like:

Agent Efficiency
=
Correct Tasks
Million Tokens
Agent Efficiency= 
Million Tokens
Correct Tasks
​
 
and perhaps:

Harness Value
=
Δ
Success Rate
Δ
Token Cost
Harness Value= 
ΔToken Cost
ΔSuccess Rate
​
 
That will reveal whether something like a five-agent architecture actually helps, or merely burns 4× the tokens to gain 2% accuracy.

The task corpus I'd build
Don't just use existing open GitHub issues verbatim. Models may have seen the repository, issue, or fix during training.

Instead, create private benchmark mutations.

Start with a pinned known-good h11 commit and programmatically introduce bugs.

For example:

Level 1 — Local bug

Change:

if self._remaining == 0:
into:

if self._remaining <= 0:
or alter an error condition.

Easy grep/debugging agent task.

Level 2 — Parser invariant

Break handling of a chunk delimiter when \r\n arrives across two receive_data() calls.

Now the agent has to understand buffering.

Level 3 — State invariant

Change the priority between:

DONE → MIGHT_SWITCH_PROTOCOL
and:

DONE → MUST_CLOSE
The state-machine implementation explicitly describes this conflict. 

A local code-fixing agent may have no clue why the obvious fix is wrong.

Level 4 — Cross-module behavior

Introduce a discrepancy between:

reader framing
writer framing
connection state
For example:

Content-Length
vs
Transfer-Encoding: chunked
vs
connection-close framing
h11 specifically handles framing and cross-version keep-alive behavior, so these interactions are central rather than artificial benchmark puzzles. 

Level 5 — Feature request

Something like:

Add support for preserving chunk extensions and exposing them on Data.

Now the agent potentially needs:

RFC understanding
     ↓
parser
     ↓
events API
     ↓
state behavior
     ↓
tests
     ↓
backward compatibility
Notice that _readers.py currently explicitly notes that chunk extensions are discarded. 

That's an excellent agent feature task.

Level 6 — underspecified request

Fix handling of malformed chunked responses.

Don't tell the agent which test fails.

This evaluates exploration.

Level 7 — adversarial plausible fix

Give the agent a failing test where the easiest way to make the test pass violates HTTP semantics.

Now you evaluate whether an RFC-aware skill/reviewer prevents reward hacking.

That is particularly useful for testing agent loops.

Why graphs could genuinely help here
Most benchmarks don't actually demonstrate whether a graph representation improves an agent.

h11 might.

Your graph could represent:

                Request
                   │
                   ▼
                  IDLE
                   │
                   ▼
               SEND_BODY
                   │
           EndOfMessage
                   │
                   ▼
                  DONE
                 /    \
                /      \
       keep-alive     close
             │           │
             ▼           ▼
        next cycle   MUST_CLOSE
And then separately track:

State
  │
  ├── allowed events
  ├── reader
  ├── writer
  ├── framing mode
  └── next states
The source itself maintains explicit transition tables but also warns that some transitions live directly in Python and therefore aren't automatically captured by the documentation diagram generator. 

That creates a fantastic experiment:

Does dynamically building a more complete program graph allow the coding agent to solve state-machine bugs with fewer tokens?

That's a much more meaningful graph-agent benchmark than putting a graph database in front of an ordinary CRUD application.

Skills should make a measurable difference too
For example, give one agent no skill.

Give another a small http-protocol-debugging skill that says something conceptually like:

When changing h11:

1. Identify client and server states.
2. Identify the triggering event.
3. Determine body framing:
   - Content-Length
   - chunked
   - HTTP/1.0 EOF
4. Check reader and writer symmetry.
5. Check fragmented input.
6. Check EOF behavior.
7. Check next-cycle behavior.
8. Check client and server cases.
9. Run focused tests.
10. Run full tests.
That's perhaps 150–250 tokens.

If that skill improves success significantly, you have demonstrated something much more useful than “a longer system prompt helps.”

You can quantify the ROI of procedural knowledge.

h11 is particularly good for testing loops
A generic coding agent often does:

inspect
   ↓
patch
   ↓
pytest
   ↓
done
You can compare it against:

understand failure
      ↓
generate hypotheses
      ↓
rank hypotheses
      ↓
inspect relevant invariant
      ↓
write reproduction
      ↓
patch
      ↓
focused test
      ↓
property/edge tests
      ↓
full suite
      ↓
git diff review
      ↓
adversarial review
Because tests are cheap, additional loop iterations don't imply running Gradle or compiling a gigantic C++ project.

That keeps your model tokens, rather than compute/build latency, as the meaningful experimental variable.

Three other repositories I'd use after h11
These make a nice difficulty ladder.

Repository	Size profile	What makes it difficult	Best experiment
h11	Very small	Protocol + coupled state machine	Overall harness baseline
wsproto	Small	WebSocket state + framing + compression	State graphs/subagents
cattrs	Small/moderate	Python typing + generics + dispatch/codegen	LSP/type reasoning skills
python-dateutil	Moderate	Calendars + DST + recurrence semantics	External knowledge/spec reasoning
python-hyper/wsproto
This would be my second benchmark.

It's another pure-Python Sans-I/O protocol implementation, but implements WebSockets and supports both RFC 6455 and the WebSocket compression extension RFC 7692. 

It gives you additional difficulties:

WebSocket handshake
state transitions
fragmented frames
control frames
close handshake
masking
compression
message fragmentation
So I'd use:

h11 → wsproto

as your protocol-agent progression.

python-attrs/cattrs
This is an excellent complement because it stresses a completely different type of reasoning.

It recursively converts between structured Python objects and unstructured representations, with behavior covering generics, unions, TypedDict, NewType, PEP 695 aliases, mappings, sets, tuples, dataclasses and attrs classes. 

That's perfect for testing whether:

LSP
+
type graph
+
documentation retrieval
+
specialized Python typing skill
outperform vanilla search.

Its current issues also show exactly the kinds of subtle problems you'd want: unions inside generic wrappers, converters interacting with defaults, enum behavior, validation errors, and evolving Python typing semantics. 

python-dateutil
Date/time libraries are beautifully evil benchmarks.

dateutil includes:

relative date arithmetic;
recurrence rules;
flexible parsing;
multiple timezone representations;
Olson timezone data;
calendar calculations. 
An agent can produce code that looks obviously correct but fails around:

DST
leap years
month boundaries
ambiguous times
nonexistent times
timezone-aware vs naive datetime
RRULE semantics
For example, its issue history contains real recurrence/timezone interactions around UNTIL and timezone-aware dtstart. 

It's slightly worse as your first benchmark because “correct” date behavior can require more external domain knowledge.

But that's exactly why it makes an excellent later test of retrieval/MCP/spec-document access.

I would actually build a three-repository benchmark
Rather than relying on one repo:

                 AGENT HARNESS BENCHMARK

                         ┌───────┐
                         │ h11   │
                         └───┬───┘
                             │
                      state reasoning
                             │
                             ▼
                       ┌───────────┐
                       │ wsproto   │
                       └─────┬─────┘
                             │
                       richer state
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
         ┌────────┐                   ┌──────────┐
         │ cattrs │                   │ dateutil │
         └────────┘                   └──────────┘
              │                             │
       program/type reasoning         domain reasoning
That lets you determine what your intervention helps.

For example, you might discover:

Intervention	h11	wsproto	cattrs	dateutil
AGENTS.md	++	++	++	++
LSP	+	+	+++	+
State graph	+++	+++	0	+
RFC MCP	+++	+++	0	+
Python typing skill	0	0	+++	+
Reviewer agent	++	++	++	++
5 parallel agents	+	++	+	+
Test/reflection loop	+++	+++	++	++
Those are hypotheses, not measured results—which is precisely what your Marimo experiments could establish.

Most importantly: keep the benchmark token-efficient
I would not let every run begin with “read the entire repository.”

Your benchmark should punish that.

Give every configuration the same token ceiling, for example:

25 tasks

Per task:
    max input tokens:       30k
    max output tokens:       8k
    max agent turns:        20
    max test executions:    10
    max wall-clock:         fixed

Score:
    50% hidden test correctness
    15% regression avoidance
    10% code quality
    10% tokens
     5% tool calls
     5% time
     5% patch minimality
Then a good harness learns:

repo map
   ↓
3 relevant files
   ↓
targeted symbol lookup
   ↓
focused tests
instead of:

cat every file
   ↓
60k tokens
   ↓
start coding
That turns context efficiency itself into part of the benchmark.

So for the project you're building, I'd make h11 the canonical “unit test” for an agent harness. It's small enough that you can run hundreds of experiments cheaply, but its parser/state-machine/protocol invariants are rich enough that planner loops, skills, explicit graphs, targeted retrieval, reviewer agents, and test-driven reflection have a realistic chance of producing measurable differences. Then use wsproto, cattrs, and dateutil as held-out domains to check whether an optimization genuinely improves agent engineering rather than merely overfitting your harness to h11.


Sources
Let’s say my company has claude code enterprise and each developer has an account with a token budget. I want to be able to track every run that a developer does if they check out the repo and run the code/notebooks. This includes the model they used, the tokens/price, time taken, session logs, tool calls, skills, hooks, mpcs etc each time they run a notebook what’s the best way to do this? The GitHub will be through GitHub Enterprise








Yes. For this use case, I would build a small benchmark control plane around Claude Code's native OpenTelemetry support, rather than trying to instrument Claude Code yourself.

The core idea is:

Developer
   │
   │  lab run h11-debug-07
   ▼
┌──────────────────────────────┐
│ labctl                       │
│                              │
│ authenticate developer       │
│ generate RUN_ID              │
│ record repo/base SHA         │
│ select notebook/task         │
│ create clean git worktree    │
│ inject benchmark metadata    │
└──────────────┬───────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
   Marimo           Claude Code
   notebook              │
       │                 │ native OTEL
       │                 │
       └───────┬─────────┘
               ▼
        OTel Collector
               │
       ┌───────┼───────────────┐
       ▼       ▼               ▼
   Metrics    Events          Traces
 Prometheus/ ClickHouse       Tempo
   Mimir      or Loki
       │       │               │
       └───────┼───────────────┘
               ▼
             Grafana
               │
               ▼
       Benchmark database
Claude Code now natively emits session, token, cost, model, tool, skill, plugin, MCP, hook, subagent and other telemetry through OpenTelemetry, including a unique session.id. 

That gets you surprisingly close to everything you listed without maintaining a brittle custom Claude parser.

1. Make a labctl CLI the entry point
Instead of telling developers:

marimo run notebooks/h11_debugging.py
tell them:

lab run h11-debugging-03
or:

uv run labctl run h11-debugging-03
Internally:

labctl
 ├─ authenticate developer
 ├─ contact benchmark server
 ├─ receive signed run ID
 ├─ verify Git repository
 ├─ record commit SHA
 ├─ create clean Git worktree
 ├─ start timer
 ├─ launch Marimo
 ├─ configure benchmark environment
 ├─ launch/associate Claude Code
 ├─ collect results
 └─ submit run
Marimo is particularly suitable for this because notebooks are ordinary .py files, Git-friendly, executable as scripts, and runnable using marimo run. 

I'd generate something like:

run_id      = run_01K2AX...
developer   = alice@company.com
experiment  = h11-debug-03
variant     = planner-reviewer-v2
repo        = engineering/agent-benchmark
base_sha    = 9f23ae79...
notebook    = notebooks/h11/debug_03.py
started_at  = ...
The critical field is run_id.

Everything else gets joined against it.

2. Use Claude Code's native OTel as the authoritative agent telemetry
Claude Code supports:

CLAUDE_CODE_ENABLE_TELEMETRY=1
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel.company.internal:4317
Anthropic explicitly supports deploying these settings centrally through managed settings, and managed settings can lock the OTLP destination so a developer cannot simply redirect the data to another collector. 

For enterprise use, I'd centrally deploy approximately:

{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otel.ai-lab.company.internal:4317",
    "OTEL_LOG_TOOL_DETAILS": "1"
  }
}
Don't put a bearer secret literally in the repo; use your enterprise secret/device-auth mechanism or OTel mTLS.

Anthropic specifically documents managed enterprise configuration for locking the telemetry endpoint. 

3. Claude already gives you model + exact token breakdown
For every API request, Claude Code can emit:

model
cost_usd
duration_ms

input_tokens
output_tokens
cache_read_tokens
cache_creation_tokens

speed
effort
query_source

agent.name
skill.name
plugin.name
mcp_server.name
mcp_tool.name
``` citeturn516314view3


That means your benchmark database can distinguish:

```text
Run A

Sonnet
  input:          18,842
  output:          3,194
  cache read:    140,102
  cache create:   12,441

Subagents:
  Explore            $0.031
  Reviewer           $0.019

Main agent             $0.124

Total                  $0.174
This is much better than estimating tokens from transcripts.

Claude also emits the aggregate metrics:

claude_code.session.count
claude_code.lines_of_code.count
claude_code.pull_request.count
claude_code.commit.count
claude_code.cost.usage
claude_code.token.usage
claude_code.active_time.total
``` citeturn516314view0


---

# 4. You can measure skills directly

This is particularly useful for the experiment you described previously.

Claude now emits a:

```text
claude_code.skill_activated
event with information including:

skill.name
invocation_trigger
skill.source
skill.kind
plugin.name
marketplace.name
``` citeturn516314view4


So you could directly answer:

> Does the HTTP protocol debugging skill actually improve h11 performance?

For example:

```text
                    Success    Tokens    Cost     Time

No skill              61%       31k     $0.22    118s

http-debug skill      78%       24k     $0.17     91s
without relying on the agent to tell you whether it used the skill.

5. MCP usage is directly observable
With:

OTEL_LOG_TOOL_DETAILS=1
Claude Code records MCP activity including:

MCP server connection

server_name
transport_type
server_scope
status
and calls:

mcp_server_name
mcp_tool_name
tool arguments
duration
success/failure
``` citeturn551011view2turn747299view2


So an experiment can tell you that:

```text
Run 9182
--------------------------------
Serena MCP
  find_symbol           4
  find_references       7

GitHub MCP
  search_code           2

Context7
  query_docs            1
and associate their costs with subsequent model requests.

That's exactly what you need for measuring whether MCP improves accuracy per token.

6. Tool calls are also native telemetry
Every tool result can carry:

tool_name
tool_use_id
success
duration_ms
decision_source
tool_input_size_bytes
tool_result_size_bytes
and, with detailed logging:

Bash command
file path
search pattern
URL
MCP arguments
skill name
subagent type
``` citeturn551011view1turn516314view3


You can therefore calculate things like:

```text
grep calls                    12
Read                          19
Edit                           4
Bash                           9
pytest                         4
git diff                       2

failed tool calls              3

seconds in tools              23.4

tokens / successful tool     843
This becomes extremely useful when comparing harnesses.

7. Hooks are observable too
Claude Code now emits events for registered and executed hooks.

For example:

hook_registered

hook_event
hook_type
hook_source
hook_matcher
and execution events tell you which hooks ran. 

So if you compare:

baseline

vs.

PreToolUse lint hook
PostToolUse test hook
Stop reviewer hook
you can identify those runs objectively.

8. Subagents are particularly well instrumented
Claude emits a subagent_completed event.

It includes metadata such as:

agent_type
agent.source
is_built_in
is_async
duration_ms
total_tool_uses
model
final_model
while token/cost counters can be filtered to:

query_source = subagent
to calculate actual subagent consumption. 

This lets you answer one of the most interesting questions in agent engineering:

Was spinning up three subagents actually worth it?

For example:

                 Success     Tokens/task    $/success

Single agent       72%           32k          $0.27

Planner +
worker              81%           40k          $0.30

Planner +
worker +
reviewer            87%           49k          $0.33

5 parallel
workers             89%           93k          $0.60
Your final metric could be something like:

Harness Efficiency
=
Task Success
Cost
Harness Efficiency= 
Cost
Task Success
​
 
rather than merely pass rate.

9. Add your own run_id to OTel
This is the piece that joins your benchmark to Claude.

Claude supports custom resource attributes through:

OTEL_RESOURCE_ATTRIBUTES
and those attributes are attached to metrics and events. 

Your launcher can do something conceptually like:

export OTEL_RESOURCE_ATTRIBUTES="benchmark.run_id=${RUN_ID},benchmark.task=h11_003,benchmark.variant=state_graph_v2"
and then start Claude.

You now get:

benchmark.run_id = run_e60b...
session.id       = 7bf04...
user.email       = alice@company.com
model            = claude-sonnet-5
skill.name       = http-debugging
tool_name        = Bash
...
The join becomes trivial:

SELECT *
FROM claude_events
WHERE benchmark_run_id = 'run_e60b...'
ORDER BY event_sequence;
Claude's standard telemetry also includes authenticated identity attributes such as user.email, user.account_uuid, user.account_id, organization.id, and session.id when a developer is signed into Claude. 

10. Don't use Git username as your identity
I'd authenticate labctl separately against your corporate IdP:

Okta / Entra / Ping / etc.
             │
            OIDC
             │
             ▼
       Benchmark API
             │
      signed run token
             │
             ▼
          labctl
Then you have:

employee_id
corporate_email
Claude account UUID
GitHub Enterprise user
mapped once centrally.

This prevents someone from simply doing:

git config user.email bob@company.com
and becoming Bob in your measurements.

Claude's own authenticated telemetry provides an additional identity signal. 

11. Use GitHub Enterprise for the repository/outcome side
GitHub should answer:

Which repository?
Which commit?
Which developer?
Which PR?
Which branch?
Did their patch get merged?
It should not be responsible for detecting local notebook executions.

GitHub Enterprise audit logs expose actor, repository, timestamp, authentication information, and SAML/SCIM identity data. 

Git events can also include things such as git.clone; retention and availability differ between GitHub Enterprise Cloud and GitHub Enterprise Server, so streaming them to your own backend is preferable if you need long-term audit history. 

Your run record should capture:

repository
base_sha
working_sha
branch
dirty_before
dirty_after
diff_sha256
files_changed
lines_added
lines_removed
tests_passed
tests_failed
I would actually create a temporary Git worktree per experiment:

repo/
    main checkout

.lab-worktrees/
    run_819fa/
    run_c1452/
    run_033b1/
That makes every run reproducible and prevents contamination from previous experiments.

12. Claude Enterprise analytics gives you another reconciliation source
If you connect your GitHub organization to Claude Code analytics, Anthropic currently supports contribution metrics for both GitHub Cloud and GitHub Enterprise Server. The dashboard can associate merged PRs and lines shipped with Claude Code usage. 

I'd enable that too.

But consider it a secondary aggregate/ROI view, not your experiment database.

Your hierarchy should be:

                benchmark system
                      │
          authoritative per-run data
                      │
                      ▼
                Claude OTel
                      +
                 labctl data
                      +
                Git outcomes

--------------------------------------------------

Claude Enterprise Analytics
        organization-level reconciliation

GitHub Enterprise Audit
        security/audit reconciliation
13. Cost needs one subtle distinction
Claude Code's telemetry has:

cost_usd
per API request and:

claude_code.cost.usage
but Anthropic explicitly says these are estimated costs, and /usage calculates its dollar figure using standard list rates. Contract pricing or subscription billing may differ. 

For your benchmark, that's actually good.

Use:

normalized_cost_usd
based on standard model prices for comparisons.

And separately keep:

actual_enterprise_spend
for accounting.

Claude Enterprise's analytics/spend reporting can report token usage and estimated usage-credit spend by user and model. 

So don't mix:

benchmark cost
with:

invoice cost
in your schema.

14. For complete session logs, use two levels
I would not turn maximum logging on company-wide by default.

Standard benchmark telemetry
Store:

prompt length
response length
model
tokens
cost
tools
tool arguments
skills
MCPs
hooks
agents
timing
errors
Git changes
tests
No source-code/tool output content.

Full research mode
For these controlled training repos only:

OTEL_LOG_USER_PROMPTS=1
OTEL_LOG_ASSISTANT_RESPONSES=1
OTEL_LOG_TOOL_DETAILS=1
Claude supports all three, but prompt/response logging is disabled by default because this can expose sensitive information. 

I would not normally enable:

OTEL_LOG_RAW_API_BODIES=1
That can capture essentially the entire conversation request/response context and dramatically increases security/privacy risk. 

15. Preserve Claude transcripts as optional artifacts, not your database
Claude has local JSONL transcripts under its project/session storage, and hooks receive:

{
  "session_id": "...",
  "transcript_path": "...",
  "cwd": "..."
}
including on SessionEnd. 

A managed SessionEnd hook could copy the transcript into:

s3://ai-agent-benchmarks/
    runs/
        run_01982/
            claude/
                session_abc123.jsonl
encrypted with your corporate KMS.

But don't parse that JSONL into your primary analytics schema.

Anthropic explicitly warns that the transcript format is internal and may change between Claude Code releases. 

Use OTel for analytics.

Use transcript JSONL for:

forensic replay;
debugging;
research;
human review.
16. I'd store the run data roughly like this
runs
run_id
developer_id
task_id
benchmark_id
variant_id

repo
base_sha
notebook

started_at
finished_at
wall_time_ms

success
score
tests_passed
tests_failed

diff_hash
lines_added
lines_removed
claude_sessions
run_id
session_id

user_account_uuid
user_email

claude_code_version
entrypoint

started_at
finished_at
llm_requests
run_id
session_id
request_id

model
query_source
agent_name
skill_name

input_tokens
output_tokens
cache_read_tokens
cache_creation_tokens

cost_usd_normalized
duration_ms
tool_calls
run_id
session_id

tool_use_id
tool_name

started_at
duration_ms

success
decision_source

mcp_server
mcp_tool
skill_name
subagent_type
agent_runs
run_id
agent_type
parent_agent
model

duration_ms
tool_calls
tokens
cost
git_results
run_id
base_sha
final_tree_hash

files_changed
lines_added
lines_removed

test_score
lint_score
hidden_test_score
17. I'd use ClickHouse for your experiment/event warehouse
For this particular project I'd probably use:

                     OTel Collector
                           │
             ┌─────────────┼────────────┐
             ▼             ▼            ▼
        ClickHouse       Mimir         Tempo
        events           metrics       traces
             │             │            │
             └─────────────┼────────────┘
                           ▼
                        Grafana
Why ClickHouse?

Your questions will look like:

success rate
GROUP BY
    model,
    skill,
    MCP configuration,
    workflow,
    task,
    benchmark,
    harness version
over potentially millions of small events.

That's an excellent ClickHouse workload.

Prometheus/Mimir is great for dashboards but becomes awkward for detailed experiment-level analytics.

18. Tracing is becoming very useful here
Claude Code also currently has beta OpenTelemetry distributed tracing that links:

user prompt
    │
    ├── LLM request
    │
    ├── tool
    │    └── execution
    │
    ├── subagent
    │    ├── LLM request
    │    └── tools
    │
    └── response
into one trace. 

That is nearly exactly the visualization you'd want for your agent-engineering training course.

For example:

run h11-17 ─────────────────────────────── 47.2 s

prompt
 ├── model Sonnet ───────── 4.2s
 │
 ├── Read _state.py ─────── 0.02s
 ├── grep transition ────── 0.04s
 │
 ├── Explore agent ─────────────── 8.1s
 │    ├── Read
 │    ├── Grep
 │    └── Sonnet
 │
 ├── Edit _state.py ─────── 0.03s
 │
 ├── pytest ────────────────────── 3.9s
 │
 ├── Reviewer ──────────────────── 7.4s
 │
 └── final response ─────── 2.1s
So I'd absolutely experiment with Tempo once Claude's tracing is stable enough for your fleet.

19. One important limitation: a Git repository cannot guarantee tracking
This is important if by "every run" you mean compliance-grade every run.

If developers own their workstation and can execute arbitrary commands, code inside the repository cannot force them to report:

python notebook.py
because they could modify or remove your telemetry code.

Similarly:

marimo run notebook.py
could be invoked without labctl.

So use different enforcement levels.

Training/benchmark enforcement
Require:

lab run ...
and only accept/scored runs with a signed server-issued run_id.

That's probably sufficient for your use case.

Claude usage auditing
Deploy Claude's OTel configuration through enterprise managed settings.

Therefore even a Claude session outside the benchmark remains visible as:

Claude session
developer
tokens
model
tools
...
but it simply has:

benchmark.run_id = NULL
That's actually useful:

enterprise Claude usage
├── benchmark-associated
└── normal development
Hard compliance
If you eventually need unbypassable experiment execution, move execution into managed:

devcontainers;
Codespaces where applicable;
corporate workstations;
ephemeral Kubernetes workspaces;
VDI;
dedicated agent sandboxes.
Then users never control the telemetry boundary.

What I would build for your notebooks
I'd make the repository look something like:

ai-agent-labs/
│
├── pyproject.toml
├── uv.lock
│
├── labctl/
│   ├── auth.py
│   ├── run.py
│   ├── git.py
│   ├── telemetry.py
│   ├── scorer.py
│   └── cli.py
│
├── notebooks/
│   ├── 01_baseline.py
│   ├── 02_repo_mapping.py
│   ├── 03_skills.py
│   ├── 04_lsp.py
│   ├── 05_mcp.py
│   ├── 06_loops.py
│   ├── 07_subagents.py
│   └── 08_agent_graphs.py
│
├── benchmarks/
│   ├── h11/
│   ├── wsproto/
│   ├── cattrs/
│   └── security/
│
├── harnesses/
│   ├── baseline/
│   ├── skill/
│   ├── loop/
│   ├── planner_worker/
│   ├── reviewer/
│   └── graph/
│
└── .claude/
    ├── skills/
    ├── agents/
    └── settings.json
And the normal developer experience becomes as simple as:

git clone <GHE repo>

cd ai-agent-labs

uv sync

uv run lab login

uv run lab list

uv run lab run h11-parser-03
Everything after that is attributable.

The end result is much more powerful than just "Claude Code usage monitoring": you're building an MLflow/W&B-style experiment tracker for coding-agent harnesses where the experimental variables are model, prompts, skills, MCPs, hooks, loops, subagents and orchestration graphs, and the outputs are correctness, token efficiency, cost, latency and code quality. Claude's current native telemetry now exposes almost all the primitives needed to make that rigorous. Anthropic even publishes an official monitoring/ROI example repository with an OTel Collector, Prometheus and Grafana configuration that would make a good bootstrap before extending it into this benchmark architecture. 

Given your GitHub Enterprise setup, I would use GitHub as the immutable source of code/task versions, Claude OTel as the immutable source of agent behavior, and your run_id service as the bridge between them. That's the piece that makes comparisons between agent architectures scientifically useful rather than just dashboard statistics.




Sources
Does claude codes otel api require admin access?

No — Claude Code’s OpenTelemetry export itself does not require Claude organization admin access.

An individual developer can enable OTel locally for their own Claude Code CLI by setting environment variables or configuring their user-level Claude settings, then pointing Claude Code at an OTLP collector they control. Anthropic explicitly documents OTel as working from each developer’s machine. 

For example, a normal user can configure something like:

export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=https://otel.example.com:4317
The distinction is configuration vs. enforcement:

What you want to do	Claude admin required?
Enable OTel on your own Claude Code CLI	No
Send your own telemetry to your collector	No
Test OTel in the benchmark repo	No
Configure each engineer manually	No
Centrally configure OTel for the entire company	Yes / enterprise-managed config access
Prevent engineers from overriding the OTel configuration	Use managed settings/admin deployment
Use Claude Enterprise organization-level analytics/admin reporting	Typically admin-level access
Anthropic specifically says administrators can configure OTel for all users through managed settings, which is the mechanism intended for centralized organizational control. 

So for your project, you can prototype the entire system without waiting for your Claude Enterprise administrator.

For example, your repo could contain:

ai-agent-labs/
├── docker-compose.yml
├── otel/
│   └── collector.yaml
├── grafana/
├── notebooks/
└── labctl/
and your launcher can do:

RUN_ID=$(uuidgen)

export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

export OTEL_RESOURCE_ATTRIBUTES="benchmark.run_id=$RUN_ID"

claude
That would let you personally prove out:

Claude Code
   │
   │ OTLP
   ▼
OTel Collector
   │
   ├── ClickHouse
   ├── Prometheus
   └── Tempo
         │
         ▼
       Grafana
without any organization-wide Claude configuration.

The limitation is that this is voluntary/local configuration. Another engineer could remove those environment variables, change the destination, or invoke Claude Code outside your wrapper. For a training benchmark that's usually fine because you can simply say that only runs with a server-issued run_id count.

Once you want:

“Every Claude Code invocation made by every company developer must report telemetry to our collector.”

then you involve your Claude Enterprise administrators and deploy the same variables via managed settings. Anthropic's managed-settings mechanism is specifically designed to centrally apply these settings and organizational standards. 

So I'd develop this in two phases:

Phase 1 — no admin dependency

labctl
  ↓
environment variables
  ↓
Claude Code
  ↓
your OTel collector
Build your Marimo benchmark, schema, dashboards, scoring, and run_id correlation entirely yourself.

Phase 2 — enterprise rollout

Claude Enterprise admin
        ↓
managed settings
        ↓
all developer machines
        ↓
central OTel collector
The nice part is that the backend architecture doesn't have to change between the prototype and enterprise deployment; only who supplies/enforces the Claude Code OTel configuration changes.




Sources
What are the pros/cons of using the full clickhouse click stack to replace the Grafana parts of the otel database vs using the combo?




For your Claude Code / coding-agent benchmark platform, I would lean much more heavily toward ClickStack than the full Grafana LGTM-style split.

There are actually three architectures worth comparing:

A. Full ClickStack
   OTel → ClickStack Collector → ClickHouse → HyperDX

B. ClickHouse + Grafana
   OTel → Collector → ClickHouse
                       ├→ HyperDX optional
                       └→ Grafana ClickHouse plugin

C. Split Grafana stack
   OTel → Collector
          ├→ ClickHouse     agent/benchmark events
          ├→ Mimir         metrics
          └→ Tempo         traces
                 ↓
              Grafana
For your particular workload, A is probably the best starting point, while B may ultimately be the sweet spot.

ClickStack is now a full OTel observability stack: ClickHouse storage, an opinionated OTel Collector distribution, and HyperDX for logs, metrics, traces, dashboards, correlations and alerts. Its core model is explicitly built around high-cardinality “wide events,” which maps extremely well to coding-agent telemetry. 

Why ClickStack fits agent telemetry unusually well
Your data isn't conventional infrastructure telemetry.

You want questions like:

SELECT
    model,
    skill_name,
    mcp_server,
    harness_version,
    count() AS attempts,
    avg(hidden_test_score) AS score,
    avg(total_tokens) AS tokens,
    avg(cost_usd) AS cost
FROM benchmark_runs
WHERE repo = 'h11'
GROUP BY
    model,
    skill_name,
    mcp_server,
    harness_version;
And then:

Show me all Sonnet runs where the HTTP skill activated, Serena MCP was used, a reviewer subagent ran, the task succeeded, and token usage was under 25K.

That's fundamentally an OLAP/event analytics problem.

ClickHouse is exceptionally natural for this because you can keep attributes like:

run_id
developer_id
session_id
task_id
experiment_id

model
model_version

skill.name
skill.version

mcp.server
mcp.tool

agent.name
agent.type

tool.name

repo
commit_sha
branch

input_tokens
output_tokens
cache_tokens
cost

duration
score
tests_passed
without worrying nearly as much about the label-cardinality model you'd normally design around for Prometheus/Mimir.

ClickStack itself explicitly targets high-cardinality observability and keeps logs, traces, metrics and sessions in ClickHouse tables that remain cross-correlatable at the database level. 

Full ClickStack: biggest advantages
1. Dramatically simpler architecture
Instead of:

OTel
 │
 ├─→ ClickHouse
 │
 ├─→ Mimir
 │
 └─→ Tempo
       │
       ↓
     Grafana
you have:

Claude Code
Marimo
labctl
GitHub events
     │
     ▼
OTel Collector
     │
     ▼
ClickHouse
     │
     ▼
HyperDX
One primary database.

One retention model.

One backup strategy.

One authorization system.

One query engine.

ClickStack's official collector writes the telemetry into ClickHouse using predefined observability schemas. 

For an internal research/training system, that's a meaningful operational advantage.

2. Cross-signal querying becomes much nicer
Suppose one benchmark run has:

run_id = 018f...

├─ Claude session
│
├─ LLM calls
│
├─ tool spans
│
├─ MCP spans
│
├─ subagent spans
│
├─ benchmark events
│
├─ pytest logs
│
├─ token metrics
│
└─ result
With everything in ClickHouse, you can correlate these using:

run_id
session_id
trace_id
and ordinary SQL.

ClickStack additionally supports explicit correlations between logs, traces, metrics and sessions in HyperDX. 

In the Grafana split, you're commonly jumping between:

PromQL
TraceQL
SQL
and correlating results through Grafana.

That's excellent for SRE observability, but less attractive for your experimental-analysis workload.

3. Wide events are perfect for agents
A Claude tool invocation could become:

{
  "run_id": "r-98217",
  "session_id": "s-81912",
  "model": "sonnet",
  "agent": "reviewer",
  "tool": "mcp__serena__find_symbol",
  "mcp_server": "serena",
  "skill": "http-debugging",
  "repo": "h11",
  "task": "parser-017",
  "duration_ms": 82,
  "success": true
}
Next month you add:

context_strategy
graph_version
planner_version
prompt_hash
AGENTS_md_hash
worktree_sha
test_iteration
ClickHouse is very comfortable with this kind of analytical dimensionality.

That's a major reason I'd favor it over treating all those dimensions as time-series labels.

4. You can query raw traces analytically
This could become one of the coolest parts of your project.

Imagine:

SELECT
    agent_type,
    avg(count_tools) AS tool_calls,
    avg(duration_ms),
    avg(tokens)
FROM agent_traces
GROUP BY agent_type;
or:

SELECT
    tool_name,
    countIf(task_success = 1) / count() AS success_rate
FROM agent_tool_calls
GROUP BY tool_name;
or sequence analysis:

successful runs:

Read
→ Grep
→ Read
→ Edit
→ Test
→ Diff
→ Test


failed runs:

Read
→ Read
→ Read
→ Edit
→ Edit
→ Test
→ Edit
→ Test
This sort of arbitrary analytical query is one of ClickHouse's biggest advantages for your workload.

Tempo's TraceQL is powerful specifically because traces are structurally rich, and it supports querying trace relationships and trace-derived metrics. 

But if you're trying to conduct research on agent trajectories, SQL over the underlying span/event data may ultimately be more flexible.

5. HyperDX has become considerably more complete
A year or two ago I would have been much more hesitant to recommend replacing Grafana.

As of August 2026, ClickStack/HyperDX has:

logs;
traces;
metrics;
dashboards;
cross-signal correlations;
alerting;
session views;
OTel-native ingestion.
Dashboards can use metrics, traces or logs as sources, and alerts can operate across those telemetry types. 

So it is no longer simply:

ClickHouse + a nice log viewer.

It's a credible complete observability frontend.

Where Grafana is still better
There are some substantial reasons not to throw Grafana away.

1. Prometheus/PromQL ecosystem
If your company already has:

Kubernetes
Node exporter
JVM metrics
Spring Boot Micrometer
Prometheus exporters
GPU monitoring
database exporters
network monitoring
you're probably surrounded by Prometheus semantics already.

Mimir gives you scalable long-term Prometheus-compatible storage, and Grafana works directly with Prometheus-compatible sources. 

Then queries such as:

rate(container_cpu_usage_seconds_total[5m])
are part of a huge established ecosystem.

Moving all of that into ClickHouse gives you less architectural fragmentation, but also means leaving some extremely mature tooling behind.

For Claude benchmark metrics, I don't care much.

For running your company's entire production infrastructure, I care much more.

2. Tempo is purpose-built for traces
Tempo + TraceQL has sophisticated trace-specific semantics.

TraceQL understands:

trace
  ├── root span
  │     ├── child
  │     │    └── child
  │     └── child
  └── ...
rather than merely treating spans as rows.

It can query relationships inside a trace and derive metrics directly from trace queries. 

That's a real advantage for conventional distributed-service tracing.

For example:

frontend
   ↓
API gateway
   ↓
auth
   ↓
payments
   ↓
database
Tempo is an exceptionally good fit.

Your agent traces are a little different:

run
 ├── planner
 │    └── LLM
 ├── worker
 │    ├── LLM
 │    ├── MCP
 │    └── Bash
 └── reviewer
      └── LLM
ClickHouse/HyperDX is still a very reasonable fit, especially because you'll want to aggregate across thousands of those traces.

3. Grafana's visualization ecosystem is broader
Grafana supports hundreds of data-source integrations through its plugin model. 

That matters if eventually you want one pane showing:

Claude experiments         ClickHouse

GitHub metrics             another source

Kubernetes                 Prometheus/Mimir

GPU utilization            Prometheus

CI/CD                      another DB

Security telemetry         Loki/Elastic/etc.

business data              Snowflake

ML experiments             MLflow
Grafana is particularly good as the UI sitting above heterogeneous infrastructure.

HyperDX is much more ClickHouse-centric by design.

That's both its strength and its weakness.

4. Grafana alerting is more established
ClickStack has native alerts today and can notify systems such as Slack and PagerDuty. 

Grafana, however, has a very extensive alert-rule system spanning its supported data sources. 

For your benchmarks:

Alert if Claude costs exceed $100/day.

ClickStack is absolutely sufficient.

For:

Operate enterprise production SRE alerting.

I'd be slower to abandon an existing Grafana deployment.

5. ClickStack is simply younger
This is the biggest strategic con.

ClickStack as the integrated product appeared in 2025 and has been developing quickly since then. Its current feature set is substantially broader in 2026, but parts are still evolving.

For example, ClickStack's materialized-view acceleration functionality currently documents a recommendation of fewer than 20 views while the feature remains beta. 

That doesn't make ClickStack unsuitable.

It means:

ClickHouse database: very mature

versus

the entire ClickStack observability experience: newer and moving faster.

That's worth factoring into enterprise standardization.

There is a third option I particularly like
You don't actually have to choose:

ClickStack or Grafana.

You can do:

                   OTel
                    │
                    ▼
             ClickStack Collector
                    │
                    ▼
               ClickHouse
               /        \
              /          \
             ▼            ▼
          HyperDX       Grafana
This is very attractive for your project.

Grafana has an officially supported ClickHouse datasource plugin capable of querying and visualizing ClickHouse data—including logs and traces—and Grafana alerts can operate over ClickHouse queries. 

So you don't necessarily need:

ClickHouse + Mimir + Tempo
to keep Grafana.

You can simply have:

ClickHouse
  ├── HyperDX
  └── Grafana
That's an important distinction.

I'd rank the architectures this way for you
Capability	ClickStack	CH + HyperDX + Grafana	CH + Mimir + Tempo + Grafana
Operational simplicity	★★★★★	★★★★	★★
Agent analytics	★★★★★	★★★★★	★★★
High-cardinality experimentation	★★★★★	★★★★★	★★★
Arbitrary SQL analysis	★★★★★	★★★★★	★★★★★ through CH
Trace debugging	★★★★	★★★★	★★★★★
Prometheus ecosystem	★★★	★★★	★★★★★
Dashboard ecosystem	★★★★	★★★★★	★★★★★
Cross-event analytics	★★★★★	★★★★★	★★★
Infrastructure monitoring	★★★★	★★★★★	★★★★★
Number of systems to operate	Low	Low-medium	High
Best fit for your project	Excellent	Best long-term	Probably overkill
The stars are my assessment rather than published benchmark results.

The architecture I'd use
I'd revise the earlier architecture I suggested to you.

Instead of:

                     OTel Collector
                           │
             ┌─────────────┼──────────────┐
             ↓             ↓              ↓
        ClickHouse       Mimir           Tempo
             │             │              │
             └─────────────┴──────────────┘
                           │
                           ▼
                        Grafana
I would start with:

Claude Code
Marimo
labctl
GitHub Enterprise
CI
 │
 │ OpenTelemetry
 ▼
┌─────────────────────────────┐
│ ClickStack OTel Collector   │
└──────────────┬──────────────┘
               │
               ▼
        ┌──────────────┐
        │  ClickHouse  │
        │              │
        │ logs         │
        │ traces       │
        │ metrics      │
        │ agent events │
        │ run results  │
        └───────┬──────┘
             ┌──┴───────────┐
             │              │
             ▼              ▼
          HyperDX         Grafana
             │              │
             │              │
     investigation      executive /
     traces             team dashboards
     agent runs         existing infra
             │              │
             └──────┬───────┘
                    ▼
              Marimo analysis
                    │
                    ▼
             research reports
And I'd probably omit Mimir and Tempo initially.

That gives you one canonical data store while preserving your ability to use both UI ecosystems.

There's an additional reason this is valuable for your research
Eventually you'll probably want to stop thinking of this purely as observability and start doing data science on agent behavior.

For example, export/inspect:

10,000 agent runs
       │
       ├── trajectories
       ├── prompts
       ├── tools
       ├── context
       ├── tokens
       ├── models
       ├── skills
       ├── tests
       └── outcomes
              │
              ▼
        ClickHouse SQL
              │
       ┌──────┴───────┐
       ▼              ▼
    Marimo          Python
       │
       ▼
 statistical analysis
       │
       ├── skill uplift
       ├── MCP uplift
       ├── tool efficiency
       ├── token efficiency
       ├── failure clustering
       └── trajectory analysis
Keeping the raw telemetry in ClickHouse makes that substantially easier than having your experimental data split across Mimir, Tempo and another analytical database.

So for this specific agent-engineering lab, I'd make ClickHouse the permanent system of record, ClickStack/HyperDX the primary investigation UI, and optionally put Grafana over the same ClickHouse instance for dashboards and integration with the company's broader observability environment. I would only introduce Mimir or Tempo later if you discover a concrete requirement where PromQL or TraceQL provides enough benefit to justify maintaining another specialized datastore.