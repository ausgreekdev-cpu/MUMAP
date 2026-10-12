import { Link } from 'react-router-dom';

export function Privacy() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] py-12 px-6">
      <div className="max-w-2xl mx-auto card">
        <h1 className="text-2xl font-bold mb-6">Privacy Policy</h1>
        <div className="space-y-4 text-sm text-gray-300 leading-relaxed">
          <p className="text-gray-400">Last updated: October 2026</p>

          <h2 className="text-lg font-semibold text-white pt-2">Overview</h2>
          <p>
            MUMAP (Multi-Agent Platform) is a self-hosted application. The
            Microsoft Store listing distributes a client application; all data
            is stored on servers you (or your organization) control. We do not
            operate a central MUMAP service and we do not collect your data.
          </p>

          <h2 className="text-lg font-semibold text-white pt-2">What data exists</h2>
          <p>
            Accounts you create (email, username), agents and tasks you define,
            API keys you generate, webhook endpoints you register, audit logs of
            actions on your instance, and usage records for billing on your
            instance. Everything lives in the database of your MUMAP server.
          </p>

          <h2 className="text-lg font-semibold text-white pt-2">Third parties</h2>
          <p>
            The application itself does not transmit data to the developer.
            Optional LLM providers you configure (for example OpenAI or
            Anthropic) receive prompts you send to your agents, under your own
            accounts and their terms. Microsoft Store handles your purchase and
            install entitlement under Microsoft&rsquo;s privacy policy.
          </p>

          <h2 className="text-lg font-semibold text-white pt-2">Purchases</h2>
          <p>
            The Store version is a paid client application. Payments are
            processed by Microsoft; the developer never sees your payment card
            details. A purchase grants a license to the client application; it
            does not include hosting, which remains your responsibility.
          </p>

          <h2 className="text-lg font-semibold text-white pt-2">Contact</h2>
          <p>
            Questions about this policy or the application: open an issue at{' '}
            <a
              className="text-indigo-400 hover:text-indigo-300"
              href="https://github.com/ausgreekdev-cpu/MUMAP"
              target="_blank"
              rel="noreferrer"
            >
              github.com/ausgreekdev-cpu/MUMAP
            </a>
            .
          </p>
        </div>
        <div className="mt-8 pt-6 border-t border-white/10">
          <Link to="/login" className="text-sm text-indigo-400 hover:text-indigo-300">
            ← Back to sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
