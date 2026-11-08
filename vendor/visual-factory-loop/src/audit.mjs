const HARD = ["fact_truth","product_identity","physical_truth"];

export function auditCandidate({checks = {}, soft_score = 0} = {}) {
  const failedHard = HARD.filter(k => checks[k] === false);
  if (failedHard.length) {
    return {
      decision: "reject",
      failed_hard_gates: failedHard,
      repair_scope: inferRepairScope(failedHard)
    };
  }
  return {
    decision: "pass",
    failed_hard_gates: [],
    soft_score,
    note: soft_score < 60 ? "pass_with_style_review" : "pass"
  };
}

export function inferRepairScope(failures) {
  if (failures.includes("fact_truth")) return "information_region";
  if (failures.includes("product_identity")) return "product_region";
  if (failures.includes("physical_truth")) return "physical_relation_region";
  return "current_slot";
}

export function nextAfterFailure(previousFailures = [], currentFailure) {
  const same = previousFailures.filter(x => x === currentFailure).length;
  return same >= 1 ? "new_branch" : "local_repair";
}
