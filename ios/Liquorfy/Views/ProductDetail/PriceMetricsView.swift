import SwiftUI

struct PriceMetricsView: View {
    let price: Price

    var body: some View {
        let metrics = buildMetrics()

        if !metrics.isEmpty {
            HStack(spacing: 16) {
                ForEach(metrics, id: \.label) { metric in
                    VStack(spacing: 2) {
                        Text(metric.value)
                            .font(.subheadline)
                            .fontWeight(.semibold)
                        Text(metric.label)
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                    .frame(maxWidth: .infinity)
                }
            }
            .padding()
            .background(Color.appTertiaryBackground)
            .clipShape(RoundedRectangle(cornerRadius: 10))
        }
    }

    private struct Metric {
        let label: String
        let value: String
    }

    private func buildMetrics() -> [Metric] {
        var metrics: [Metric] = []

        if let per100ml = price.pricePer100ml {
            metrics.append(Metric(label: "per 100ml", value: Formatters.formatPrice(per100ml)))
        }
        if let perDrink = price.pricePerStandardDrink {
            metrics.append(Metric(label: "per std drink", value: Formatters.formatPrice(perDrink)))
        }
        if let drinks = price.standardDrinks {
            metrics.append(Metric(label: "std drinks", value: String(format: "%.1f", drinks)))
        }

        return metrics
    }
}

#Preview {
    PriceMetricsView(price: PreviewData.price)
        .padding()
}
