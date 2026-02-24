# Battwheels OS — Development Commands

## Seed demo org in development database
seed-demo:
	cd /app && python scripts/seed_demo_org.py --env development

## Seed demo org in staging database
seed-demo-staging:
	cd /app && python scripts/seed_demo_org.py --env staging

## Seed dev org in development database
seed-dev:
	cd /app && python scripts/seed_dev_org.py --env development

## Wipe and reseed both dev orgs (safe — development db only)
reseed-dev: seed-dev seed-demo
	@echo "Dev environment reseeded"

## Verify production org is intact (read-only check)
check-prod:
	cd /app && python scripts/verify_prod_org.py

.PHONY: seed-demo seed-demo-staging seed-dev reseed-dev check-prod
