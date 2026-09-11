## {{project}} — repository facts

Rendered from `.agent-harness/facts.toml`; change that file and re-run `project-init`. Authority stays in the global working contract.

- Tests: `{{test_command}}`
- Lint: `{{lint_command}}`
- Fastest refuting check: {{shortest_loop}}
- Truth sources, in precedence order:
{{truth_sources}}
- Traps:
{{traps}}
- Review lenses:
{{review_lenses}}
