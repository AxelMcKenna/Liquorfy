import { Link } from "react-router-dom";

export const Support = () => {
  return (
    <div className="min-h-screen bg-background">
      <header className="bg-primary py-6">
        <div className="px-4">
          <Link to="/" className="text-xl font-semibold text-white tracking-tight">
            LIQUORFY
          </Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-semibold text-foreground mb-2">Support</h1>
        <p className="text-sm text-muted-foreground mb-10">
          Have a question or need help? We're here for you.
        </p>

        <div className="space-y-8 text-sm leading-relaxed text-foreground/90">
          <section className="bg-secondary rounded-lg p-6">
            <h2 className="text-lg font-semibold text-foreground mb-2">Contact Us</h2>
            <p>
              For any questions, feedback, or issues, email us at{" "}
              <a href="mailto:support@liquorfy.co.nz" className="text-primary hover:underline">
                support@liquorfy.co.nz
              </a>
              . We aim to respond within 48 hours.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-6">
              Frequently Asked Questions
            </h2>

            <div className="space-y-6">
              <div>
                <h3 className="font-semibold text-foreground mb-1">What is Liquorfy?</h3>
                <p>
                  Liquorfy is a free price comparison tool for liquor in New Zealand. We aggregate
                  prices from major retailers so you can find the best deals near you.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-foreground mb-1">
                  Do I need to create an account?
                </h3>
                <p>
                  No. Liquorfy is completely free to use and does not require an account or sign-up.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-foreground mb-1">
                  Why does the app ask for my location?
                </h3>
                <p>
                  Location access is optional. If you grant it, we use your position to show stores
                  and prices near you. You can revoke location access at any time in your device
                  settings.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-foreground mb-1">
                  How often are prices updated?
                </h3>
                <p>
                  Prices are updated daily from retailer websites. Promotions are refreshed as they
                  become available. Occasionally, a price may be slightly out of date — always
                  confirm at the retailer before purchasing.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-foreground mb-1">
                  Can I buy products through Liquorfy?
                </h3>
                <p>
                  No. Liquorfy is a comparison tool only. We show you where to find the best price,
                  but purchases are made directly with the retailer.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-foreground mb-1">
                  A price seems wrong. What should I do?
                </h3>
                <p>
                  Prices are scraped from retailer websites and may occasionally be inaccurate. If
                  you spot an error, please let us know at{" "}
                  <a
                    href="mailto:support@liquorfy.co.nz"
                    className="text-primary hover:underline"
                  >
                    support@liquorfy.co.nz
                  </a>{" "}
                  and we'll investigate.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-foreground mb-1">
                  Which retailers are included?
                </h3>
                <p>
                  We cover major New Zealand liquor retailers including Liquorland, Super Liquor,
                  Countdown, New World, and more. We're always working to expand coverage.
                </p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">Responsible Drinking</h2>
            <p>
              You must be 18 or older to purchase alcohol in New Zealand. If you or someone you know
              needs support with alcohol, visit{" "}
              <a
                href="https://www.alcohol.org.nz"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                Alcohol.org.nz
              </a>{" "}
              or call the Alcohol Drug Helpline on{" "}
              <a href="tel:0800787797" className="text-primary hover:underline">
                0800 787 797
              </a>
              .
            </p>
          </section>
        </div>
      </main>
    </div>
  );
};

export default Support;
