FlowEvo / DeepSeek benchmark
============================
Directory: /opt/flowevo-benchmark-20261019
Service: flowevo-benchmark-20261019.service

Progress:
  systemctl status flowevo-benchmark-20261019.service
  tail -f /opt/flowevo-benchmark-20261019/benchmark.log
  cat /opt/flowevo-benchmark-20261019/reports/summary.json

Results (updated after each completed problem):
  reports/report.html           human-readable table
  reports/summary.json          overall and per-difficulty success rates
  reports/experiment_config.json
  data/taco_manifest.json       selected task IDs, order, counts, hashes
  data/lcb_manifest.json        selected task IDs, order, counts, hashes
  data/download_manifest.json   dataset download hashes
  data/expected_sha256.json     official Hugging Face LFS hashes
  runs/<dataset>_<difficulty>/<task_id>/result.json
  runs/<dataset>_<difficulty>/<task_id>/<stage>.py
  runs/<dataset>_<difficulty>/<task_id>/<stage>.response.json
  runs/<dataset>_<difficulty>/<task_id>/<stage>.verdict.json

Protocol:
  TACO official test split; sample 100 of 200 at each of 5 difficulties.
  LiveCodeBench code_generation_lite release_v6 (test.jsonl through test6.jsonl).
  Select min(100, group size) using SHA256(seed|dataset|difficulty|source_id),
  seed 20261019. Episode order is the same hash order.
  Each of the 8 difficulty groups starts with an independent empty skill library.
  Use the official FlowEvo code_math CodeSkillLibrary and ours pipeline:
  initial candidate, up to two independent alternatives, then up to two
  feedback/skill-conditioned repairs. Stop after the first all-tests-pass result.
  Maximum 5 attempts. Only pass/fail or error category is returned to the LLM.
  Reference solutions and private inputs/outputs are never sent to the LLM.
  Final success rate uses test feedback and is NOT hidden-test-blind pass@1.
  The first-candidate rate is separately recorded.
  All official TACO cases and LCB public+private cases are used for verification.
  TACO timeout: 4 seconds/case. LCB: 6 seconds/case. Python 3.10.12.
  First-failure short circuit preserves the all-tests-pass predicate.

Model:
  Requested: deepseek-reasoner, thinking enabled, effort high, max_tokens 32768.
  Actual API returned model is recorded for every call (currently deepseek-flash).
  DeepSeek thinking mode ignores temperature; original stage temperature values
  are retained in request logs but do not control sampling in this mode.
  All API usage is logged. Infrastructure/API failures stop rather than count
  as model solving failures. Partial-run final rates remain null.

Source revisions:
  FlowEvo https://github.com/DEFENSE-SEU/FlowEvo
    36e81efd4d1fdbabca7366200b15808ebef157fa
  TACO dataset d593ed0a2becbbc952230bb89be09189bf1056dc
  TACO evaluator 245eba3beb2d23a07082307de303de2589e4321a
  LCB dataset 0fe84c3912ea0c4d4a78037083943e8f0c4dd505
  LCB evaluator 28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24

Scope and limitations:
  This uses FlowEvo's released code/math benchmark implementation, whose skill
  library stores and retrieves previous successful solutions. The full workflow
  governance implementation for other environments is not substituted here.
  Adapter changes: new prompts/evaluators, full repair context rather than the
  original prompt/code truncation, larger reasoning token limit, independent
  difficulty streams, and durable per-attempt logs.
  Some TACO reference solutions fail its own official output checker, including
  non-unique-output problems. No sampled task is removed or manually re-scored.
  Reported scores mean official test-suite acceptance, not human semantic review.

Isolation:
  Evaluation runs in bubblewrap namespaces as uid 65534, without networking or
  credentials, with read-only mounts and a private temporary directory.
  Only API calls run in the credential-holding parent process.

Resume after a stop:
  cd /opt/flowevo-benchmark-20261019
  systemctl reset-failed flowevo-benchmark-20261019.service
  systemd-run --unit=flowevo-benchmark-20261019 \
    --property=WorkingDirectory=/opt/flowevo-benchmark-20261019 \
    --property=StandardOutput=append:/opt/flowevo-benchmark-20261019/benchmark.log \
    --property=StandardError=append:/opt/flowevo-benchmark-20261019/benchmark.log \
    /opt/flowevo-benchmark-20261019/venv/bin/python -u \
    /opt/flowevo-benchmark-20261019/benchmark.py
  Completed candidate responses and verdicts are reused. Completed task solutions
  reconstruct the skill library in the same deterministic episode order.

Local cleanup:
  Previously downloaded local datasets, FlowEvo, evaluation sources, and temporary
  virtual environment were moved to the Windows Recycle Bin at the user's request.
  The original desktop API key file was retained.
