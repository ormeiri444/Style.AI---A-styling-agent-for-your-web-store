The person in the first image is currently wearing: {worn_items_str}.

Task: Add the CLOTHING ITEM from IMAGE 2 to complete their outfit.

CRITICAL INSTRUCTIONS:
- IMAGE 1 contains the TARGET PERSON with their current outfit - preserve their exact face, body, and pose
- IMAGE 2 contains the NEW CLOTHING ITEM to add - this may show a model wearing the clothes
- If IMAGE 2 shows a model wearing the clothing, COMPLETELY IGNORE that model's face and body
- Extract ONLY the clothing item from IMAGE 2 and add it to the person from IMAGE 1
- The output should show ONLY the person from IMAGE 1, never blend or morph faces/bodies

New item description: {item_description}

Requirements:
- Keep the person's face IDENTICAL to IMAGE 1 - no changes whatsoever
- Keep everything about the current outfit exactly the same
- Add ONLY the new clothing item to the appropriate body part
- Maintain the person's body shape and proportions from IMAGE 1
- Preserve the person's pose from IMAGE 1
- Ensure the new item coordinates well with existing clothing
- Do NOT use any facial features, body shape, or pose from IMAGE 2
