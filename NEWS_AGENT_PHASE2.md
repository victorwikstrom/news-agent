# Phase 2 — User Interface & Registration

Build a web UI where users can sign up, select news sources, and configure their delivery channel (email or Slack). The agent from phase 1 is updated to read user configuration from the database instead of a static YAML file.

---

## Architecture

```
news-agent/
├── agent/                    # Phase 1 – Python agent (updated)
│   ├── fetcher.py
│   ├── filter.py
│   ├── summarizer.py
│   └── publisher.py          # Updated: per-user email + Slack support
│
└── web/                      # New – Next.js app
    ├── app/
    │   ├── page.tsx           # Landing page
    │   ├── auth/
    │   │   └── callback/
    │   │       └── route.ts   # Supabase OAuth callback
    │   ├── dashboard/
    │   │   └── page.tsx       # Authenticated view: manage subscription
    │   └── api/
    │       └── subscription/
    │           └── route.ts   # API route: save settings
    ├── components/
    │   ├── SourcePicker.tsx   # Select news sources
    │   ├── ChannelSetup.tsx   # Configure Slack/email
    │   └── SubscriptionForm.tsx
    ├── lib/
    │   └── supabase.ts        # Supabase client
    └── middleware.ts          # Protect /dashboard with auth
```

---

## Tech Stack

| Component | Choice |
|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript |
| Styling | Tailwind CSS |
| Auth + DB | Supabase (auth + postgres) |
| Hosting | Vercel |
| Email | Resend API |
| Slack | Incoming Webhook (user pastes their own URL) |

---

## Database Schema (Supabase)

Run these in the Supabase SQL Editor:

```sql
-- User subscriptions
create table subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  is_active boolean default true,

  -- Delivery channel
  channel text check (channel in ('email', 'slack')) not null,
  email text,                  -- populated if channel = 'email'
  slack_webhook_url text,      -- populated if channel = 'slack'

  -- Schedule
  digest_time time default '07:00',
  timezone text default 'Europe/Stockholm',
  weekdays_only boolean default true
);

-- Selected sources per user
create table user_sources (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  source_id text not null,     -- matches id in sources.yaml
  enabled boolean default true
);

-- Row Level Security
alter table subscriptions enable row level security;
alter table user_sources enable row level security;

create policy "Users can only access their own data"
  on subscriptions for all using (auth.uid() = user_id);

create policy "Users can only access their own sources"
  on user_sources for all using (auth.uid() = user_id);
```

---

## Phase 2a — Supabase & Authentication

**Goal:** Users can sign up and log in.

**Tasks:**
- Create a Supabase project at supabase.com
- Run the SQL above in the Supabase SQL Editor
- Initialize Next.js app: `npx create-next-app@latest web --typescript --tailwind --app`
- Add Supabase client: `npm install @supabase/supabase-js @supabase/ssr`
- Create `lib/supabase.ts` with server and browser clients
- Implement `middleware.ts` to protect `/dashboard`
- Enable email/password auth in Supabase Dashboard under Authentication → Providers
- Build basic auth pages: sign up, log in, forgot password

**Environment variables:**
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...   # server-side only
```

**Deliverable:** Users can register and log in. `/dashboard` requires authentication.

---

## Phase 2b — Landing Page

**Goal:** A clear page that explains the service and leads to registration.

**Tasks:**
- Build `app/page.tsx` with:
  - Hero: headline, short description, CTA button ("Get started for free")
  - How it works: 3 steps (Pick sources → Pick channel → Get digest)
  - Example mockup of a Slack message
- No complex design needed — focus on clarity

**Deliverable:** Landing page with a working "Sign up" link.

---

## Phase 2c — Dashboard & Subscription Form

**Goal:** A logged-in user can configure their digest.

**Tasks:**

**SourcePicker component:**
- Load all available sources from a static list (ported from `sources.yaml`)
- Display as clickable cards grouped by category (Sweden, Tech, Finance, World)
- Save selected sources to the `user_sources` table in Supabase

**ChannelSetup component:**
- Toggle: Email / Slack
- If email: show email field (pre-filled with account email)
- If Slack: show Webhook URL field + link to setup instructions
- Validate that webhook URL starts with `https://hooks.slack.com/`

**SubscriptionForm:**
- Digest time picker (default 07:00)
- Weekdays only toggle
- Save button → POST to `/api/subscription`

**`app/api/subscription/route.ts`:**
```typescript
// Receive and validate form data
// Upsert to subscriptions table using service role key
// Return 200 OK or error message
```

**Deliverable:** Logged-in user can select sources, choose a channel, and save settings.

---

## Phase 2d — Update the Python Agent

**Goal:** The agent reads user configuration from Supabase and sends individual digests.

**Tasks:**
- Add `supabase-py` as a dependency: `uv add supabase`
- Update `main.py`:
  - Fetch all active subscriptions from Supabase
  - Loop over each user
  - Fetch the user's selected sources
  - Run fetch → filter → summarize → publish per user
- Update `publisher.py`:
  - Support `channel = 'slack'`: use the user's own webhook URL
  - Support `channel = 'email'`: send via Resend API
- Add new GitHub Actions secrets: `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`

**Email via Resend:**
```python
import resend
resend.api_key = os.environ["RESEND_API_KEY"]

resend.Emails.send({
    "from": "digest@yourdomain.com",
    "to": user.email,
    "subject": f"News Digest – {today}",
    "html": render_email_template(articles)
})
```

**Deliverable:** Each user receives their personal digest via their chosen channel.

---

## Deployment

**Vercel (frontend):**
```bash
cd web
vercel deploy
```
Add environment variables in Vercel Dashboard under Settings → Environment Variables.

**GitHub Actions (agent):**
Add new secrets to the repo:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `RESEND_API_KEY`

---

## Environment Variables — Full List

```env
# web/.env.local
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# agent/.env
ANTHROPIC_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
RESEND_API_KEY=
```

---

## Out of Scope for This Phase (saved for V3)

- No paywall or subscription plans
- No admin panel
- No per-user keyword filtering
- No verification of Slack webhook URLs

---

## Build Order

1. Supabase project + database tables
2. Next.js app with auth (2a)
3. Landing page (2b)
4. Dashboard + form (2c)
5. Deploy to Vercel
6. Update the Python agent (2d)
7. End-to-end test: sign up → pick sources → wait for digest
