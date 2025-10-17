#!/usr/bin/env python3
"""
Database migration script for Phase 1-4 changes:
1. Create email_subscribers table
2. Make wishes.user_id nullable
"""

from app import app, db
from models import EmailSubscriber
from sqlalchemy import inspect, text

def run_migrations():
    """Run database migrations."""
    with app.app_context():
        inspector = inspect(db.engine)

        # Check existing tables
        tables = inspector.get_table_names()
        print(f'✓ Found {len(tables)} existing tables: {", ".join(tables)}')

        # 1. Create email_subscribers table if it doesn't exist
        if 'email_subscribers' not in tables:
            print('\n→ Creating email_subscribers table...')
            EmailSubscriber.__table__.create(db.engine)
            print('✓ email_subscribers table created successfully')
        else:
            print('\n✓ email_subscribers table already exists')

        # 2. Make wishes.user_id nullable if it isn't already
        if 'wishes' in tables:
            columns = inspector.get_columns('wishes')
            user_id_col = next((c for c in columns if c['name'] == 'user_id'), None)

            if user_id_col:
                print(f'\n→ Checking wishes.user_id: nullable={user_id_col.get("nullable", False)}')

                if not user_id_col.get('nullable', False):
                    print('→ Making wishes.user_id nullable...')
                    with db.engine.connect() as conn:
                        conn.execute(text('ALTER TABLE wishes ALTER COLUMN user_id DROP NOT NULL'))
                        conn.commit()
                    print('✓ wishes.user_id is now nullable')
                else:
                    print('✓ wishes.user_id is already nullable')
            else:
                print('⚠ user_id column not found in wishes table')

        print('\n✅ All migrations completed successfully!')

        # Verify final state
        final_tables = inspector.get_table_names()
        print(f'\n✓ Final table count: {len(final_tables)}')
        print(f'  Tables: {", ".join(sorted(final_tables))}')

if __name__ == '__main__':
    print('='*60)
    print('Phase 1-4 Database Migrations')
    print('='*60)
    run_migrations()
