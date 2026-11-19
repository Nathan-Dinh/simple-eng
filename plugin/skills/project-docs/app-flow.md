# App Flow guidance

**New project.** Derive the flows from the PRD's user stories. For each MVP story, ask or propose how the person arrives (a link, sign-in, a notification, a command), the steps and screens in order, the decisions and branches, the outcome, and what happens when a step fails. Ask early about sign-up, sign-in, roles, and permission boundaries, because they shape most flows.

**Existing project.** Read the router or route definitions, navigation components, page or screen directories, command definitions, handlers that drive multi-step processes, and end-to-end tests. Record each flow found, labeled verified with the paths. Treat unreachable or dead routes as drift candidates, not as intent.

Each primary flow names its actor, trigger, numbered steps, outcome, and related REQ IDs. Cover the error, empty, expired-session, and permission-denied paths for flows that touch money, data loss, or access. List each screen or step once in the inventory and refer to it from the flows. Leave visual design to the UI/UX Design Brief.

If people do not move through the product interactively (a library, a batch job), write `Not applicable: <reason>` under "Primary flows".
