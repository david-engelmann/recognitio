[Back to the documentation index](README.md)

# The Build 7 mod, in process hooks for the review fan out

## At a glance

**What ships**

The hooks module under `hooks/` with its host side tests, registering one agent.spawn hook that gates a reviewer spawn on the packet manifest verified flag, and the recognitio-mod marketplace entry under `plugins/recognitio-mod/` carrying byte identical copies of the module.

**What was proven**

The module validates clean on Claude Code 2.1.314 with its agent.spawn hook named in the gating hooks report with its catch flag set, and the module ran live on that build across headless sessions, a streamed session, the marketplace install route and the root plugin route. The five packet states stand proven on the headless route, where a spawn over a verified packet passed, a spawn over an unverified packet was denied in the gate's own words, spawns over a missing or corrupt manifest were denied through the catch handler, and a spawn with no packet configured proceeded untouched. The unverified packet was also denied on the streamed, marketplace and root plugin routes.

**What is unverified**

Agent team teammate spawns, the Desktop and VS Code surfaces, and an induced catch handler timeout stand unverified. The catch handler limit itself stands as the recorded limit section states it, on the primary events guide's word and the reference's one second limit for catch handlers.

## Summary

Build 7 adds an in process hook on the home platform that reads
the packet manifest when a reviewer spawn is about to start and
lets the spawn through only when the manifest reads verified.
The mod ships in this repo as the hooks module and its host side
tests under hooks, beside the portable core and outside the
canonical skill text. The contract lives in the sections below,
and the gate at scripts/check_mod.py pins the module list, the
spawn hook and its fail closed deny handler.

This document is the brief for the Build 7 Claude Code mod.
The mod lives under `hooks/` beside the portable core, not
in the canonical skill text. It exploits the Mods surface,
the strongest enforcement point on the home platform, with
the `agent.spawn` handler gating the reviewer fan out and
the `.catch` handler returning a deny shape as the fail
closed mechanism. Decision 4 binds this build like every
other build.

The marketplace listing at `.claude-plugin/marketplace.json`
offers the mod as its own marketplace entry, named
recognitio-mod and sourced from `plugins/recognitio-mod/`.
That folder carries its own manifest and byte identical
copies of the hooks module, its host side tests and the
root LICENSE, so a setup can install the spawn gate
without the skill bundle. The gate pins the copies to
the originals, so the two can never drift apart. The main recognitio
plugin already includes the mod, because the hooks folder
at the repo root loads with that plugin, and the install
prose tells the reader to install one shape or the other
and never both.

## What the mod does

The hooks module at `hooks/register.js` registers one hook
on the `agent.spawn` event. When a subagent or an agent team
teammate is about to start, the hook reads the review packet
manifest named by the `RECOGNITIO_PACKET_DIR` environment
variable and applies the shipped deterministic rule. The
manifest's `verified` flag is the whole check. A packet
whose manifest reads verified lets the spawn through. A
packet whose manifest is missing, unreadable, unparsable,
or not verified denies the spawn with a reason. A
manifest that names one key twice at any level reads
as not verified, so the last value in the file cannot win
a flag an earlier value refused. That is the same
refusal the packet gate's strict reader stamps on the
same bytes. When no
packet directory is configured, the mod is inert and the
spawn passes through, because the mod enforces the review
workflow and is not a global spawn gate.

The hook never calls a model. No model judgment replaces
the manifest check. The hook's only mods API calls are
`$.fs.read` and `$.env.get`.

The mod needs Claude Code v2.1.287 or later, the first
build with mods, and stands live tested on 2.1.314.

## The fail closed mechanism

The `agent.spawn` registration carries a `.catch` handler.
A hook refuses an action by returning the deny shape, and
the events guide prescribes the catch handler as the way a
hook that blocks calls keeps its refusal standing when the
hook itself fails. When the gate hook throws or times out before it
answers, the host calls the catch handler with the same
event, and the handler returns the deny shape for
`agent.spawn`, which is `{ deny: reason }`. A crashed hook
denies the spawn rather than letting it through. That is
the fail closed mechanism, and the gate pins it. A mod
hook shipped without a `.catch` handler fails the repo
gate.

## The recorded limit

If the catch handler itself throws or times out, the host
skips the hook as if it had no handler and the spawn
proceeds. A hook crash is denied only while the catch
handler itself runs clean. This second layer fail open is
a stated limit of the build, not a surprise. The brief
states it here and the gate pins the sentence, so a later
edit cannot quietly drop the limit.

## The gating boundary

