import SwiftUI

struct ComparisonItemView: View {
    let product: Product

    @Environment(ComparisonManager.self) private var comparisonManager

    var body: some View {
        VStack(spacing: 6) {
            ZStack(alignment: .topTrailing) {
                AsyncProductImageView(url: product.imageUrl, size: 50)
                    .clipShape(RoundedRectangle(cornerRadius: 6))

                Button {
                    comparisonManager.remove(product)
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.caption)
                        .foregroundStyle(.white, .red)
                }
                .offset(x: 6, y: -6)
            }

            Text(product.name)
                .font(.system(size: 10))
                .lineLimit(2)
                .multilineTextAlignment(.center)
                .foregroundStyle(.primary)

            Text(Formatters.formatPrice(product.price.currentPrice))
                .font(.caption2)
                .fontWeight(.bold)

            ChainBadgeView(chain: product.chain)
        }
        .frame(width: 80)
        .padding(6)
        .background(Color(.tertiarySystemGroupedBackground))
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}

#Preview {
    ComparisonItemView(product: PreviewData.product)
        .environment(ComparisonManager())
}
