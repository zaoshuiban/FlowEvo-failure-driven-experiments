import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Explicitly reviewed against frozen task statements, not inferred from outputs.
FLOATS = {
    "lcb_atcoder_abc314_e": (5, "relative_or_absolute"),
    "lcb_atcoder_abc385_f": (9, "relative_or_absolute"),
    "lcb_atcoder_abc392_d": (8, "relative_or_absolute"),
    "taco_0191": (7, "absolute"), "taco_0967": (6, "absolute"),
    "taco_0334": (6, "absolute"), "taco_0526": (9, "absolute"),
    "taco_0330": (8, "absolute"), "taco_0134": (6, "absolute"),
    "taco_0504": (3, "absolute"), "taco_0587": (6, "absolute"),
    "taco_0348": (6, "relative_or_absolute"), "taco_0808": (6, "relative_or_absolute"),
    "taco_0743": (6, "relative_or_absolute"), "taco_0243": (9, "relative_or_absolute"),
    "taco_0675": (6, "relative_or_absolute"), "taco_0018": (6, "relative_or_absolute"),
    "taco_0953": (6, "relative_or_absolute"), "taco_0916": (6, "relative_or_absolute"),
    "taco_0198": (6, "relative_or_absolute"), "taco_0554": (6, "relative_or_absolute"),
    "taco_0868": (6, "relative_or_absolute"), "taco_0543": (6, "relative_or_absolute"),
    "taco_0815": (6, "relative_or_absolute"), "taco_0659": (6, "relative_or_absolute"),
}

MULTI = set('''lcb_atcoder_abc350_c lcb_atcoder_abc311_c lcb_atcoder_abc315_e
lcb_atcoder_arc181_c lcb_atcoder_abc366_g lcb_atcoder_arc185_c
taco_0552 taco_0137 taco_0510 taco_0831 taco_0946 taco_0720 taco_0054 taco_0594
taco_0444 taco_0519 taco_0639 taco_0173 taco_0638 taco_0295 taco_0221 taco_0790
taco_0726 taco_0485 taco_0742 taco_0094 taco_0649 taco_0238 taco_0010 taco_0042
taco_0968 taco_0056 taco_0574 taco_0077 taco_0298 taco_0394 taco_0942 taco_0615
taco_0381 taco_0477 taco_0343 taco_0047 taco_0347 taco_0718 taco_0621 taco_0825
taco_0260 taco_0083 taco_0565 taco_0582 taco_0220 taco_0081 taco_0771 taco_0119
taco_0984 taco_0422 taco_0308 taco_0577 taco_0945 taco_0408 taco_0205 taco_0617
'''.split())


def main():
    catalog = json.loads((ROOT / "catalog.json").read_text())
    rows = {}
    for task in catalog:
        tid = task["task_id"]; text = task["prompt"]
        p = {"task_id": tid, "dataset": task["dataset"], "function": task["fn_name"],
             "comparison": "semantic" if tid in MULTI else "structured" if task["fn_name"] else "tokens",
             "case_insensitive": bool(re.search(r"case[- ]insensitive|case of (?:the )?(?:letters|characters).*does not matter", text, re.I)),
             "input_contract": "structural_only", "reference_status": "provided_not_independently_proven",
             "task_sha256": task["task_sha256"], "policy_source": "frozen statement; explicit reviewed registry"}
        if tid in FLOATS:
            exponent, mode = FLOATS[tid]
            p.update(epsilon="1e-" + str(exponent), error_mode=mode, strict=tid in {"taco_0330", "taco_0334"})
            p["negative_one_sentinel"] = bool(re.search(r"(?:no such|no solution|impossible).*?-\s*1", text, re.I | re.S))
        if re.search(r"\binteractive (?:problem|task)\b", text, re.I):
            p["protocol"] = "interactive_unsupported"
        else:
            p["protocol"] = "function" if task["fn_name"] else "stdio"
        if tid == "taco_0808":
            p["policy_note"] = "Statement mentions both 1e-6 and a looser subtask tolerance; use stricter global 1e-6."
        rows[tid] = p
    (ROOT / "policies.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    print("Frozen task policies", len(rows), "float", len(FLOATS), "multi", len(MULTI))


if __name__ == "__main__":
    main()