The hook sees only in session agent spawns. Reviewers the
Build 6 runbook starts as `claude -p` subprocesses are not
in session spawns, and the mod does not see them. That
path stays gated by the run record validator at
`scripts/check_fanout.py`, not by this mod. The mod and
the validator cover different spawn shapes, and the brief
states which is which so no reader mistakes the
enforcement for wider than it is.

## The disabled mods degradation

When mods are disabled or unavailable, the mod never
loads and nothing about the scripts changes. The packet
is still gated by `scripts/check_packet.py` before any
reviewer spawns, and the run record is still gated by
`scripts/check_fanout.py` after the second pass. The mod
wraps the gate and degrades gracefully to it, which is
what decision 4 requires.

## The deployment gate

The build's gate check on a host with the CLI is
`claude plugin validate --json` on the plugin
directory. Its `gatingHooks` report names every mod
hook that can refuse an action with a `hasCatch`
flag, and the build requires the flag set on the
`agent.spawn` hook. On Claude Code 2.1.314 the report
names the hook exactly so, in the contents entry for
`hooks/hooks.json`. Validation refuses a module whose
environment read names its variable through anything
but a string literal, which is how the first shipped
module failed, as the live run correction below
records. The options object file read passes
validation, and only the live run and the repo gate
below catch that shape. The host side test
story is `claude plugin test`, which runs the
`*.test.ts` files under `hooks/` with no session,
sign in, or network, firing the event through the
loaded module against stubs in the documented shapes.
Where the CLI is absent, `scripts/check_mod.py` pins
what source inspection can hold. That pinning is scoped
to the structural family the section after this one
enumerates, and a module standing outside the family is
refused rather than judged. The `hooks/hooks.json`
module list, the `.catch` handler, the deny shape, and
the limit sentence above are pinned as before, and the
mods API allowlist stands pinned as before, so a call
to any mods API beside `$.fs.read` and `$.env.get`
fails the gate. The registration pin reads the module
with its comments stripped and judges every registration
call whose first argument is a string literal the host
reads as the `agent.spawn` event name, an escaped
spelling of that name included. Each judged call must
stand in the statement flow of the register function
the host calls, outside every conditional branch and
after no statement that cannot fall in its sequence,
with a plain block, a statement level try block, a
finally block and a do body counting as that flow, and
it must be the only
registration for the event, because the host refuses a
module that registers the event twice. The flow is
read through the one completion calculus the outcome
judgement below reads, so a sequence closed by an
unconditional throw, by an if and an else whose
branches both return, by a returning catch answering
a throwing try, or by a switch whose clauses all
return stands closed to a call after it the same way
a sequence closed by a return does, a finally block
counts as the flow even where the try it answers
returns, because the finally runs on that path too,
and a call standing in a later comma separated
segment of a statement counts as reached, because the
comma ends the segment before it and nothing in that
segment governs the next. A labelled statement reads
as the statement it labels, so a flow the labelled
statement closes stands closed the same way, and a
break that leaves a labelled statement stands for a
fall where the statement is no loop or switch, since
that break ends the statement it labels. The handler a
call registers must be the gating handler, read as a
handler whose own body and the local functions it
reaches through bare local calls standing in its own
code between them call the environment read and the
file read and produce the deny shape on one of its outcomes,
so a handler that approves every spawn certifies
nothing. The two calls are judged the way
the call pins below judge them, as call sites standing
in code position outside every literal span, in the
handler's own code or in the code of a function it
reaches that way, so a call spelling quoted inside a
string or a template text, or standing inside a
nested function the handler never calls, counts for
nothing, a callee counts only where the call that
reaches it stands reached in its own unit's flow, so
a callee the handler calls only on a governed branch
counts for nothing, and a call counts for the
presence of the two reads where it stands reached or
on governed ground in a unit the handler reaches,
never where its sequence has closed, so calls
standing after a closing return count for nothing
the same way, and a function the handler invokes at the
very site where it stands counts as the handler's own
code, since its body runs where it stands, while a
declaration followed by a parenthesised expression
counts for nothing, since the parenthesis there opens
a separate statement and the declaration never runs,
and the deny outcome is read through as many
levels of delegation as the handler chains, so a
handler that delegates its gating to a helper that
delegates in turn reads as the gating handler it is.
A `.catch` handler must stand on that call's
own chain, its spaced spelling included, and the
handler it names is judged by its binding as at the
registration call, a rebinding before the call counting
and a rebinding after it not counting, with a binding
by a destructuring assignment or a destructuring
declaration counting the same way at the value
standing at the name's own key path in the right hand
side, in any declarator of the declaration, for the
catch handler name, the gating handler
name and every name the deny judgement reads alike. A
function declaration binds when its scope is
instantiated, before any statement of the scope runs,
so an assignment standing before the declaration in
the text is the binding in force wherever the
declaration stands, the ordering every binding
judgement in this gate reads. The catch
handler must return or produce the deny shape on every
outcome it can produce, where every return expression,
every bare return, every throw no catch inside the
handler answers, and the end of the body where control
can reach it counts as an outcome, so a comment or a
string carrying the registration, catch or deny
spellings certifies nothing, and a handler written as
a function declaration, a function expression or an
arrow, with a block or an expression body, stands
judged the same. A deny outcome counts through a helper
call whose own outcomes all deny, through as many
levels of helpers as the module chains, under a
computed key that spells the deny name as a plain
template, as a decoded literal or as a template whose
interpolations are string literals spelling the name
between them, through a spread of a bound object
whose own reading carries the deny key, and as the
first side of a fallback expression whose first side
carries it, because a deny object is truthy and so
stands as the value the fallback produces, and as
the first side of a nullish fallback the same way,
since a deny object is never nullish and a merely
falsy first operand still stands as the value a
nullish fallback produces. A bare
name standing as an outcome counts where every value
the name can hold when the handler runs carries the
deny shape, the values read from the bindings that
run before it in their written order, the module top
level first, then the register function the host
calls at load, then the handler's own function up to
the return, with a binding standing in the statement
flow settling the value and a binding standing on
governed ground adding a value the name can hold, so
the last assignment standing anywhere in the module
text decides nothing on its own. The gating handler
of the same registration runs on the spawn path
before the catch handler can run, so the values it
and the functions it reaches bind add values the name
can hold without settling it, since the crash can
come before any of them runs or after any of them,
and the functions the catch handler itself reaches
before the return run as part of its own run, at the
place of the call that reaches them. A name bound by
a catch clause around the return is judged by the
throws of that clause's try block, the feeds the file
read walk traces for a catch binding, since the
thrown value is the value the name holds there. A return followed
by a line terminator and then an expression is a
bare return, because the terminator ends the
expression the return word opens under the restricted
production, the same fact the slash judgement holds,
so the expression on the next line is no outcome of
the handler.
Both call pins read the module with
its comments stripped, and each judges its receiver
spelling as written, before any member spelling is
normalised, and refuses a computed or optional member
access on `$`, on `$.env` or `$.fs`, or on the method
itself, whether the access stands as a bracket member
in any key spelling, an optional chain step, or an
optional call step, because the host refuses that
access at load. Each pin reads an identifier escape
in a member name as the plain name it spells, so an
escaped noun or method stands judged as that member
and not outside the pins. A slash is judged by the
previous significant token, by the kind of the
bracket it stands inside, and by the wider facts the
grammar decides from beyond the previous token, in
every walk the gate
makes, so no walk in the gate reads a slash by a
character reading of its own. After an operand or a
postfix step a slash is division and the code behind
it stands judged in full. After a keyword that
expects an expression a slash opens a regex literal
and its contents stand quoted as text. A closing
parenthesis that ends a control head from if or
while or for or with or switch or catch leaves a
statement to start, so a slash after it opens a
regex literal. A closing brace that ends an object
literal is an operand, so a slash after it is
division, and a closing brace that ends a block
leaves a statement to start, so a slash after it
opens a regex literal. A colon is judged by the
construct it stands in, so a brace after a colon
heading a label, a case or a default block is a
block, while a brace after a value colon, inside an
object, a parenthesis, a bracket, an interpolation
or a conditional branch, is an object. A dot that
closes a number token is part of the number, so a
slash after a trailing dot number is division. A
function or class word is judged by the position it
stands in, so the brace closing a function or class
expression is an operand, while the brace closing a
declaration ends a block. A line terminator after
the return word or the yield word ends the expression
that word opens, so a brace after one is a block. A
line terminator after the throw word stands outside
that set, because the grammar makes the terminator an
error there rather than the end of an expression. The auxiliary walks read
a template as the charged walks do, with
interpolations as nested ranges and template text
inert, so a brace standing as template text moves no
range in any walk. The gate tests prove the
reading on a division chain after a postfix step,
behind a regex literal after a keyword, behind a
regex literal standing as the body of a control
head, and on division chains headed by object
literals standing after a return, inside call
arguments and arrays, behind a comma, as the value
of a member, and inside function, arrow and class
bodies, and on the colon, number dot, expression
standing, line terminator and nested template
positions this section names. Two limits stand
declared, a spelling that is not valid JavaScript
can pass the pins and load nowhere, and a dot spaced
or parenthesised receiver can fail the pins while
the host accepts it. An escape that spells a character which
cannot stand in an identifier where it stands is left
undecoded and judged as written, so the pins fabricate
no member chain from an invalid or punctuation valued
escape. The environment pin requires every
`$.env.get` and `$.env.set` call site to name its
variable with the exact literal
`RECOGNITIO_PACKET_DIR` standing alone, with whitespace
and comments allowed around the name and nothing joined
onto it, and it refuses an environment reference taken
without a call, a name that is not a string literal, an
interpolated template name, a second argument beside
the name at a `get` call, and an escaped spelling of
the name, which must stand spelled plainly, a stricter
spelling than the host decoded comparison. The file
read pin refuses an options object at every
`$.fs.read` call site, whether the object stands in
the call itself or in one of its branches, in
parentheses inside the call, behind a name the module
binds to an object literal in any binding spelling,
where a module top level binding counts wherever it
stands and a binding inside a function counts in its
written order, behind a member holding one, behind
the return value of a local helper, behind a member
of a call result, behind a getter, behind a value
bound by a catch clause where its try block throws an
object the walk traces, behind an object produced by
a rest destructuring of an object literal or of a
name bound to one, or behind a
parameter its own call sites feed an object, and it
refuses any argument count but one at the read, a
second argument or none. The gate also refuses a
module that binds `$` itself to another name, because
the host requires the `$.` spelling at every call
site and refuses the declaration and assignment
bindings at load, and it refuses a `$` called on its
own, in a plain call or an optional call spelling, a
`$` passed other than as a bare argument to a
parameter named `$`, a
`$` spread, returned, interpolated or read as a
value, a noun of `$` bound onward, and a mods API
call through any receiver other than `$`, because a
call behind any of those stands where no pin can
read it. A comment quoting either call shape is not
a call site and trips neither pin, and neither does a
call shape quoted inside a string, a template or a
regex literal, while a call inside a template
interpolation is a call site and trips the pins as
before. The file read pin
does not judge an options object the walk does not
trace, one produced by a branch, a call, a
constructor, a member walk, a container or an await
step, whether it stands at the call itself or
behind a bound name. Those shapes pass the pin
and deny a verified packet at runtime, so they fail
closed and stand outside the promise the pin makes.
A call production the walk does trace, a direct helper
call and an `Object.assign` production among them,
stands judged and refused, and a rest destructuring
and a catch clause binding the walk traces stand
judged the same. The catch clause tracing follows a
thrown object it can read, and a catch clause feed
produced by a call production stands among the feeds
that tracing does not follow, failing closed at
runtime where the read takes it.
What the pins cannot hold is the runtime half of
the contract, which stands on the live run and the
host side tests alone.

