import SwiftUI

struct DealCardView: View {
    let product: Product

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            ZStack(alignment: .topTrailing) {
                AsyncProductImageView(url: product.imageUrl, size: 140)
                    .frame(maxWidth: .infinity)
                    .frame(height: 156)
                    .background(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 8))

                if product.price.savingsPercent > 0 {
                    PromoBadgeView(percent: product.price.savingsPercent)
                        .padding(6)
                }
            }

            VStack(alignment: .leading, spacing: 4) {
                // Name — always 2 lines
                Text(product.name)
                    .font(.appSerif(size: 14, relativeTo: .subheadline))
                    .lineLimit(2)
                    .frame(minHeight: 36, alignment: .topLeading)
                    .foregroundStyle(.primary)

                ChainBadgeView(chain: product.chain)

                // Price — always reserve space for strikethrough
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
                .frame(minHeight: 22)

                // Distance — always reserve space
                if let distance = product.price.distanceKm {
                    DistanceBadgeView(distanceKm: distance)
                } else {
                    Text(" ")
                        .font(.appCaption)
                }
            }
        }
        .frame(width: 180)
        .padding(12)
        .frame(maxHeight: .infinity, alignment: .top)
        .cardStyle()
    }
}

#Preview {
    HStack {
        DealCardView(product: PreviewData.product)
        DealCardView(product: PreviewData.productNoPromo)
    }
    .padding()
}
