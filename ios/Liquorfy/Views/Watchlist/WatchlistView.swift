import SwiftUI

/// Mirrors the web Watchlist page: price alerts, favourite products, and recently
/// viewed products in one screen.
struct WatchlistView: View {
    @Environment(LocationManager.self) private var locationManager
    @Environment(AuthManager.self) private var authManager
    @Environment(\.navigate) private var navigate

    @State private var alertsVM = AlertsViewModel()
    @State private var favouritesVM = FavouritesViewModel()
    private let favourites = FavouritesManager.shared
    private let recentlyViewed = RecentlyViewedManager.shared

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 28) {
                alertsSection
                favouritesSection
                recentlyViewedSection
            }
            .padding(.vertical)
        }
        .background(Color.appBackground)
        .navigationTitle("Watchlist")
        .navigationBarTitleDisplayMode(.large)
        .task {
            if authManager.isAuthenticated {
                await alertsVM.fetchAlerts()
            }
            await loadFavourites()
        }
        .onChange(of: favourites.favouriteIds) {
            Task { await loadFavourites() }
        }
    }

    private func loadFavourites() async {
        await favouritesVM.load(
            ids: favourites.favouriteUUIDs,
            lat: locationManager.location?.latitude,
            lon: locationManager.location?.longitude,
            radiusKm: locationManager.isLocationSet ? locationManager.radiusKm : nil
        )
    }

    // MARK: - Alerts

    @ViewBuilder
    private var alertsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Price Alerts", systemImage: "bell.fill")

            if !authManager.isAuthenticated {
                promptCard(
                    "Sign in to track prices",
                    detail: "Get notified when a product drops below your target price.",
                    actionTitle: "Sign in"
                ) { navigate(.login) }
            } else if alertsVM.isLoading {
                ProgressView().frame(maxWidth: .infinity).padding(.vertical, 20)
            } else if alertsVM.alerts.isEmpty {
                emptyCard("No price alerts yet", systemImage: "bell")
            } else {
                VStack(spacing: 8) {
                    ForEach(alertsVM.alerts) { alert in
                        alertRow(alert)
                    }
                }
                .padding(.horizontal)
            }
        }
    }

    private func alertRow(_ alert: PriceAlert) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(alert.productName ?? "Unknown product")
                    .font(.appSansSemiBold(size: 14, relativeTo: .subheadline))
                HStack(spacing: 12) {
                    if let threshold = alert.thresholdPrice {
                        Text("Below \(Formatters.formatPrice(threshold))")
                            .font(.appCaption)
                            .foregroundStyle(.secondary)
                    }
                    if alert.alertOnPromo {
                        Text("On promo")
                            .font(.appCaption)
                            .foregroundStyle(.secondary)
                    }
                    if !alert.active {
                        Text("Paused")
                            .font(.appCaption)
                            .foregroundStyle(.orange)
                    }
                }
            }
            Spacer()
            Button {
                Task { try? await alertsVM.deleteAlert(id: alert.id) }
            } label: {
                Image(systemName: "trash")
                    .foregroundStyle(.secondary)
            }
        }
        .padding(12)
        .cardStyle(cornerRadius: 12)
    }

    // MARK: - Favourites

    @ViewBuilder
    private var favouritesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Favourites", systemImage: "heart.fill")

            if favourites.favouriteIds.isEmpty {
                emptyCard("Tap the heart on any product to save it here", systemImage: "heart")
            } else if favouritesVM.isLoading {
                ProgressView().frame(maxWidth: .infinity).padding(.vertical, 20)
            } else {
                ProductGridView(products: favouritesVM.products) { product in
                    navigate(.productDetail(id: product.id))
                }
            }
        }
    }

    // MARK: - Recently Viewed

    @ViewBuilder
    private var recentlyViewedSection: some View {
        if !recentlyViewed.products.isEmpty {
            VStack(alignment: .leading, spacing: 12) {
                sectionHeader("Recently Viewed", systemImage: "clock.arrow.circlepath")
                ProductGridView(products: recentlyViewed.products) { product in
                    navigate(.productDetail(id: product.id))
                }
            }
        }
    }

    // MARK: - Building blocks

    private func sectionHeader(_ title: String, systemImage: String) -> some View {
        Label(title, systemImage: systemImage)
            .font(.appTitle3)
            .padding(.horizontal)
    }

    private func emptyCard(_ message: String, systemImage: String) -> some View {
        HStack(spacing: 10) {
            Image(systemName: systemImage)
                .foregroundStyle(.secondary)
            Text(message)
                .font(.appCardBody)
                .foregroundStyle(.secondary)
            Spacer()
        }
        .padding(16)
        .cardStyle(cornerRadius: 12)
        .padding(.horizontal)
    }

    private func promptCard(
        _ title: String,
        detail: String,
        actionTitle: String,
        action: @escaping () -> Void
    ) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.appSansSemiBold(size: 15, relativeTo: .subheadline))
            Text(detail)
                .font(.appCaption)
                .foregroundStyle(.secondary)
            Button(actionTitle, action: action)
                .buttonStyle(.borderedProminent)
                .controlSize(.small)
                .padding(.top, 2)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .cardStyle(cornerRadius: 12)
        .padding(.horizontal)
    }
}

#Preview {
    NavigationStack {
        WatchlistView()
    }
    .environment(LocationManager())
    .environment(AuthManager())
}
