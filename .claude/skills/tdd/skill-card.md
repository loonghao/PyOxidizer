## Description: <br>
Guides coding agents through test-driven development for coding and bug fixing, including Red-Green-Refactor, test execution, and test design strategies. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[drumrobot](https://clawhub.ai/user/drumrobot) <br>

### License/Terms of Use: <br>
MIT <br>


## Use Case: <br>
Developers and engineering agents use this skill to write failing tests before implementation, run the relevant test suites, fix defects, and report verification results during coding and bug-fix work. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill may activate on broad testing or bug-fix language and push the agent toward writing and running tests before discussion. <br>
Mitigation: Use it where a strict TDD workflow is desired and review the proposed tests and execution scope before relying on results. <br>
Risk: The skill can lead an agent to edit tests and run project test commands. <br>
Mitigation: Run it in an appropriate development workspace and review test changes before deployment or commit. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/drumrobot/tdd) <br>
- [TDD cycle guide](cycle.md) <br>
- [Test run guide](run.md) <br>
- [Test strategies guide](test-strategies.md) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, guidance] <br>
**Output Format:** [Markdown guidance with inline code and shell command examples] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Produces process guidance and test-related changes; it does not define a fixed machine-readable output schema.] <br>

## Skill Version(s): <br>
0.3.0 (source: server release evidence and target metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
