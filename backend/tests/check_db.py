"""Quick DB state check for test setup"""
import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / '.env')

from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    # Find the tech user
    user = await db.users.find_one({'email': 'tech@battwheels.in'}, {'_id': 0, 'user_id': 1, 'email': 1, 'role': 1, 'name': 1, 'password_hash': 1})
    print('Tech user:', user)
    
    # Find admin user
    admin = await db.users.find_one({'email': 'admin@battwheels.in'}, {'_id': 0, 'user_id': 1, 'email': 1, 'role': 1, 'organization_id': 1})
    print('Admin user:', admin)
    
    # Find emp_7e79d8916b6b
    emp = await db.employees.find_one({'employee_id': 'emp_7e79d8916b6b'}, {'_id': 0, 'employee_id': 1, 'first_name': 1, 'last_name': 1, 'organization_id': 1, 'status': 1, 'user_id': 1})
    print('Employee:', emp)
    
    # Count payroll docs
    count_total = await db.payroll.count_documents({'employee_id': 'emp_7e79d8916b6b'})
    print(f'Total payroll docs: {count_total}')
    
    # Get distinct statuses
    sample = await db.payroll.find({'employee_id': 'emp_7e79d8916b6b'}, {'_id': 0, 'status': 1, 'year': 1, 'month': 1}).limit(5).to_list(5)
    print('Sample payroll docs:', sample)
    
    # Count by status
    gen_count = await db.payroll.count_documents({'employee_id': 'emp_7e79d8916b6b', 'status': 'generated'})
    proc_count = await db.payroll.count_documents({'employee_id': 'emp_7e79d8916b6b', 'status': 'processed'})
    paid_count = await db.payroll.count_documents({'employee_id': 'emp_7e79d8916b6b', 'status': 'paid'})
    print(f'Status counts - generated: {gen_count}, processed: {proc_count}, paid: {paid_count}')
    
    # FY 2025-26 records (year=2026, months=Jan/Feb/Mar OR year=2025, months=Apr-Dec)
    fy_q4 = await db.payroll.count_documents({
        'employee_id': 'emp_7e79d8916b6b',
        'year': 2026,
        'month': {'$in': ['January', 'February', 'March']},
        'status': {'$in': ['generated', 'processed', 'paid']}
    })
    print(f'FY 2025-26 Q4 payroll (year=2026, Jan/Feb/Mar): {fy_q4}')
    
    # Check organization membership for tech user
    if user:
        membership = await db.organization_users.find_one({'user_id': user['user_id']}, {'_id': 0})
        print('Tech membership:', membership)
    
    # Check organization for admin
    if admin:
        org = await db.organizations.find_one({'organization_id': admin.get('organization_id')}, {'_id': 0, 'organization_id': 1, 'name': 1, 'company_name': 1})
        print('Admin org:', org)
    
    # Check webhook_logs indexes
    indexes = await db.webhook_logs.index_information()
    print('webhook_logs indexes:', list(indexes.keys()))
    
    # Check a few other collection indexes
    for coll_name in ['composite_items', 'units', 'webhook_logs']:
        if coll_name in await db.list_collection_names():
            idxs = await db[coll_name].index_information()
            has_org = any('organization_id' in str(v.get('key', {})) for v in idxs.values())
            print(f'{coll_name} has org_id index: {has_org}')
    
    client.close()

asyncio.run(main())
