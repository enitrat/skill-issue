.PHONY: skill-install skill-update skill-list codex-setup emil-sync thermos-sync

skill-install:
	./scripts/install-skills --yes

skill-update:
	./scripts/install-skills --update

skill-list:
	npx skills list

codex-setup:
	./scripts/install-skills --global --agent codex --skill '*' --yes
	codex plugin marketplace add michael-denyer/pstack-claude
	codex plugin add pstack@pstack-claude

emil-sync:
	./plugins/emil/sync

thermos-sync:
	./plugins/thermos/sync
