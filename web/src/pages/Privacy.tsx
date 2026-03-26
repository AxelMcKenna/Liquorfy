import { Link } from "react-router-dom";

export const Privacy = () => {
  return (
    <div className="min-h-screen bg-background">
      <header className="bg-primary py-6">
        <div className="px-4">
          <Link to="/" className="text-xl font-semibold text-white tracking-tight font-display">
            LIQUORFY
          </Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-semibold text-foreground mb-2">Privacy Policy</h1>
        <p className="text-sm text-muted-foreground mb-10">Last updated: 26 March 2026</p>

        <div className="space-y-8 text-sm leading-relaxed text-foreground/90">
          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Overview</h2>
            <p>
              Liquorfy is a liquor price comparison service for New Zealand. We help you find the
              best deals from major retailers near you. This policy explains what data we collect,
              how we use it, and your rights.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Data We Collect</h2>
            <p className="mb-3">
              Liquorfy can be used without an account. If you choose to create an account, we collect
              additional data as described below.
            </p>

            <h3 className="font-semibold text-foreground mt-4 mb-2">Without an account</h3>
            <ul className="list-disc pl-5 space-y-2">
              <li>
                <strong>Location data</strong> — If you grant permission, we use your device's
                location to show nearby stores and prices. This data is sent to our server to perform
                geographic searches but is not stored or linked to any identifier.
              </li>
              <li>
                <strong>Search queries</strong> — Product searches you perform are processed by our
                server to return results. We do not log individual search queries tied to any user.
              </li>
              <li>
                <strong>Analytics</strong> — We use Vercel Analytics and Speed Insights to collect
                anonymous, aggregated usage data (page views, performance metrics). These services do
                not use cookies and do not track individual users across sites.
              </li>
            </ul>

            <h3 className="font-semibold text-foreground mt-4 mb-2">With an account</h3>
            <p className="mb-2">
              If you sign in via Google or Apple, we additionally collect and store:
            </p>
            <ul className="list-disc pl-5 space-y-2">
              <li>
                <strong>Email address</strong> — Provided by your Google or Apple account during
                sign-in. Used to send price alert notifications and for account identification.
              </li>
              <li>
                <strong>Name and profile photo</strong> — If provided by your sign-in provider.
                Used only for display within the app.
              </li>
              <li>
                <strong>Location preferences</strong> — Your saved default location and search radius,
                so they persist between sessions.
              </li>
              <li>
                <strong>Price alerts</strong> — Products you choose to track and the price thresholds
                you set.
              </li>
              <li>
                <strong>Favourites</strong> — Products you mark as favourites.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Data We Do Not Collect</h2>
            <ul className="list-disc pl-5 space-y-2">
              <li>We do not collect payment or financial information.</li>
              <li>We do not track you across other websites or apps.</li>
              <li>We do not sell or share data with advertisers.</li>
              <li>We do not store your Google or Apple password.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">How We Use Your Data</h2>
            <ul className="list-disc pl-5 space-y-2">
              <li>To show liquor prices from stores near your location.</li>
              <li>To return relevant product search results.</li>
              <li>To monitor and improve site performance via anonymous analytics.</li>
              <li>To send you price alert emails when products you track drop in price or go on promotion.</li>
              <li>To save your preferences so they persist between sessions.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Third-Party Services</h2>
            <p>We use the following third-party services:</p>
            <ul className="list-disc pl-5 space-y-2 mt-3">
              <li>
                <strong>Vercel</strong> — Hosting, analytics, and speed insights. See{" "}
                <a
                  href="https://vercel.com/legal/privacy-policy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  Vercel's Privacy Policy
                </a>
                .
              </li>
              <li>
                <strong>Supabase</strong> — Database hosting and authentication. Product, store, and
                account data is stored on Supabase infrastructure. User authentication is handled
                by Supabase Auth. See{" "}
                <a
                  href="https://supabase.com/privacy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  Supabase's Privacy Policy
                </a>
                .
              </li>
              <li>
                <strong>Google</strong> — If you sign in with Google, your email and profile
                information are provided to us by Google's OAuth service. See{" "}
                <a
                  href="https://policies.google.com/privacy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  Google's Privacy Policy
                </a>
                .
              </li>
              <li>
                <strong>Apple</strong> — If you sign in with Apple, your email (or a private relay
                address) is provided to us by Apple's Sign In service. See{" "}
                <a
                  href="https://www.apple.com/legal/privacy/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  Apple's Privacy Policy
                </a>
                .
              </li>
              <li>
                <strong>MapLibre / Map tiles</strong> — Used to display store locations on a map.
                Your approximate location is sent to tile servers to load map imagery.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Email Communications</h2>
            <p>
              If you set up price alerts, we will send you email notifications when your alert
              conditions are met. Every alert email includes a one-click unsubscribe link. You can
              also manage or delete your alerts from the Settings page at any time.
            </p>
            <p className="mt-2">
              We comply with New Zealand's Unsolicited Electronic Messages Act 2007. We will never
              send you marketing emails without your consent.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Cookies</h2>
            <p>
              Liquorfy does not use cookies for tracking or advertising. Your location preference and
              search radius are stored in your browser's local storage. Authentication tokens are
              managed by Supabase and stored in your browser's local storage.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Your Rights</h2>
            <p>Under New Zealand's Privacy Act 2020, you have the right to:</p>
            <ul className="list-disc pl-5 space-y-2 mt-2">
              <li>
                <strong>Access your data</strong> — You can view your account information, preferences,
                and alerts from the Settings page.
              </li>
              <li>
                <strong>Delete your data</strong> — You can delete your account at any time from the
                Settings page. This permanently removes all your data including preferences, alerts,
                and favourites.
              </li>
              <li>
                <strong>Revoke location access</strong> — You can revoke location permissions at any
                time through your browser or device settings.
              </li>
            </ul>
            <p className="mt-2">
              If you have questions about your data, contact us at the address below.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Children's Privacy</h2>
            <p>
              Liquorfy is intended for users aged 18 and over. We do not knowingly collect data from
              anyone under 18.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Changes to This Policy</h2>
            <p>
              We may update this policy from time to time. Changes will be reflected on this page
              with an updated date.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Contact</h2>
            <p>
              If you have questions about this privacy policy, email us at{" "}
              <a href="mailto:liquorfy@gmail.com" className="text-primary hover:underline">
                liquorfy@gmail.com
              </a>
              .
            </p>
          </section>
        </div>
      </main>
    </div>
  );
};

export default Privacy;