## The structural family the gate certifies

The repo gate certifies the shipped module and the
modules standing in its structural family, and it
refuses a module standing outside that family rather
than judge it. The family is the construct space the
shipped module and the variants this programme has
priced as legitimate exercise, and the census in the
gate reads it as a list of constructs a module in the
family never carries. A module carrying one is
refused with the family problem for its kind, whatever
the readings would have said of it, so the
certification this brief describes is a certification
of a family member and of nothing else.

A module in the family carries no labelled statement.
Its loop conditions read state the module holds,
standing as a name, a member or a call in the
condition, and never as a bare literal or an empty for
condition. Every function declaration in it stands
where a statement can stand, and never after a
statement the grammar ends by insertion for want of a
semicolon. The gating handler name and the catch
handler name stand declared under const or let only
at the top level of the module or of a function body,
and never inside a block, a class body or a static
block, and neither name stands alone inside brackets,
as the key of a computed member step or an element of
an array. A destructuring pattern
stands only as the first declarator of its
declaration. No member of an object is written in it,
by an assignment, by a step or by the delete
operator, under the dot spelling of the member or
the bracket spelling, and a member standing as the
target of a destructuring assignment or of a for
head is written the same way. No call writes into an
object, the calls being Object.assign,
Object.defineProperty, Object.defineProperties,
Object.setPrototypeOf, Reflect.set,
Reflect.defineProperty and Reflect.deleteProperty,
under the dot spelling of the call or the bracket
spelling of its receiver and its name. The module
names no Proxy constructor and no Function
constructor and carries no call to eval, and a
method or a field named delete, Proxy, eval or
Function is a member name, neither the operator nor
the constructor the spelling names. Inside the family the readings judge the
contract the deployment gate section states, the
registration, the two call pins and the deny
outcomes, and the variation they price is the
family's tolerated variation, delegation through bare
local calls, handlers standing in try and catch and
finally blocks, switch clauses and the conditional
and fallback outcome spellings among it.

