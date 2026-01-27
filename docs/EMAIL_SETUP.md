# Email Setup with Resend

Farewellify uses **Resend** to send emails. Resend is simple, reliable, and has a generous free tier.

## Why Resend?

- **No Gmail setup required** - Just an API key
- **Free tier**: 100 emails/day, 3000/month
- **Simple API** - No complex OAuth flows
- **Reliable delivery** - Built for developers

## Setup Steps

### 1. Create Resend Account

1. Go to [resend.com](https://resend.com)
2. Sign up (free)
3. Verify your email

### 2. Get API Key

1. Go to [API Keys](https://resend.com/api-keys)
2. Click "Create API Key"
3. Name it (e.g., "Farewellify")
4. Copy the key (starts with `re_`)

### 3. Configure Environment

Add to your `.env`:

```bash
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxx
EMAIL_FROM=Farewellify <farewell@pandata.de>
```

### 4. Verify Domain (Optional but Recommended)

For production, verify your domain:

1. Go to [Domains](https://resend.com/domains)
2. Add your domain (e.g., `pandata.de`)
3. Add the DNS records Resend provides
4. Wait for verification (usually 5-10 minutes)

Without domain verification, you can still test with:
```bash
EMAIL_FROM=onboarding@resend.dev
```

## Usage

Once configured, emails are sent automatically when you:
- Click "Send Invitations" in the admin dashboard
- Click "Send Reminders" for pending submissions

## Email Templates

The app uses HTML email templates with Pandata branding:

### Invitation Email
- **Subject:** `Farewell Card for {Name} 🎉`
- **Content:**
  - Greeting with recipient's first name
  - Announcement of honoree's last day with date
  - Call-to-action to contribute via the farewell app
  - Personalized submit link (no login required)
  - Organizer name in footer

### Reminder Email
- **Subject:** `Reminder: Farewell Card for {Name} ⏰`
- **Content:**
  - Friendly reminder about the upcoming last day
  - Note that contribution hasn't been received yet
  - Same personalized submit link
- Only sent to team members who haven't submitted

## Troubleshooting

### "Email not configured"

Check that:
1. `RESEND_API_KEY` is in `.env`
2. The key starts with `re_`
3. The app was restarted after adding the key

### Emails not arriving

1. Check spam folder
2. Verify domain if using custom FROM address
3. Check Resend dashboard for delivery logs

### Rate limits

Free tier limits:
- 100 emails/day
- 3000 emails/month
- 1 email/second

For higher volumes, upgrade to a paid plan.

## Alternative: Supabase Edge Functions

If you want emails to be triggered directly from Supabase (e.g., on database changes), you can set up an Edge Function:

1. Create Edge Function in Supabase dashboard
2. Add Resend integration
3. Trigger on `team_members` insert or `submissions` insert

This is more advanced but allows for event-driven emails.

## Comparison with Previous Gmail Setup

| Feature | Gmail OAuth | Resend |
|---------|-------------|--------|
| Setup complexity | High (OAuth flow) | Low (API key) |
| User needs to login | Yes | No |
| Free tier | 500 emails/day | 100 emails/day |
| Domain required | No | Recommended |
| Maintenance | Token refresh | None |
