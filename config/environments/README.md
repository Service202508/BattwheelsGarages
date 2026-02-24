# Battwheels OS — Environment Configuration

## Three Environments

### production (.env)
- Database: battwheels (MongoDB — live production data)
- Org: Battwheels Garages (real data, real customers, real money)
- Rule: NEVER use for testing. NEVER seed test data here.

### staging (.env.staging)
- Database: battwheels_staging (separate MongoDB database)
- Org: Battwheels Garages Staging (mirrors prod structure, fake data)
- Rule: Test all code changes here before promoting to production.

### development (.env.development)
- Database: battwheels_dev (local or separate database)
- Org: Battwheels Dev + Volt Motors Demo
- Rule: Break things here freely. Wipe and reseed anytime.

## Promotion Path
development -> staging -> production
NEVER skip staging for any change affecting financial data, auth, or tenant isolation.

## Demo Credentials (for sales demos — never show production)
- Login: demo@voltmotors.in
- Password: Demo@12345
- Reseed anytime: `make seed-demo`

## Dev Credentials (for internal testing only)
- Login: dev@battwheels.internal
- Password: DevTest@123
- Reseed anytime: `make reseed-dev`
