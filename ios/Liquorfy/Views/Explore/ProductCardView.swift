import SwiftUI

struct ProductCardView: View {
    let product: Product

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Image
            ZStack(alignment: .topLeading) {
                AsyncProductImageView(url: product.imageUrl, size: 100)
                    .frame(maxWidth: .infinity)
                    .frame(height: 120)
                    .background(Color.appBackground)
                    .clipShape(RoundedRectangle(cornerRadius: 8))

                if product.price.savingsPercent > 0 {
                    PromoBadgeView(percent: product.price.savingsPercent)
                        .padding(6)
                }
            }

            // Info
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

                    if product.price.hasPromo {
                        Text(Formatters.formatPrice(product.price.priceNzd))
                            .font(.caption2)
                            .strikethrough()
                            .foregroundStyle(.secondary)
                    }
                }

                DistanceBadgeView(distanceKm: product.price.distanceKm)
            }
        }
        .padding(10)
        .background(Color.appCardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .accessibilityElement(children: .combine)
        .accessibilityLabel(productAccessibilityLabel)
    }

    private var productAccessibilityLabel: String {
        var parts = [product.name, Formatters.formatPrice(product.price.currentPrice)]
        if product.price.hasPromo {
            parts.append("\(product.price.savingsPercent)% off")
        }
        if let distance = Formatters.formatDistance(product.price.distanceKm) {
            parts.append(distance + " away")
        }
        return parts.joined(separator: ", ")
    }
}

#Preview {
    ProductCardView(product: PreviewData.product)
        .frame(width: 180)
}