The boundary stands where it does because of what the
repair programme proved against the wider claim. The
lane 8 consolidation unified the gate's readings and
passed the whole local gate, and its repair red team
then proved six fresh certification holes in shapes
outside the family as now drawn, a labelled break
leaving its loop read as a fall so a catch handler
returning nothing certified, a registration standing
after an endless loop certifying while nothing
registered, a rebind lost behind a declaration
standing after an unterminated statement, a handler
name declared inside a block judged as the binding at
a call outside it, a destructuring declarator hidden
behind a member named of or in, and a deny object
emptied through a member while the catch handler
returned it. Each one is a regression test now whose
required verdict is the family refusal. The broad
claim that the gate judges an arbitrary module is
dropped, and it stays dropped. Widening the family is
a deliberate act that names the construct in this
section and in the census in the same change, and a
shape nobody has named stands refused until someone
does.

Seven shapes stand as named residuals of this
contract.
The gate reads a loop condition's shape, not its
value, so a loop condition that is constant in fact
but not in spelling, standing as a name the module
bound to a literal, as a member of a literal, or
against a bound no spelling can reach, reads as
state under the census while the loop it heads never
ends. A bare local call that never returns, standing
before the registration, reads as the delegation the
family tolerates while the registration it precedes
never runs. A call that writes into an object,
reached through a receiver whose identity the census
does not judge, an alias holding the constructor or
the constructor reached through the global object,
reads as a call on a name the census leaves alone
while the write lands the same way. A write through
a member standing as one clause of a comma sequence
inside a returned value reads as the value it stands
in, since the write readings judge statements and a
sequence clause is a value position. A handler
standing under an export alias, or under a
differently cased export name beside the name the
registration binds, reads as the export it stands
under, since the readings judge the names the
module's own text binds. A call to eval reached
through a member chain reads as a call on the
receiver it stands behind. A regex literal spelled
inside a template literal's hole reads as the
template it stands in, since the slash judgement
stands over literal text and a hole is code. A
condition constant in fact but not in spelling, a
local call that never returns, a write call through
a receiver whose identity the census does not judge,
a write standing as a sequence clause in a returned
value, a handler standing under an export alias, a
call reached through a member chain, and a regex
spelled inside a template hole are outside what a
structural gate can judge, because judging them is
judging what a value holds, what a call does, what
a name stands for, and where a value's clauses run.
The certified population is this
project's own shipped module in this project's own
repo, and the gate's job is catching accidental
breakage of that module's contract and keeping the
claims in this brief honest. A determined author
spelling past a syntactic line inside their own repo
is not a threat this gate can price. The gate judges
structure, not intent.

