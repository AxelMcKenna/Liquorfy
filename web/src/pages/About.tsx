import { Link } from 'react-router-dom';
import { LegalPage } from '@/components/layout/LegalPage';

export default function About() {
  return (
    <LegalPage title="About Liquorfy" subtitle="One search. More stores. A clearer comparison.">
      <section>
        <h2 className="text-lg font-semibold text-foreground mb-3">Find the best price near you</h2>
        <p>
          Liquorfy compares beer, wine, and spirits prices across New Zealand retailers.
          Search once, see what nearby stores charge, and check the latest offers.
          It’s free to browse, with no account needed.
        </p>
        <p className="mt-3">
          Different pack sizes and promotions can make a good deal hard to spot. Liquorfy
          brings those details together so you can compare more easily, without jumping
          between retailer websites.
        </p>
      </section>
      <section>
        <h2 className="text-lg font-semibold text-foreground mb-3">Built by Axel McKenna</h2>
        <p>
          Alongside Liquorfy, Axel is building{' '}
          <a href="https://damascus-llm.dev" className="text-primary hover:underline">DAMASCUS</a>,
          an experimental LLM inference engine for Apple Silicon. It’s an exploration of how
          language models run and how to make inference more efficient.
        </p>
        <p className="mt-3">
          <a href="https://damascus-llm.dev/axel-mckenna" className="text-primary hover:underline">More about Axel’s work</a>
          {' · '}
          <a href="https://github.com/AxelMcKenna" className="text-primary hover:underline">GitHub</a>
        </p>
      </section>
      <section>
        <h2 className="text-lg font-semibold text-foreground mb-3">Ready to compare?</h2>
        <p>
          <Link to="/explore" className="text-primary hover:underline">Explore products</Link>
          {' or '}
          <Link to="/support" className="text-primary hover:underline">get in touch</Link>{' '}
          if you spot something we should fix.
        </p>
        <p className="mt-4 text-xs text-muted-foreground">
          Prices and availability can change. Confirm the details with the retailer before buying.
          You must be 18+ to purchase alcohol. For support, visit{' '}
          <a href="https://www.alcohol.org.nz" className="text-primary hover:underline">Alcohol.org.nz</a>.
        </p>
      </section>
    </LegalPage>
  );
}
