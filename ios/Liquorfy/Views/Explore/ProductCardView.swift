import SwiftUI

struct ProductCardView: View {
    let product: Product
    var sort: SortOption = .bestValue

    private let favourites = FavouritesManager.shared

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
            .overlay(alignment: .topTrailing) {
                Button {
                    favourites.toggle(product.id)
                } label: {
                    Image(systemName: favourites.isFavourite(product.id) ? "heart.fill" : "heart")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(favourites.isFavourite(product.id) ? .red : .secondary)
                        .padding(6)
                        .background(.white.opacity(0.9))
                        .clipShape(Circle())
                }
                .buttonStyle(.plain)
                .padding(.top, 6)
                .padding(.trailing, 6)
                .accessibilityLabel(favourites.isFavourite(product.id) ? "Remove from favourites" : "Add to favourites")
            }
            .overlay(alignment: .bottomLeading) {
                if product.isCheapestNearby {
                    HStack(spacing: 3) {
                        Image(systemName: "arrow.down.right.circle.fill")
                            .font(.system(size: 9))
                        Text("Cheapest nearby")
                    }
                    .font(.appBadge)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 3)
                    .background(.white)
                    .foregroundStyle(Color.appPrimary)
                    .clipShape(Capsule())
                    .overlay(Capsule().stroke(Color.appPrimary.opacity(0.25), lineWidth: 1))
                    .padding(.bottom, 6)
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
                        .fontWeight(.medium)
                        .foregroundStyle(Formatters.distanceColor(distanceKm))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.appTertiaryBackground)
                        .clipShape(Capsule())
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

                // Savings — the tangible value, in dollars (always reserves 1 line)
                Text(product.price.hasPromo && product.price.savingsAmount > 0
                     ? "Save \(Formatters.formatPrice(product.price.savingsAmount))"
                     : " ")
                    .font(.appBadge)
                    .foregroundStyle(Color.appPrimary)
                    .lineLimit(1)

                // Per-unit value matching the active sort (always reserves 1 line)
                Text(perUnitText ?? " ")
                    .font(.appCaption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
        }
        .padding(12)
        .frame(maxHeight: .infinity, alignment: .top)
        .cardStyle()
        .accessibilityElement(children: .combine)
        .accessibilityLabel(productAccessibilityLabel)
    }

    private var perUnitText: String? {
        if sort == .bestPerDrink {
            guard let perDrink = product.price.pricePerStandardDrink else { return nil }
            return "\(Formatters.formatPrice(perDrink)) / std drink"
        }
        guard let per100ml = product.price.pricePer100ml else { return nil }
        return "\(Formatters.formatPrice(per100ml)) / 100ml"
    }

    private var productAccessibilityLabel: String {
        var parts = [product.name, Formatters.formatPrice(product.price.currentPrice)]
        if product.price.hasPromo {
            parts.append("\(product.price.savingsPercent)% off")
        }
        if product.isCheapestNearby {
            parts.append("cheapest nearby")
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
