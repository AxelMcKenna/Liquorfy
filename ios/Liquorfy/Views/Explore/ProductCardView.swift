import SwiftUI

struct ProductCardView: View {
    let product: Product

    @Environment(ComparisonManager.self) private var comparisonManager

    private var isComparing: Bool {
        comparisonManager.contains(product)
    }

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

                HStack {
                    DistanceBadgeView(distanceKm: product.price.distanceKm)
                    Spacer()

                    // Compare button
                    Button {
                        comparisonManager.toggle(product)
                    } label: {
                        Image(systemName: isComparing ? "checkmark.circle.fill" : "plus.circle")
                            .font(.body)
                            .foregroundStyle(isComparing ? .tint : .secondary)
                    }
                    .disabled(!isComparing && comparisonManager.isAtLimit)
                }
            }
        }
        .padding(10)
        .background(Color.appCardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

#Preview {
    ProductCardView(product: PreviewData.product)
        .frame(width: 180)
        .environment(ComparisonManager())
}
