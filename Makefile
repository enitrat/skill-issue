.PHONY: skill-install skill-update skill-list

skill-install skill-update:
	./scripts/install-skills --yes

skill-list:
	npx skills list
