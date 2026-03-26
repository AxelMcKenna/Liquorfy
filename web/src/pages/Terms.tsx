import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";

export const Terms = () => {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <PageHeader backTo="/" />

      <main className="max-w-3xl mx-auto px-4 py-12 flex-1">
        <h1 className="text-3xl font-semibold text-foreground mb-2">Terms of Service</h1>
        <p className="text-sm text-muted-foreground mb-10">Last updated: 26 March 2026</p>

        <div className="space-y-8 text-sm leading-relaxed text-foreground/90">
          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Acceptance of Terms</h2>
            <p>
              By accessing or using Liquorfy ("the Service"), you agree to be bound by these Terms of Service.
              If you do not agree to these terms, please do not use the Service.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Description of Service</h2>
            <p>
              Liquorfy is a price comparison tool that aggregates publicly available liquor pricing
              information from retailers across New Zealand. We do not sell alcohol or facilitate
              transactions. All purchases are made directly through the respective retailers.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Age Requirement</h2>
            <p>
              You must be at least 18 years old to use this Service. By using Liquorfy, you confirm
              that you meet the legal drinking age requirement in New Zealand. We do not knowingly
              provide services to anyone under the age of 18.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">User Accounts</h2>
            <p>
              You may create an account using email/password or third-party authentication (Google, Apple).
              You are responsible for maintaining the security of your account credentials. You may delete
              your account at any time through the Settings page, which will permanently remove all
              associated data.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Acceptable Use</h2>
            <p>You agree not to:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li>Use the Service for any unlawful purpose</li>
              <li>Scrape, crawl, or otherwise extract data from the Service by automated means</li>
              <li>Attempt to gain unauthorised access to any part of the Service</li>
              <li>Interfere with or disrupt the Service or its infrastructure</li>
              <li>Impersonate any person or entity</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Pricing Information</h2>
            <p>
              Product prices, promotions, and availability displayed on Liquorfy are sourced from
              publicly available retailer information and are provided for informational purposes only.
              We make reasonable efforts to keep pricing accurate and up-to-date, but we do not guarantee
              the accuracy, completeness, or timeliness of any pricing information. Always verify prices
              directly with the retailer before making a purchase.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Intellectual Property</h2>
            <p>
              The Service, including its design, features, and content (excluding third-party product
              information), is owned by Liquorfy. Product names, images, and branding belong to their
              respective owners and are displayed for informational purposes only.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Limitation of Liability</h2>
            <p>
              Liquorfy is provided "as is" without warranties of any kind. We are not liable for any
              damages arising from your use of the Service, including but not limited to inaccurate
              pricing information, service interruptions, or data loss. Our total liability shall not
              exceed the amount you have paid to use the Service (which is zero, as the Service is free).
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Third-Party Services</h2>
            <p>
              The Service integrates with third-party providers including Google and Apple for
              authentication, Supabase for data storage, and Vercel for hosting. Your use of these
              services is subject to their respective terms and privacy policies. Links to external
              retailer websites are provided for convenience; we are not responsible for the content
              or practices of external sites.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Termination</h2>
            <p>
              We reserve the right to suspend or terminate your access to the Service at any time,
              with or without cause. You may stop using the Service at any time by deleting your
              account through the Settings page.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Changes to Terms</h2>
            <p>
              We may update these terms from time to time. Continued use of the Service after changes
              constitutes acceptance of the revised terms. We will update the "Last updated" date at
              the top of this page when changes are made.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Governing Law</h2>
            <p>
              These terms are governed by the laws of New Zealand. Any disputes shall be subject to
              the exclusive jurisdiction of the courts of New Zealand.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Contact</h2>
            <p>
              Questions about these Terms of Service? Contact us at{" "}
              <a href="mailto:liquorfy@gmail.com" className="text-primary hover:underline">
                liquorfy@gmail.com
              </a>
            </p>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Terms;
