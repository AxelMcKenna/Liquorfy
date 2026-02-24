import SwiftUI

struct LandingView: View {
    @Environment(LocationManager.self) private var locationManager
    @Environment(\.navigate) private var navigate

    @State private var viewModel = LandingViewModel()
    @State private var searchQuery = ""
    @State private var tempRadius: Double = Constants.Radius.default

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                heroSection
                dealsSection
                mapSection
                statsSection
            }
        }
        .background(Color.appBackground)
        .navigationTitle("")
        .navigationBarHidden(true)
        .refreshable {
            await refresh()
        }
        .task {
            tempRadius = locationManager.radiusKm
            await refresh()
        }
        .onChange(of: locationManager.location?.latitude) {
            Task { await refresh() }
        }
        .onChange(of: locationManager.radiusKm) {
            Task { await refresh() }
        }
    }

    // MARK: - Hero

    private var heroSection: some View {
        VStack(spacing: 20) {
            Text("Compare liquor prices across NZ")
                .font(.appTitle2)
                .foregroundStyle(.white)
                .multilineTextAlignment(.center)

            Text("Find the best deals from major retailers near you")
                .font(.appCallout)
                .foregroundStyle(.white.opacity(0.8))
                .padding(.bottom, 8)

            SearchBarView(text: $searchQuery, onSubmit: handleSearch)
                .padding(.horizontal)
        }
        .padding(.top, 56)
        .padding(.bottom, 48)
        .padding(.horizontal)
        .frame(maxWidth: .infinity)
        .background(Color.appPrimary)
    }

    // MARK: - Deals

    private var dealsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(locationManager.isLocationSet ? "Deals Near You" : "Top Deals")
                        .font(.appTitle3)

                    if !locationManager.isLocationSet {
                        Text("Enable location for personalized results")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }

                Spacer()

                Button {
                    navigate(.explore(promoOnly: true))
                } label: {
                    HStack(spacing: 4) {
                        Text("View all")
                            .font(.subheadline)
                        Image(systemName: "arrow.right")
                            .font(.caption)
                    }
                }
            }

            if viewModel.isLoadingDeals {
                SkeletonDealScrollView()
                    .frame(height: 260)
            } else if viewModel.deals.isEmpty {
                Text("No deals available")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 40)
            } else {
                ScrollView(.horizontal, showsIndicators: false) {
                    LazyHStack(spacing: 12) {
                        ForEach(viewModel.deals) { product in
                            Button {
                                navigate(.productDetail(id: product.id))
                            } label: {
                                DealCardView(product: product)
                            }
                            .buttonStyle(.pressableCard)
                        }
                    }
                    .padding(.horizontal, 1)
                }
            }
        }
        .padding()
    }

    // MARK: - Map

    private var mapSection: some View {
        VStack(spacing: 16) {
            Divider()

            if !locationManager.isLocationSet {
                LocationRequestView()
            } else {
                VStack(spacing: 12) {
                    RadiusSliderView(
                        radius: $tempRadius,
                        storeCount: viewModel.stores.count,
                        onChanged: { newRadius in
                            locationManager.setRadius(newRadius)
                        }
                    )

                    StoreMapView(
                        stores: viewModel.stores,
                        userLocation: locationManager.location,
                        radiusKm: locationManager.radiusKm
                    )
                    .frame(height: 350)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }
            }
        }
        .padding()
    }

    // MARK: - Stats

    private var statsSection: some View {
        VStack(spacing: 16) {
            Divider()
            StatsSection()
        }
        .padding()
    }

    // MARK: - Actions

    private func handleSearch() {
        guard !searchQuery.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        navigate(.explore(query: searchQuery))
    }

    private func refresh() async {
        await viewModel.loadDeals(
            location: locationManager.location,
            radiusKm: locationManager.radiusKm
        )
        if let location = locationManager.location {
            await viewModel.loadStores(
                location: location,
                radiusKm: locationManager.radiusKm
            )
        }
    }
}

#Preview {
    NavigationStack {
        LandingView()
    }
    .environment(LocationManager())
}
