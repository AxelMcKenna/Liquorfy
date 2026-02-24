import SwiftUI

struct QuickViewSheet: View {
    let product: Product
    var onViewDetail: () -> Void = {}

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ZStack(alignment: .topTrailing) {
            ScrollView {
                VStack(spacing: 0) {
                    // Image section
                    ZStack(alignment: .topLeading) {
                        AsyncProductImageView(url: product.imageUrl, size: 200)
                            .frame(maxWidth: .infinity)
                            .frame(height: 260)
                            .background(.white)

                        if product.price.savingsPercent > 0 {
                            PromoBadgeView(percent: product.price.savingsPercent)
                                .padding(12)
                        }
                    }

                    // Content section
                    VStack(alignment: .leading, spacing: 16) {
                        // Name + brand
                        VStack(alignment: .leading, spacing: 6) {
                            Text(product.name)
                                .font(.appSerif(size: 22, relativeTo: .title2))
                                .lineLimit(2)

                            if let brand = product.brand {
                                Text(brand)
                                    .font(.appCardBody)
                                    .foregroundStyle(.secondary)
                            }
                        }

                        // Price
                        VStack(alignment: .leading, spacing: 8) {
                            HStack(alignment: .firstTextBaseline, spacing: 8) {
                                Text(Formatters.formatPrice(product.price.currentPrice))
                                    .font(.appSansBold(size: 36, relativeTo: .largeTitle))
                                    .foregroundStyle(Color.appPrimary)

                                if product.price.hasPromo {
                                    Text(Formatters.formatPrice(product.price.priceNzd))
                                        .font(.appSans(size: 18, relativeTo: .title3))
                                        .strikethrough()
                                        .foregroundStyle(.secondary)
                                }
                            }

                            // Price metrics
                            PriceMetricsView(price: product.price)
                        }

                        // Promo badges
                        if product.price.hasPromo {
                            HStack(spacing: 8) {
                                if product.price.isMemberOnly {
                                    Label("Members Only", systemImage: "crown.fill")
                                        .font(.appCaption)
                                        .foregroundStyle(.orange)
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 4)
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 6)
                                                .stroke(Color.orange.opacity(0.3), lineWidth: 1)
                                        )
                                }
                                if let endText = Formatters.formatPromoEndDate(product.price.promoEndsAt) {
                                    Label(endText, systemImage: "clock")
                                        .font(.appCaption)
                                        .foregroundStyle(Color.appPrimary)
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 4)
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 6)
                                                .stroke(Color.appPrimary.opacity(0.3), lineWidth: 1)
                                        )
                                }
                            }
                        }

                        // Store info
                        VStack(alignment: .leading, spacing: 8) {
                            HStack(spacing: 8) {
                                Image(systemName: "storefront")
                                    .font(.system(size: 14))
                                    .foregroundStyle(Color.appPrimary)
                                Text(product.price.storeName)
                                    .font(.appSansMedium(size: 14, relativeTo: .subheadline))
                            }

                            if let distance = product.price.distanceKm,
                               let text = Formatters.formatDistanceAway(distance) {
                                HStack(spacing: 8) {
                                    Image(systemName: "mappin.circle.fill")
                                        .font(.system(size: 14))
                                        .foregroundStyle(Formatters.distanceColor(distance))
                                    Text(text)
                                        .font(.appSansMedium(size: 14, relativeTo: .subheadline))
                                        .foregroundStyle(Formatters.distanceColor(distance))
                                }
                            }
                        }

                        Divider()

                        // Product details
                        ProductSpecsView(product: product)

                        // Actions
                        if let urlString = product.productUrl, let url = URL(string: urlString) {
                            Link(destination: url) {
                                HStack(spacing: 8) {
                                    Text("View at Store")
                                        .font(.appSansSemiBold(size: 16, relativeTo: .body))
                                    Image(systemName: "arrow.up.right")
                                        .font(.system(size: 12, weight: .semibold))
                                }
                                .foregroundStyle(.white)
                                .frame(maxWidth: .infinity)
                                .frame(height: 48)
                                .background(Color.appPrimary)
                                .clipShape(RoundedRectangle(cornerRadius: 8))
                            }
                        }
                    }
                    .padding(24)
                }
            }
            .background(Color.appBackground)

            // Floating close button
            Button {
                dismiss()
            } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundStyle(.secondary)
                    .padding(10)
                    .background(.ultraThinMaterial)
                    .clipShape(Circle())
            }
            .padding(16)
        }
    }
}

#Preview {
    QuickViewSheet(product: PreviewData.product)
}
