export const HARD_GATES = Object.freeze([
  "fact_truth",
  "product_identity",
  "physical_truth",
  "locked_slot_immutability"
]);

export function chooseRenderMode(slot) {
  const kind = slot.kind || "normal_detail";
  if (["spec_table","legal","qr","exact_identifier"].includes(kind)) return "deterministic_overlay";
  if (["dense_fact_detail","pin_map","dimension_diagram"].includes(kind)) return "hybrid_generation";
  return "whole_image_generation";
}

export function compileSlotBrief(job, slotId) {
  const slot = job.slots.find(s => s.id === slotId);
  if (!slot) throw new Error("unknown_slot");
  const claims = (slot.claim_ids || [])
    .map(id => job.claims.find(c => c.id === id))
    .filter(Boolean);

  const hardFacts = claims.flatMap(c => c.evidence || []);
  const relevantIdentity = (job.product_identity || []).filter(r =>
    !r.scopes || r.scopes.includes(slotId) || r.scopes.includes("*")
  );
  const relevantPhysics = (job.physical_rules || []).filter(r =>
    !r.scopes || r.scopes.includes(slotId) || r.scopes.includes("*")
  );

  return {
    job_id: job.job_id,
    slot_id: slot.id,
    role: slot.role,
    buyer_question: slot.buyer_question,
    dominant_message: slot.dominant_message,
    exact_copy: slot.exact_copy || [],
    claims,
    render_mode: chooseRenderMode(slot),
    style: job.style,
    hard_constraints: {
      facts: hardFacts,
      identity: relevantIdentity,
      physics: relevantPhysics
    },
    creative_freedom: {
      composition: "open",
      lighting: "open",
      scenario: "open_if_fact_compatible",
      typography: "open",
      camera_language: "open"
    }
  };
}

export function planJob(job) {
  return {
    job_id: job.job_id,
    hard_gates: HARD_GATES,
    slots: job.slots.map(s => ({
      id: s.id,
      role: s.role,
      render_mode: chooseRenderMode(s),
      status: s.status || "planned"
    }))
  };
}
