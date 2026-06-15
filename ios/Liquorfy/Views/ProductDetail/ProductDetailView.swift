import SwiftUI
import Charts

struct ProductDetailView: View {
    let productId: UUID

    @Environment(LocationManager.self) private var locationManager
    @State private var viewModel = ProductDetailViewModel()
    @State private var showLocation = false
    private let favourites = FavouritesManager.shared

    var body: some View {
        Group {
            if viewModel.isLoading {
                LoadingView(message: "Loading product...")
            } else if let error = viewModel.error {
                ErrorView(message: error) {
                    Task { await load() }
                }
            } else if let detail = viewModel.detail {
                productContent(detail)
            }
        }
        .navigationTitle("Product")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    favourites.toggle(productId)
                } label: {
                    Image(systemName: favourites.isFavourite(productId) ? "heart.fill" : "heart")
                        .foregroundStyle(favourites.isFavourite(productId) ? .red : .secondary)
                }
                .accessibilityLabel(favourites.isFavourite(productId) ? "Remove from favourites" : "Add to favourites")
            }
        }
        .sheet(isPresented: $showLocation) {
            LocationSheetView {
                Task { await load() }
            }
        }
        .task {
            await load()
        }
    }

    private func load() async {
        await viewModel.load(
            id: productId,
            lat: locationManager.location?.latitude,
            lon: locationManager.location?.longitude,
            radiusKm: locationManager.isLocationSet ? locationManager.radiusKm : nil
        )
    }

    @ViewBuilder
    private func productContent(_ detail: ProductDetail) -> some View {
        let product = detail.product
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
                    HStack(spacing: 8) {
                        if product.price.hasPromo {
                            PromoBadgeView(percent: product.price.savingsPercent)
                        }
                        ChainBadgeView(chain: product.chain)
                    }

                    Text(product.name)
                        .font(.appTitle2)

                    if let brand = product.brand {
                        Text(brand)
                            .font(.appCardBody)
                            .foregroundStyle(.secondary)
                    }

                    if let description = detail.description, !description.isEmpty {
                        Text(description)
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

                    if product.price.hasPromo && product.price.savingsAmount > 0 {
                        Text("You save \(Formatters.formatPrice(product.price.savingsAmount)) · \(product.price.savingsPercent)% off")
                            .font(.appSansSemiBold(size: 14, relativeTo: .subheadline))
                            .foregroundStyle(Color.appPrimary)
                    }

                    PriceMetricsView(price: product.price)

                    if product.price.hasPromo {
                        promoInfo(product)
                    }

                    Divider()

                    storeInfo(product)

                    Divider()

                    ProductSpecsView(product: product)

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

                // Compare prices — viewed product, other stores, and other chains, cheapest first.
                compareSection

                // Price history
                if !detail.priceHistory.isEmpty {
                    priceHistorySection(detail.priceHistory)
                }
            }
            .padding(.vertical)
        }
        .background(Color.appBackground)
        .transition(.opacity)
    }

    // MARK: - Compare Section

    private static let compareInitial = 6

    @State private var compareExpanded = false

    @ViewBuilder
    private var compareSection: some View {
        let entries = viewModel.compareEntries
        if entries.count > 1 {
            VStack(alignment: .leading, spacing: 12) {
                HStack(alignment: .firstTextBaseline, spacing: 8) {
                    Text("Compare prices")
                        .font(.appSansSemiBold(size: 18, relativeTo: .title3))
                    Text("\(entries.count) options")
                        .font(.appCaption)
                        .foregroundStyle(.secondary)
                }
                Text("Across stores and chains — cheapest first")
                    .font(.appCaption)
                    .foregroundStyle(.secondary)

                if !locationManager.isLocationSet {
                    Button {
                        showLocation = true
                    } label: {
                        HStack(spacing: 8) {
                            Image(systemName: "mappin.circle.fill")
                                .foregroundStyle(Color.appPrimary)
                            Text("Set your location to see distances and what's cheapest nearby")
                                .font(.appCaption)
                                .foregroundStyle(.primary)
                                .multilineTextAlignment(.leading)
                            Spacer(minLength: 4)
                            Text("Enable")
                                .font(.appSansSemiBold(size: 13, relativeTo: .footnote))
                                .foregroundStyle(Color.appPrimary)
                        }
                        .padding(12)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.appPrimary.opacity(0.06))
                        .overlay(
                            RoundedRectangle(cornerRadius: 10)
                                .stroke(Color.appPrimary.opacity(0.3), lineWidth: 1)
                        )
                        .clipShape(RoundedRectangle(cornerRadius: 10))
                    }
                    .buttonStyle(.plain)
                }

                let visible = compareExpanded ? entries : Array(entries.prefix(Self.compareInitial))
                VStack(spacing: 8) {
                    ForEach(Array(visible.enumerated()), id: \.element.id) { index, entry in
                        CompareRowView(entry: entry, isBest: index == 0)
                    }
                }

                let remaining = entries.count - Self.compareInitial
                if !compareExpanded && remaining > 0 {
                    Button("Show \(remaining) more") {
                        compareExpanded = true
                    }
                    .font(.appSansSemiBold(size: 14, relativeTo: .subheadline))
                    .foregroundStyle(Color.appPrimary)
                }
            }
            .padding(.horizontal)
        }
    }

    // MARK: - Price History

    @ViewBuilder
    private func priceHistorySection(_ points: [PriceHistoryPoint]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Price history")
                .font(.appSansSemiBold(size: 18, relativeTo: .title3))

            Chart(Array(points.enumerated()), id: \.offset) { index, point in
                LineMark(
                    x: .value("Point", index),
                    y: .value("Price", point.effectivePrice)
                )
                .foregroundStyle(Color.appPrimary)
                .interpolationMethod(.catmullRom)

                AreaMark(
                    x: .value("Point", index),
                    y: .value("Price", point.effectivePrice)
                )
                .foregroundStyle(Color.appPrimary.opacity(0.12))
                .interpolationMethod(.catmullRom)
            }
            .chartXAxis(.hidden)
            .frame(height: 160)
        }
        .padding()
        .cardStyle(cornerRadius: 16)
        .padding(.horizontal)
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

