import SwiftUI

struct ProductDetailView: View {
    let productId: UUID

    @State private var viewModel = ProductDetailViewModel()

    var body: some View {
        Group {
            if viewModel.isLoading {
                LoadingView(message: "Loading product...")
            } else if let error = viewModel.error {
                ErrorView(message: error) {
                    Task { await viewModel.loadProduct(id: productId) }
                }
            } else if let product = viewModel.product {
                productContent(product)
            }
        }
        .navigationTitle("Product")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await viewModel.loadProduct(id: productId)
        }
    }

    @ViewBuilder
    private func productContent(_ product: Product) -> some View {
        ScrollView {
            VStack(spacing: 16) {
                // Image
                AsyncProductImageView(url: product.imageUrl, size: 200)
                    .frame(maxWidth: .infinity)
                    .frame(height: 250)
                    .background(Color.appBackground)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    .padding(.horizontal)

                // Info card
                VStack(alignment: .leading, spacing: 16) {
                    // Badges
                    HStack(spacing: 8) {
                        if product.price.hasPromo {
                            PromoBadgeView(percent: product.price.savingsPercent)
                        }
                        ChainBadgeView(chain: product.chain)
                    }

                    // Name
                    Text(product.name)
                        .font(.appTitle2)

                    if let brand = product.brand {
                        Text(brand)
                            .font(.appCardBody)
                            .foregroundStyle(.secondary)
                    }

                    // Price
                    HStack(alignment: .firstTextBaseline, spacing: 8) {
                        Text(Formatters.formatPrice(product.price.currentPrice))
                            .font(.appSansBold(size: 36, relativeTo: .largeTitle))
                            .foregroundStyle(.tint)

                        if product.price.hasPromo {
                            Text(Formatters.formatPrice(product.price.priceNzd))
                                .font(.appSans(size: 20, relativeTo: .title3))
                                .strikethrough()
                                .foregroundStyle(.secondary)
                        }
                    }

                    // Price metrics
                    PriceMetricsView(price: product.price)

                    // Promo info
                    if product.price.hasPromo {
                        promoInfo(product)
                    }

                    Divider()

                    // Store info
                    storeInfo(product)

                    Divider()

                    // Product specs
                    ProductSpecsView(product: product)

                    // View at store
                    if let urlString = product.productUrl, let url = URL(string: urlString) {
                        Link(destination: url) {
                            Label("View at Store", systemImage: "safari")
                                .font(.appSansMedium(size: 16, relativeTo: .body))
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
                .padding()
                .cardStyle(cornerRadius: 16)
                .padding(.horizontal)
            }
            .padding(.vertical)
        }
        .background(Color.appBackground)
        .transition(.opacity)
    }

    private func promoInfo(_ product: Product) -> some View {
        HStack(spacing: 12) {
            if product.price.isMemberOnly {
                Label("Members Only", systemImage: "crown.fill")
                    .font(.appCaption)
                    .foregroundStyle(.orange)
            }
            if let endText = Formatters.formatPromoEndDate(product.price.promoEndsAt) {
                Label(endText, systemImage: "clock")
                    .font(.appCaption)
                    .foregroundStyle(.tint)
            }
        }
    }

    private func storeInfo(_ product: Product) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Image(systemName: "storefront")
                    .foregroundStyle(.tint)
                VStack(alignment: .leading, spacing: 2) {
                    Text(product.price.storeName)
                        .font(.appSansSemiBold(size: 14, relativeTo: .subheadline))
                    Text(ChainConstants.displayName(for: product.chain))
                        .font(.appCaption)
                        .foregroundStyle(.secondary)
                }
            }

            if let distance = product.price.distanceKm {
                HStack(spacing: 4) {
                    DistanceBadgeView(distanceKm: distance)
                    if let text = Formatters.formatDistanceAway(distance) {
                        Text(text)
                            .font(.appCaption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
    }
}

#Preview {
    NavigationStack {
        ProductDetailView(productId: UUID())
    }
}
