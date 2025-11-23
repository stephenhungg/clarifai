# Database Migration Guide

This guide explains how to migrate from JSON file storage to PostgreSQL database storage.

## Overview

The application now supports **both JSON and database storage** automatically:
- **JSON mode** (default): Uses `storage/papers_db.json` when `SUPABASE_DATABASE_URL` is not set
- **Database mode**: Uses PostgreSQL (Supabase) when `SUPABASE_DATABASE_URL` is set

The storage layer automatically switches based on your configuration - no code changes needed!

## Migration Steps

### 1. Set Up Supabase Database

1. Go to your Supabase project dashboard
2. Navigate to **Settings → Database**
3. Copy the **Connection string** (URI format)
4. Add it to your `.env` file:
   ```
   SUPABASE_DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT].supabase.co:5432/postgres
   ```

### 2. Run Database Schema

The database schema is already defined in `backend/app/database/schema.sql`. Run it in your Supabase SQL editor to create the tables.

### 3. Migrate Existing Data

Run the migration script to move papers from JSON to database:

```bash
# Dry run (see what would be migrated)
python backend/migrate_to_db.py --dry-run

# Actual migration (creates backup automatically)
python backend/migrate_to_db.py

# Skip backup
python backend/migrate_to_db.py --no-backup
```

The script will:
- ✅ Load all papers from `storage/papers_db.json`
- ✅ Create users for papers with `user_id`
- ✅ Migrate papers, concepts, and videos to database
- ✅ Create a timestamped backup of your JSON file
- ✅ Handle errors gracefully

### 4. Verify Migration

After migration, the app will automatically use the database. You can verify by:
- Checking that papers still appear in your library
- Uploading a new paper (should save to database)
- Checking Supabase dashboard for data in tables

## Storage System

### Automatic Mode Detection

The `PaperStorage` service automatically detects which storage to use:

```python
# Automatically uses database if SUPABASE_DATABASE_URL is set
paper = PaperStorage.get_paper(paper_id, user_id)
PaperStorage.save_paper(paper, user_id)
```

### Benefits of Database Storage

✅ **Scalable**: Handles millions of papers efficiently  
✅ **Concurrent**: Safe for multiple users/requests  
✅ **Queryable**: Fast searches and filtering  
✅ **Reliable**: ACID transactions prevent data loss  
✅ **Per-user isolation**: Row-level security policies  

### Video Generation Limits

Per-user limits are now properly tracked:
- **5 videos per day** per user (enforced)
- **3 concurrent videos** per user (enforced)
- Limits work in both JSON and database modes

## Rollback

If you need to rollback to JSON storage:
1. Remove `SUPABASE_DATABASE_URL` from `.env`
2. Restore from backup: `cp storage/papers_db.json.backup.* storage/papers_db.json`
3. Restart the backend

## Troubleshooting

### Migration fails with "user not found"
- The script creates a dev user for papers without `user_id`
- Papers will be assigned to user `00000000-0000-0000-0000-000000000000`

### Database connection errors
- Verify `SUPABASE_DATABASE_URL` is correct
- Check Supabase project is active
- Ensure database tables exist (run `schema.sql`)

### Papers not showing after migration
- Check that `user_id` matches your Supabase auth user ID
- Verify papers were migrated (check Supabase dashboard)
- Check backend logs for errors