## What the brief strikes

The `onFailure` language is struck from this brief as a
category error. That setting belongs to command and HTTP
settings hooks, not to mods. The `--mod` flag is struck.
The one session flags are `--plugin-dir` and
`--plugin-url`. The `agent.spawn` claim narrows to model
choice and deny, which is what the primary Mods
reference documents. Prompt rewriting by the hook is now
primary documented. The v2.1.300 release notes and the
October 14 2026 docs changelog both document the
prompt.change mod hook. The mods reference return table
lags behind, showing model choice and deny only, stamped
as of v2.1.290.

## The scheduled execution reconciliation

The mod leaves `disable-model-invocation` at its default
false and withholds the skill through no deny rule, so
scheduled runs through `/loop` keep working. Setting the
flag true would turn scheduled fires into plain text
sends, which is the failure mode the primary scheduled
tasks page warns about.

## The live run correction

The module as first shipped never ran. Its environment
read passed a variable where the host requires a string
literal at the call site, so validation failed on the
module and the host refused to load it in a session,
and a spawn over an unverified packet proceeded with
no gate at all. Its file read passed an options object
where the host takes the path alone, and no repo gate
could see either defect, because the host side tests
stubbed the calls in the same shapes the code assumed.
A live run on Claude Code 2.1.314 in an OpenRouter
backed session caught both. This pass corrects the two
call sites, rebuilds the host
side tests on the test kit engine with stubs in the
documented shapes, pins both call shapes in the repo
gate, and gives the mod entry the brand icon its
manifest lacked.

## Skill tightness

The mod, its tests, and this brief live outside the
canonical skill text under `hooks/` and `docs/`. The
skill description is untouched, so the description
protocol does not fire. The deliverable remains the
skill.

## Navigation

- [Documentation index](README.md)
- [Decisions](decisions.md)
- [Principles](principles.md)
