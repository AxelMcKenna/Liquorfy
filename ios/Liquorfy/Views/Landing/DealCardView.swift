import SwiftUI

struct DealCardView: View {
    let product: Product

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            ZStack(alignment: .topTrailing) {
                AsyncProductImageView(url: product.imageUrl, size: 120)
                    .frame(maxWidth: .infinity)
                    .background(Color(.systemBackground))
                    .clipShape(RoundedRectangle(cornerRadius: 8))

                if product.price.savingsPercent > 0 {
                    PromoBadgeView(percent: product.price.savingsPercent)
                        .padding(6)
                }
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(product.name)
                    .font(.caption)
                    .fontWeight(.medium)
                    .lineLimit(2)
                    .foregroundStyle(.primary)

                ChainBadgeView(chain: product.chain)

                HStack(alignment: .firstTextBaseline, spacing: 4) {
                    Text(Formatters.formatPrice(product.price.currentPrice))
                        .font(.subheadline)
                        .fontWeight(.bold)
                        .foregroundStyle(.primary)

                    if product.price.hasPromo {
                        Text(Formatters.formatPrice(product.price.priceNzd))
                            .font(.caption2)
                            .strikethrough()
                            .foregroundStyle(.secondary)
                    }
                }

                if let distance = product.price.distanceKm {
                    DistanceBadgeView(distanceKm: distance)
                }
            }
        }
        .frame(width: 160)
        .padding(10)
        .background(Color(.secondarySystemGroupedBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

#Preview {
    HStack {
        DealCardView(product: PreviewData.product)
        DealCardView(product: PreviewData.productNoPromo)
    }
    .padding()
}
