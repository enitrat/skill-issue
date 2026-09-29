.PHONY: skill-install skill-update skill-list pstack-sync emil-sync

skill-install skill-update:
	./scripts/install-skills --yes

skill-list:
	npx skills list

pstack-sync:
	./plugins/pstack/sync

emil-sync:
	./plugins/emil/sync
