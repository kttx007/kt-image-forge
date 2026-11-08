import { compileSlotBrief, planJob } from "./planner.mjs";
import { auditCandidate, nextAfterFailure } from "./audit.mjs";

export function createRun(job) {
  return {
    schema_version: "0.1",
    job_id: job.job_id,
    created_at: new Date().toISOString(),
    plan: planJob(job),
    slots: Object.fromEntries(job.slots.map(s => [s.id, {
      status: "planned",
      attempts: 0,
      failures: [],
      locked: false
    }]))
  };
}

export function prepareSlot(job, run, slotId) {
  const state = run.slots[slotId];
  if (!state) throw new Error("unknown_slot");
  if (state.locked) throw new Error("locked_slot_immutable");
  state.status = "bundled";
  return compileSlotBrief(job, slotId);
}

export function recordAudit(run, slotId, auditInput) {
  const state = run.slots[slotId];
  if (!state) throw new Error("unknown_slot");
  const result = auditCandidate(auditInput);
  state.attempts += 1;

  if (result.decision === "pass") {
    state.status = "passed";
    return result;
  }

  const failure = result.failed_hard_gates[0] || "soft";
  const action = nextAfterFailure(state.failures, failure);
  state.failures.push(failure);
  state.status = action === "new_branch" ? "branch_required" : "repair_requested";
  return {...result, action};
}

export function lockSlot(run, slotId, artifact = {}) {
  const state = run.slots[slotId];
  if (!state || state.status !== "passed") throw new Error("slot_not_passed");
  state.locked = true;
  state.status = "locked";
  state.artifact = artifact;
  return state;
}

export function runStatus(run) {
  const values = Object.values(run.slots);
  return {
    total: values.length,
    locked: values.filter(x => x.locked).length,
    blocked: values.filter(x => x.status === "branch_required").length,
    pending: values.filter(x => !x.locked).length
  };
}
