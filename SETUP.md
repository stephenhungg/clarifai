# Clarifai Setup Guide

## Quick Start (5 minutes)

### 1. Create Environment File

```bash
# Copy the example file
cp .env.example .env
```

### 2. Add Your Gemini API Key (Required)

Edit `.env` and add your Gemini API key:

```bash
GEMINI_API_KEY=your_actual_api_key_here
```

Get your key from: https://aistudio.google.com/app/apikey

### 3. Start the Application

```bash
./start.sh
```

That's it! The app will run in **dev mode** with:
- ✅ Single-user access (no auth required)
- ✅ All features work locally
- ✅ Perfect for testing and development

Visit:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs

---

## Multi-User Setup (Optional)

To enable authentication and multi-user support:

### 1. Create Supabase Project

1. Go to https://supabase.com
2. Create a new project
3. Save your database password

### 2. Get Supabase Credentials

In Supabase Dashboard:

**Settings → API:**
- Copy `Project URL` → `SUPABASE_URL`
- Copy `anon public` key → `SUPABASE_ANON_KEY`
- Copy `service_role` key → `SUPABASE_SERVICE_KEY`

**Settings → Database → Connection string (URI):**
- Copy and replace `[YOUR-PASSWORD]` → `SUPABASE_DATABASE_URL`

### 3. Run Database Schema

1. In Supabase Dashboard, go to **SQL Editor**
2. Click "New Query"
3. Copy contents from `backend/app/database/schema.sql`
4. Paste and click "Run"

### 4. Enable Google OAuth

1. In Supabase Dashboard: **Authentication → Providers**
2. Enable "Google"
3. Add your Google OAuth credentials

**Get Google OAuth credentials:**
- Go to https://console.cloud.google.com
- Create OAuth Client ID (Web application)
- Add authorized redirect URI: `https://<your-project-ref>.supabase.co/auth/v1/callback`

### 5. Update .env File

Add your Supabase credentials to `.env`:

```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.your-project-ref.supabase.co:5432/postgres

NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 6. Restart the Application

```bash
./stop.sh  # Stop current instance
./start.sh # Restart with Supabase enabled
```

Now you have:
- ✅ Google OAuth login
- ✅ Per-user data isolation
- ✅ Rate limiting (5 videos/day per user)
- ✅ Production-ready multi-user support

---

## Environment Variables Reference

### Required
- `GEMINI_API_KEY` - Google Gemini API key for AI features

### Optional (Multi-User)
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `SUPABASE_DATABASE_URL` - PostgreSQL connection string

### Optional (Storage)
- `BLOB_READ_WRITE_TOKEN` - Vercel Blob for persistent video storage

### Frontend
- `NEXT_PUBLIC_SUPABASE_URL` - Same as `SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Same as `SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_URL` - Backend URL (default: http://localhost:8000)
- `NEXT_PUBLIC_WS_URL` - WebSocket URL (default: ws://localhost:8000)

---

## Stopping the Application

```bash
./stop.sh
```

---

## Troubleshooting

### "GEMINI_API_KEY not found"
- Make sure you copied `.env.example` to `.env`
- Add your actual API key to the `.env` file

### "Could not validate credentials"
- Check that Supabase credentials are correct in `.env`
- Verify your Supabase project is active (not paused)

### Videos not persisting after server restart
- Set `BLOB_READ_WRITE_TOKEN` for Vercel Blob storage
- Or accept that videos are temporary in dev mode

---

## Production Deployment

See `MIGRATION_GUIDE.md` for complete deployment instructions for:
- Railway (backend)
- Vercel (frontend)
- Supabase (database)
