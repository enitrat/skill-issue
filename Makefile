.PHONY: skill-install skill-update skill-list emil-sync

skill-install skill-update:
	./scripts/install-skills --yes

skill-list:
	npx skills list

emil-sync:
	./plugins/emil/sync
