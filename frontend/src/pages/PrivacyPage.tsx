export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="max-w-4xl mx-auto px-6 py-16">
        <a href="/" className="text-brand-600 dark:text-brand-400 hover:underline text-sm mb-8 inline-block">&larr; Back to MUMAP</a>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Privacy Policy</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">Last updated: July 23, 2026</p>

        <div className="prose dark:prose-invert max-w-none space-y-8 text-gray-700 dark:text-gray-300">
          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">1. Introduction</h2>
            <p>MUMAP ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our multi-agent orchestration platform, including our website, mobile applications, and related services (collectively, the "Service").</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">2. Information We Collect</h2>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mt-4">Account Information</h3>
            <ul className="list-disc pl-6 space-y-1">
              <li>Email address</li>
              <li>Display name</li>
              <li>Password (stored securely using bcrypt hashing)</li>
              <li>Organization name (if applicable)</li>
            </ul>

            <h3 className="text-lg font-medium text-gray-900 dark:text-white mt-4">Usage Data</h3>
            <ul className="list-disc pl-6 space-y-1">
              <li>Agent configurations and task history</li>
              <li>API call logs and performance metrics</li>
              <li>Feature usage patterns</li>
              <li>Device type, browser, and operating system</li>
              <li>IP address and connection timestamps</li>
            </ul>

            <h3 className="text-lg font-medium text-gray-900 dark:text-white mt-4">Payment Information</h3>
            <p>Subscription payments are processed through Google Play (Android) or Microsoft Store (Windows). We do not store credit card numbers or payment details on our servers. We only retain your subscription status and transaction identifiers provided by the payment processor.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">3. How We Use Your Information</h2>
            <ul className="list-disc pl-6 space-y-1">
              <li>To provide, maintain, and improve the Service</li>
              <li>To authenticate your account and prevent fraud</li>
              <li>To process subscriptions and manage billing</li>
              <li>To send service-related communications (e.g., security alerts, billing notices)</li>
              <li>To analyze usage patterns and optimize platform performance</li>
              <li>To comply with legal obligations</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">4. Data Sharing</h2>
            <p>We do <strong>not</strong> sell your personal data. We may share information with:</p>
            <ul className="list-disc pl-6 space-y-1">
              <li><strong>Service providers:</strong> Hosting (cloud infrastructure), payment processors (Google, Microsoft), and analytics tools that help us operate the Service.</li>
              <li><strong>Legal requirements:</strong> When required by law, subpoena, or other governmental process.</li>
              <li><strong>Business transfers:</strong> In connection with a merger, acquisition, or sale of assets, with notice to users.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">5. Data Security</h2>
            <p>We implement industry-standard security measures including:</p>
            <ul className="list-disc pl-6 space-y-1">
              <li>Encrypted data transmission (TLS/HTTPS)</li>
              <li>Bcrypt password hashing with salt</li>
              <li>JWT-based authentication with expiration</li>
              <li>Rate limiting and API key authentication</li>
              <li>Regular security audits</li>
            </ul>
            <p className="mt-2">However, no method of electronic transmission or storage is 100% secure, and we cannot guarantee absolute security.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">6. Data Retention</h2>
            <p>We retain your account data for as long as your account is active. Upon account deletion, we remove your personal data within 30 days, except where retention is required by law. Anonymized and aggregated usage data may be retained indefinitely.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">7. Your Rights</h2>
            <p>Depending on your jurisdiction, you may have the right to:</p>
            <ul className="list-disc pl-6 space-y-1">
              <li>Access the personal data we hold about you</li>
              <li>Request correction of inaccurate data</li>
              <li>Request deletion of your personal data</li>
              <li>Object to or restrict processing of your data</li>
              <li>Data portability — receive your data in a structured, machine-readable format</li>
              <li>Withdraw consent at any time</li>
            </ul>
            <p className="mt-2">To exercise these rights, contact us at <a href="mailto:privacy@mumap.app" className="text-brand-600 dark:text-brand-400 underline">privacy@mumap.app</a>.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">8. Children's Privacy</h2>
            <p>The Service is not intended for children under 13 (or under 16 in the EU). We do not knowingly collect data from children. If we learn that we have collected data from a child, we will delete it promptly.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">9. International Transfers</h2>
            <p>Your data may be processed in countries other than your own. We ensure appropriate safeguards are in place for international transfers, including Standard Contractual Clauses where required by applicable law.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">10. Cookies</h2>
            <p>We use essential cookies for authentication and session management. We do not use advertising or third-party tracking cookies. You can control cookie settings through your browser.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">11. Changes to This Policy</h2>
            <p>We may update this Privacy Policy from time to time. We will notify you of material changes by posting the updated policy on our website and updating the "Last updated" date. Your continued use of the Service after changes constitutes acceptance of the updated policy.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">12. Contact Us</h2>
            <p>If you have questions about this Privacy Policy, contact us at:</p>
            <p>
              <strong>Email:</strong> <a href="mailto:privacy@mumap.app" className="text-brand-600 dark:text-brand-400 underline">privacy@mumap.app</a><br />
              <strong>Website:</strong> <a href="https://mumap.app" className="text-brand-600 dark:text-brand-400 underline">https://mumap.app</a>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
