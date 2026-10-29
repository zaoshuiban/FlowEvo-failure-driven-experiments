# V3纠错式生成：真实模型与工程边界

真实完成6次机制归纳：F三个来源组均PROPOSE_CORRECTION；T第一组HYPOTHESIS_ONLY，其余两组PROPOSE_CORRECTION。Task-Only收到相同来源题面，没有错误解答、correct=false、F机制或旧源码。它仍使用共同纠错字段，因此可能更保守；不能用提出纠错的数量证明F优越。

生成器的算法规格由proposed_corrective_operation、correctness_argument、required_assumptions等字段构成，而非直接传入failure_diagnosis作为算法指令。完整原失败仍作为证据存在，模型必须区分诊断与替代，不宣称仅凭结构就保证正确。

四次已返回的源码请求均finish_reason=length，输出12288 Token全部为reasoning Token，content为空；第五次源码请求返回HTTP402并保留UNKNOWN。没有完整算法或语义源码，因此本轮没有实际验证算子2是否已避免提前化简。

以下全文来自真实GPT机制响应（不包含标准答案）。它们是未验证假设，不是宿主写好的算法，也不是计算正确性证明。

## F1：PROPOSE_CORRECTION

**原操作诊断（GPT原文）**

Using partial admissibility filters, memory, symmetry, or informal spot-checking to assign whole subtotal counts for longer numbers ('3-digit total', '4-digit total') without exhaustive generation and exact primality verification of every candidate.

**替代操作（GPT原文）**

Replace heuristic/manual subtotaling with exact exhaustive computation: (1) For each length L=1,2,3,4, generate all permutations of length L from the given digit set. (2) Discard those with leading 0 when the problem forbids it. (3) Optionally prune only by sound necessary rules: for L>1 keep only numbers whose last digit is in {1,3,7,9} intersected with the set, exclude numbers with digit sum divisible by 3, and keep 2 or 5 only in the 1-digit case. (4) For every remaining candidate, run an exact primality test up to sqrt(n). (5) Count the primes found. This is the reusable mechanism for all supplied tasks.

**不确定性（GPT原文）**

No gold answers are supplied, so I cannot certify the true count for each episode or identify the exact first misclassified candidate in every final response. Some individual listed primality judgments may be correct; the reliably observed defect is the unsupported aggregation/guessing process, not necessarily the same local arithmetic error in every case.

状态：CORRECTION_UNVERIFIED。没有对应的完整新源码，不能据文字判定算法已纠正。

## F2：PROPOSE_CORRECTION

**原操作诊断（GPT原文）**

Replacing a leading block by a single constant on the claim that its local value is unaffected by later parenthesization, e.g. '7-7 -> 0' or '6·7·7 -> 294', before exploring all legal full parenthesizations of the whole expression.

**替代操作（GPT原文）**

Do not pre-collapse a prefix or any other subexpression unless it is proved to be closed under every allowed parenthesization boundary. Instead, compute value sets for every contiguous interval using the interval-DP recurrence S[i,j] = union over k of {x op_k y : x in S[i,k], y in S[k+1,j]}. Deduplicate values at each interval. For these two episodes, this mechanism strongly suggests the recorded answers are undercounts; an independent interval-DP reconstruction gives likely totals 33 for the first problem and 50 for the second, though no external gold is provided here.

**不确定性（GPT原文）**

No gold answers are supplied, so the corrected counts are independent reconstructions rather than externally verified truths. Also, the exact intended treatment of any nonstandard operator conventions is assumed standard here; if the source problem used unusual parsing or excluded some full binary parenthesizations, the counts could differ.

状态：CORRECTION_UNVERIFIED。没有对应的完整新源码，不能据文字判定算法已纠正。

## F3：PROPOSE_CORRECTION

**原操作诊断（GPT原文）**

Suspected invalid operation: concluding the final number of distinct results from incomplete manual enumeration, conceptual-only DP, memory/guessing, or error-prone hand union of value sets. A more specific suspected suberror is collapsing 'number of parenthesizations considered' into 'number of distinct values' without a verified exhaustive deduplication pass.

**替代操作（GPT原文）**

