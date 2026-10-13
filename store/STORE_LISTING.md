# Microsoft Store Listing Copy (MUMAP v2.1.0)

Paste-ready fields for Partner Center. Character counts noted where the Store
enforces a limit.

---

## Product name (max 30)

```
MUMAP
```

## Short description (max 100 chars, 99 used)

```
Orchestrate AI agents on your own server — private, self-hosted, no cloud lock.
```

## Long description (paste as-is)

```
MUMAP (Multi-Agent Orchestration Platform) is a developer tool for building and
coordinating teams of AI agents on infrastructure YOU control.

Install this app to get a polished, installable client for Windows. Point it at
your own MUMAP server (or a colleague's) with the built-in one-time setup
screen, then manage agents, tasks, and workflows from your Start menu.

WHY SELF-HOSTED?
• Your prompts, keys, and data never leave your server
• Works with your own OpenAI / Anthropic API keys — no middleman markup
• Docker one-liner deployment with full REST API and webhooks

WHAT YOU CAN DO
• Agents — create specialized AI agents with models, tools, and skills
• Tasks — assign, queue, and track work across agents with live status
• Real-time dashboard — usage, health, and activity at a glance
• Marketplace — install ready-made agent templates
• API keys & audit logs — programmatic access with per-key tracking
• Usage plans — free / pro / enterprise tiers seeded on your instance

WHAT YOU NEED
• A Windows 10/11 PC with internet access
• A MUMAP server you can reach over HTTPS (Docker or manual install — see the
  project README), or ask your team admin for the server URL
• Your own LLM API keys (OpenAI, Anthropic, ...) configured on the server

This is a one-time purchase for the client app. Hosting and LLM usage are your
own and are NOT included — you deploy the open-source backend yourself.

Source code: github.com/ausgreekdev-cpu/MUMAP
```

## What's New (v2.1.0)

```
• Installable PWA client with first-run server setup screen
• Privacy policy page
• API-key authentication and full audit log UI
• Rate limiting and signed webhook delivery
• Database migrations (Alembic) for clean upgrades
• Reliability fixes: Anthropic tool calls, CORS, chat error handling
```

## Search keywords (7 max, comma-separated in one field)

```
AI agents, multi-agent, orchestration, self-hosted, LLM, developer tools, automation
```

## Category

- Primary: **Developer tools** (fallback: Productivity)

## Pricing

- Model: **Paid, one-time** (no trial required; optional free trial allowed)
- Placeholder: **$24.99** — set your final price in Partner Center
- No in-app purchase products are declared

## Support / website / privacy URLs

| Field | Value |
|---|---|
| Website | `https://github.com/ausgreekdev-cpu/MUMAP` |
| Support | `https://github.com/ausgreekdev-cpu/MUMAP/issues` |
| Privacy policy | `https://ausgreekdev-cpu.github.io/MUMAP/privacy` |

## System requirements

```
Windows 10 (1809+) or Windows 11, x64
Internet connection
Reachable MUMAP backend over HTTPS (self-hosted)
```

## Screenshots (you capture — 1280×764 min, 5–8 recommended)

Suggested set of your running app:
1. Dashboard with health/usage cards
2. Agents list + agent detail
3. Agent chat
4. Tasks board with statuses
5. Marketplace templates
6. Settings → Activity (audit log)
7. First-run `/setup` server screen
8. Dark theme optional extra

## Age rating

Answer the questionnaire conservatively (no violence/adult content; likely
**3+ / Everyone**). The app is a productivity tool with user-generated text
prompts only.

## Submission notes (not shown publicly)

```
Self-hosted backend client. The packaged app opens the official PWA frontend;
users configure their own server URL on first run. No user data is collected by
the developer. Source open on GitHub under MIT.
```
