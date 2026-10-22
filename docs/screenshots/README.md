# Dashboard screenshots

These PNGs are genuine browser captures, not generated mockups. Captures are taken at a 1280 × 720 browser viewport during the 23 October 2026 audit. The local audit build includes the refreshed 268-test evidence; the deployed version will reflect it after the owner pushes the changes.

| Capture | Shows |
|---|---|
| [Overview](overview.png) | Project purpose, supported constructs and saved test evidence |
| [Compiler Playground](playground.png) | Successful compilation and real compiler output |
| [Optimization](optimization.png) | IR reduction summary and instruction-change labels |

## Refreshing captures

Run `python -m streamlit run dashboard/app.py`, then capture the actual page after the requested compilation finishes. Use the same filenames to update the README preview. Do not edit results or substitute fabricated output. Sources should contain only public example programs.

The [CLI captures](../demo_outputs/) provide readable text evidence, including diagnostics and exit codes. The current [test log](../test_results.txt) identifies its verification date and command. The final academic report is a separate preserved snapshot and is not rebuilt when these portfolio screenshots change.