Replace informal sampling/guessing or hand-managed partial lists with exact interval dynamic programming over contiguous subexpressions: 1) parse the expression as operands a_1,...,a_n and operators op_1,...,op_{n-1}; 2) initialize DP[i,i] = {a_i}; 3) for increasing interval lengths L = 2..n, compute DP[i,j] as the union over splits k of {x op_k y : x in DP[i,k], y in DP[k+1,j]}; 4) use set union at every stage to deduplicate equal numerical results; 5) return |DP[1,n]|. For reliability, each operator application should use exact arithmetic and each interval should be computed exhaustively, not heuristically.

**不确定性（GPT原文）**

The full hidden computations are not available, so the exact point of failure in each attempt cannot be proven from the visible excerpts alone. For the first and third tasks, the partial text suggests substantial manual enumeration, but we cannot determine which specific interval value(s) were omitted or miscomputed. No verified gold answers are provided here, so the correction is methodological rather than a confirmed replacement numeral for any individual instance.

状态：CORRECTION_UNVERIFIED。没有对应的完整新源码，不能据文字判定算法已纠正。

## T1：HYPOTHESIS_ONLY

**原操作诊断（GPT原文）**

Hypothetical invalid operation: count all admissible permutations satisfying only superficial prime-like properties (odd last digit, not ending in 5, digit sum not divisible by 3), or use combinations instead of permutations, or allow leading-zero representations when 0 is present.

**替代操作（GPT原文）**

Replace any shortcut counting rule with: (1) for each source digit set, iterate k=1..4; (2) generate all ordered k-tuples of distinct digits from the set; (3) discard tuples beginning with 0; (4) optionally discard tuples whose last digit forces compositeness for k>1, and discard digit-sum multiples of 3 except the number 3; (5) apply an exact primality test to each remaining integer; (6) count the integers that are prime. For these small instances, trial division up to floor(sqrt(n)) is sufficient and easy to verify.

**不确定性（GPT原文）**

Because no worked solution attempt is supplied, it is uncertain which, if any, invalid operation was actually used. The proposed mechanism is exact, but numerical totals for each source are not derived here.

状态：CORRECTION_UNVERIFIED。没有对应的完整新源码，不能据文字判定算法已纠正。

## T2：PROPOSE_CORRECTION

**原操作诊断（GPT原文）**

Suspected invalid operation: fixing standard precedence first (especially multiplying before considering all parenthesizations), enumerating only left-associated/right-associated forms, or counting Catalan many parenthesizations rather than the set of distinct evaluated results.

**替代操作（GPT原文）**

Replace any precedence-based or partial-enumeration approach with interval dynamic programming over value sets: compute all attainable values for every contiguous subexpression, then combine subinterval sets at every possible final split. Deduplicate values at each interval. For the supplied evidence, this yields 33 distinct values for source 9ecc45210889a8a0ba4746faa19efe13a3656174d440659b0bbde1e7a6ac21bd and 34 distinct values for source 6de589c079a10b732bacc69730fc21cad36c82feb6a59a2353ab9072e68f1b8e.

**不确定性（GPT原文）**

There is no actual attempted solution to audit, so the true source of any error is unknown. If a source intended a nonstandard convention for any symbol, the above model would need adjustment, though nothing in the evidence suggests that.

状态：CORRECTION_UNVERIFIED。没有对应的完整新源码，不能据文字判定算法已纠正。

## T3：PROPOSE_CORRECTION

**原操作诊断（GPT原文）**

Hypothesized invalid operation: collapsing the expression according to ordinary operator precedence/left associativity, or counting syntactic parenthesizations without deduplicating equal outcomes, instead of enumerating attainable values for each contiguous subexpression.

**替代操作（GPT原文）**

Replace any precedence-only or raw-count approach with interval dynamic programming over sets of attainable values: parse operands/operators; initialize S[i,i] with each operand; for increasing interval lengths, combine every split k and collect all x op_k y from left/right sets; deduplicate by storing results in sets; return the size of the final set. This reusable computation solves all three tasks uniformly.

**不确定性（GPT原文）**

Because no attempt was supplied, it is uncertain which incorrect mechanism, if any, was actually used. There is also a convention choice: some authors say 'insert parentheses' while intending all full parenthesizations preserving order; the proposed DP assumes that standard interpretation.

状态：CORRECTION_UNVERIFIED。没有对应的完整新源码，不能据文字判定算法已纠正。
