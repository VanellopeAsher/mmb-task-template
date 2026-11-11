# Agent environment

`Dockerfile` defines the per-task software stack. `data/` holds original inputs and metadata; `tools/` holds usable scientific programs or interfaces; `skills/` holds existing Agent Skill packages. Pin software and skill versions, document licenses and checksums, and expose only materials intended for the agent. Do not place reference answers or hidden verifier data here.

For a full task, provide a broad but relevant research environment. Include enough data and complementary tools for different plausible approaches, with configurable parameters, inspectable intermediate outputs, and ways to cross-check results. Give the agent room to design experiments and make choices within the stated resource budget. Document each tool's capabilities and limits; do not encode the Oracle's sequence of steps as the only usable workflow. Avoid adding unrelated software solely to increase the tool count.
