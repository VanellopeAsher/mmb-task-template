# Shortcut audit

The attached revised proposal used exact equality against a reference plan and fixed mechanism predictions. Its Hamming-distance check therefore remained constant for every answer that passed equality. In a direct audit, changing two measurement `purpose` fields to say that their results would be ignored still received full reward. We retained the source corrections but replaced that scoring rule.

The repository's existing checklist verifier also lacks outcome-based ground truth. It must be replaced only after a matched intervention/outcome panel and independently supported mechanism label are obtained. A proposed matrix-rank scorer was tested locally but discarded because mathematical identifiability under assumed signatures cannot prove that a plan actually eliminates the wrong mechanisms in the observed system. See `outcome_based_verification.md`.