// MARK: - Compare Row

private struct CompareRowView: View {
    let entry: CompareEntry
    let isBest: Bool

    @Environment(\.navigate) private var navigate

    var body: some View {
        Group {
            if let productId = entry.productId {
                Button {
                    navigate(.productDetail(id: productId))
                } label: { rowContent }
                .buttonStyle(.plain)
            } else {
                rowContent
            }
        }
    }

    private var rowContent: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(isBest ? Color.appPrimary.opacity(0.15) : Color.appBackground)
                    .frame(width: 32, height: 32)
                Image(systemName: "storefront")
                    .font(.system(size: 14))
                    .foregroundStyle(isBest ? Color.appPrimary : .secondary)
            }

            VStack(alignment: .leading, spacing: 2) {
                Text(entry.storeName)
                    .font(.appSansMedium(size: 14, relativeTo: .subheadline))
                    .lineLimit(1)
                HStack(spacing: 6) {
                    Text(ChainConstants.displayName(for: entry.chain))
                        .font(.appCaption)
                        .foregroundStyle(.secondary)
                    if let distance = entry.distanceKm, let text = Formatters.formatDistance(distance) {
                        Label(text, systemImage: "mappin")
                            .font(.appCaption)
                            .foregroundStyle(Formatters.distanceColor(distance))
                            .labelStyle(.titleAndIcon)
                    }
                }
            }

            Spacer(minLength: 8)

            VStack(alignment: .trailing, spacing: 2) {
                HStack(spacing: 6) {
                    if isBest {
                        Text("Best")
                            .font(.appSansSemiBold(size: 10, relativeTo: .caption2))
                            .foregroundStyle(.white)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.appPrimary)
                            .clipShape(Capsule())
                    }
                    Text(Formatters.formatPrice(entry.effective))
                        .font(isBest ? .appSansBold(size: 16, relativeTo: .body) : .appSansSemiBold(size: 14, relativeTo: .subheadline))
                        .foregroundStyle(isBest ? Color.appPrimary : .primary)
                }
                if entry.hasPromo {
                    Text(Formatters.formatPrice(entry.priceNzd))
                        .font(.appCaption)
                        .strikethrough()
                        .foregroundStyle(.tertiary)
                }
            }

            if entry.productId != nil {
                Image(systemName: "chevron.right")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(.tertiary)
            }
        }
        .padding(12)
        .background(isBest ? Color.appPrimary.opacity(0.05) : .white)
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(isBest ? Color.appPrimary.opacity(0.3) : Color.black.opacity(0.08), lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}

#Preview {
    NavigationStack {
        ProductDetailView(productId: UUID())
    }
    .environment(LocationManager())
}
