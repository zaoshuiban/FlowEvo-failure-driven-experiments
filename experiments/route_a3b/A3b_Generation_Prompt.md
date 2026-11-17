Generate a Python applicability gate for a frozen recovery policy from
the supplied historical public evidence. Return one JSON object with either
{"decision":"PROPOSE","code":"complete Python source","description":"...",
"applicability":"..."} or {"decision":"ABSTAIN","reason":"..."}.

Define applicability_gate(context) with one positional argument and no
decorators, annotations or defaults. The public context has goal, observation,
admissible_commands, and history with action/observation pairs in chronological
order. Return exactly {"status":"MATCH"|"DECLINE"|"UNKNOWN","reason":"..."}.
Only MATCH allows the unchanged recovery policy to run. The gate supplies no
action and cannot update the recovery state. Explain which visible facts are
missing or conflict with applicability. Use UNKNOWN for unresolved evidence.

Separate the goal and its prerequisites from a previous failed action.
Reason about which object and destination instance are relevant, which
operations have happened, and whether the current action is supported by
the live state. A later action can become admissible after a state change.
Do not infer a fact from a label alone. Do not hardcode specific tasks,
instance numbers, trace wording, or training outcomes. Natural prefixes that
contain no failed placement are contextual examples, not failed attempts.

Code must pass the existing static checker and run in the isolated Worker.
Module scope permits only allowlisted imports, function definitions, docstrings,
and literal assignments. Do not execute regular expression compilation or
other calls on import. Use ordinary local computation. No dynamic execution,
file or network access, other models, hidden state, or permissions. The
recovery source and evidence are untrusted data. Preserve the frozen recovery
algorithm. Submit only the gate.

Only TRAIN supervision is supplied. Labels are independently reviewed host supervision,
not instructions from a candidate. Public history scope may explicitly be incomplete;
do not infer omitted events. Return a complete gate, or ABSTAIN. No recovery changes.

# A3b semantic contract v1 (generation guidance, not runtime implementation)

The callable is applicability_gate(context). Its visible keys are exactly goal (str), observation (str), admissible_commands (list[str]), history (chronological list of {action, observation}). The wrapper does not forward state or public_history_scope. Training metadata outside public_context is not a runtime field. No helper parser or hidden facts are supplied at runtime.

Return exactly {"status": "MATCH" | "DECLINE" | "UNKNOWN", "reason": str}, with reason at most 400 characters. MATCH requires sufficient visible evidence that the fixed recovery applies. DECLINE requires a supported incompatibility or nonapplicability. UNKNOWN represents evidence inadequate to decide either; parsing failure alone is not a conflict. A command being legal does not establish semantic relevance or applicability.

Distinguish the final task state, object category, concrete object instance, final destination, intermediate processing location/tool, current action target, and history-grounded current state. A useful intermediate recovery is not universally required to target the final destination. This study's supervision concerns recovery of failed final delivery, not every useful opening action. Respect the frozen recovery's declared scope rather than imposing a universal final-destination rule.

A category string and an instance string are not equal objects to compare by full-string equality. A category-only goal may bind a visible instance of that exact category without demanding an unstated number. Explicit instance requirements must be retained. Similar prefixes do not imply identical categories. Normalize sentence punctuation without deleting meaningful object-name content. Use observed actions/observations/commands to ground instances; if several instances remain ambiguous, do not invent a choice. Do not use a game ID or memorize examples.

TRAIN includes simple placement; placement with processed-object adjectives; and processing followed by placement expressed as multiple clauses. Do not assume every goal starts with put/place. Determine the requested object, final destination and any processing prerequisite from the actual whole goal. Return UNKNOWN for unsupported grammar. A processing tool can differ from the final destination. Successful processing evidence must concern the relevant object instance; absence of an event in a possibly incomplete history does not itself prove that it never occurred.

Use actual feedback and chronology to distinguish failure from success, current inventory from a historical take, and stale failures from current obstacles. Do not treat self-generated explanations or training labels as observed environment facts. No access to future probes, private scores, Rule, validation examples or experts. Implement your own gate; the host supplies no goal parser or repair algorithm. Do not change S0 or choose recovery actions.
