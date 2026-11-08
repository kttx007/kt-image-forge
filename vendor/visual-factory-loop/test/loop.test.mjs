import test from "node:test";
import assert from "node:assert/strict";
import { createRun, recordAudit, lockSlot } from "../src/engine.mjs";
import { chooseRenderMode } from "../src/planner.mjs";

const job={job_id:"t",slots:[{id:"M01",kind:"main_image"}]};

test("whole image is default for commerce",()=>{
  assert.equal(chooseRenderMode(job.slots[0]),"whole_image_generation");
});

test("dense structured information routes hybrid",()=>{
  assert.equal(chooseRenderMode({kind:"pin_map"}),"hybrid_generation");
});

test("hard failure requests local repair first, branch second",()=>{
  const run=createRun(job);
  let r=recordAudit(run,"M01",{checks:{fact_truth:true,product_identity:false,physical_truth:true}});
  assert.equal(r.action,"local_repair");
  r=recordAudit(run,"M01",{checks:{fact_truth:true,product_identity:false,physical_truth:true}});
  assert.equal(r.action,"new_branch");
});

test("passed slot can lock",()=>{
  const run=createRun(job);
  recordAudit(run,"M01",{checks:{fact_truth:true,product_identity:true,physical_truth:true},soft_score:75});
  lockSlot(run,"M01",{sha256:"abc"});
  assert.equal(run.slots.M01.status,"locked");
});
