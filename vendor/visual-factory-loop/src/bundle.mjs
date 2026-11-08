import { compileSlotBrief } from "./planner.mjs";

export function buildManualWebBundle(job, slotId) {
  const brief = compileSlotBrief(job, slotId);
  const prompt = [
    "# TASK",
    brief.dominant_message,
    "",
    "# BUYER QUESTION",
    brief.buyer_question || "",
    "",
    "# RENDER MODE",
    brief.render_mode,
    "",
    "# STYLE DNA",
    JSON.stringify(brief.style, null, 2),
    "",
    "# VERIFIED CLAIMS",
    JSON.stringify(brief.claims, null, 2),
    "",
    "# HARD CONSTRAINTS — only these are mandatory",
    JSON.stringify(brief.hard_constraints, null, 2),
    "",
    "# CREATIVE FREEDOM",
    "You are free to choose composition, lighting, camera language, typography and scene details when they do not conflict with verified facts, product identity or physical truth.",
    "",
    "# OUTPUT",
    "Generate one complete commercial image. Do not generate an empty background for later assembly unless the render mode explicitly requests deterministic/hybrid output."
  ].join("\n");

  return {
    prompt,
    facts: brief.hard_constraints.facts,
    references: {
      product_assets: job.product_assets || [],
      style_references: job.style_references || []
    },
    return_instructions:
      "Save the generated image as candidate.png in this slot bundle. Do not overwrite locked masters. Then return to the Loop and run audit."
  };
}
