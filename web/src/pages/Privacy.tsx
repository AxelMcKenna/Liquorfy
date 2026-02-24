import { Link } from "react-router-dom";

export const Privacy = () => {
  return (
    <div className="min-h-screen bg-background">
      <header className="bg-primary py-6">
        <div className="max-w-6xl mx-auto px-4">
          <Link to="/" className="text-xl font-semibold text-white tracking-tight">
            LIQUORFY
          </Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-semibold text-foreground mb-2">Privacy Policy</h1>
        <p className="text-sm text-muted-foreground mb-10">Last updated: 23 February 2026</p>

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
              Liquorfy does not require you to create an account or sign in. We collect minimal data
              to provide our service:
            </p>
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
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Data We Do Not Collect</h2>
            <ul className="list-disc pl-5 space-y-2">
              <li>We do not collect names, email addresses, or any personal account information.</li>
              <li>We do not collect payment or financial information.</li>
              <li>We do not track you across other websites or apps.</li>
              <li>We do not sell or share data with advertisers.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">How We Use Your Data</h2>
            <ul className="list-disc pl-5 space-y-2">
              <li>To show liquor prices from stores near your location.</li>
              <li>To return relevant product search results.</li>
              <li>To monitor and improve site performance via anonymous analytics.</li>
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
                <strong>MapLibre / Map tiles</strong> — Used to display store locations on a map.
                Your approximate location is sent to tile servers to load map imagery.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Cookies</h2>
            <p>
              Liquorfy does not use cookies for tracking or advertising. Your location preference and
              search radius are stored in your browser's local storage and never sent to third
              parties.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Your Rights</h2>
            <p>
              Since we don't collect personal data or require accounts, there is no personal data to
              access, correct, or delete. You can revoke location access at any time through your
              browser or device settings. If you have questions about your data, contact us at the
              address below.
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
              <a href="mailto:support@liquorfy.co.nz" className="text-primary hover:underline">
                support@liquorfy.co.nz
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
