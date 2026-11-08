# GUANGYAN Complete Generated-Master Production Loop

> Source: Drive `GENERATED_MASTER_PRODUCTION_LOOP.md` (2026-11-01). Authoritative end-to-end SOP for commerce visuals.

## 1. Core Rule

For ecommerce main images, detail modules, posters, and short-copy marketing visuals, the strongest generation path creates the **complete designed image**: scene, product presentation, lighting, typography, copy hierarchy, color, and composition.

The complete generated image is the final candidate. If it passes product, fact, text, physics, and thumbnail review, lock and deliver it unchanged.

## 2. Reference Roles

- `identity_reference` — product structure
- `angle_physics_reference` — orientation / measuring axis / laser behavior (not automatically a deliverable)
- `style_reference` — typography / color / lighting / composition only
- `edit_target` — the one image that may be locally changed
- `generated_master` — complete candidate ready for audit

## 3. Production Loop

**A Research** → buyer task, one dominant claim per slot  
**B Lock product & facts** → hashes, invariants, physics, pending_confirmation  
**C Compile brief** → result type, subject/action, physical detail, reference roles, exact copy, edit boundary, output settings  
**D Generate complete master** → one call per slot/branch; whole-image by default  
**E Audit** → full size + ~300px (identity / physics / facts / readability)  
**F Decide once, act locally** → pass lock / product-only / text-only / physics-only / new branch; stop after 2 failed local repairs  
**G Freeze** → byte-for-byte lock + SHA-256; never overwrite  
**H Assemble set** → Set Lineage Gate before packaging

## 4. Hard Prohibitions

- Do not rebuild successful masters as HTML/CSS/slide layouts
- Do not deliver a blank angle reference when the slot needs a marketing image
- Do not overwrite locked masters
- Do not reuse rejected experiments as product references
- Contact sheets are supplementary, not delivery substitutes

## 5. Dense Specification Exception

Dense tables / QR / legal may use hybrid or deterministic repair of the factual region only after the visual direction passes.

## 6. Local Repair Priority (2026-11-01)

Prefer deterministic masked edits (Pillow/OpenCV) for local defects. Full-image generation is for new masters or demonstrated whole-composition need, not the default repair method.

Full original also lives on Drive; this repo keeps the executable contract in `forge/loop/` and this summary for agents without Drive.
