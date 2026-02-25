import SwiftUI

struct ProductCardView: View {
    let product: Product

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Image — fixed height so all cards match
            ZStack(alignment: .topLeading) {
                AsyncProductImageView(url: product.imageUrl, size: 130)
                    .frame(maxWidth: .infinity)
                    .frame(height: 140)
                    .clipped()
                    .background(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 8))

                if product.price.savingsPercent > 0 {
                    PromoBadgeView(percent: product.price.savingsPercent)
                        .padding(.top, 6)
                        .padding(.leading, 6)
                }
            }

            // Info — fixed layout so all cards are equal height
            VStack(alignment: .leading, spacing: 8) {
                // Name (always reserves 2 lines)
                Text(product.name)
                    .font(.appSerif(size: 14, relativeTo: .subheadline))
                    .lineLimit(2)
                    .frame(minHeight: 34, alignment: .topLeading)
                    .foregroundStyle(.primary)

                // Brand (always reserves 1 line)
                Text(product.brand ?? " ")
                    .font(.appCaption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)

                // Store + Distance row (matches web: Store icon + name, MapPin icon + distance)
                HStack(spacing: 12) {
                    HStack(spacing: 3) {
                        Image(systemName: "storefront")
                            .font(.system(size: 9))
                        Text(ChainConstants.displayName(for: product.chain))
                            .lineLimit(1)
                    }
                    .foregroundStyle(.secondary)

                    if let distanceKm = product.price.distanceKm,
                       let distanceText = Formatters.formatDistance(distanceKm) {
                        HStack(spacing: 3) {
                            Image(systemName: "mappin.circle.fill")
                                .font(.system(size: 10))
                            Text(distanceText)
                                .lineLimit(1)
                        }
                        .foregroundStyle(Formatters.distanceColor(distanceKm))
                    }
                }
                .font(.appCaption)

                // Price
                HStack(alignment: .firstTextBaseline, spacing: 4) {
                    Text(Formatters.formatPrice(product.price.currentPrice))
                        .font(.appPrice)
                        .foregroundStyle(Color.appPrimary)

                    if product.price.hasPromo {
                        Text(Formatters.formatPrice(product.price.priceNzd))
                            .font(.appCaption)
                            .strikethrough()
                            .foregroundStyle(.secondary)
                    }

                    Spacer()
                }
                .frame(minHeight: 24)
            }
        }
        .padding(12)
        .frame(maxHeight: .infinity, alignment: .top)
        .cardStyle()
        .accessibilityElement(children: .combine)
        .accessibilityLabel(productAccessibilityLabel)
    }

    private var productAccessibilityLabel: String {
        var parts = [product.name, Formatters.formatPrice(product.price.currentPrice)]
        if product.price.hasPromo {
            parts.append("\(product.price.savingsPercent)% off")
        }
        parts.append("at \(product.price.storeName)")
        if let distance = Formatters.formatDistance(product.price.distanceKm) {
            parts.append(distance + " away")
        }
        return parts.joined(separator: ", ")
    }
}

#if DEBUG
#Preview {
    ProductCardView(product: PreviewData.product)
        .frame(width: 180)
}
#endif
