import SwiftUI

struct LandingView: View {
    @Environment(LocationManager.self) private var locationManager
    @Environment(\.navigate) private var navigate

    @State private var viewModel = LandingViewModel()
    @State private var searchQuery = ""
    @State private var tempRadius: Double = Constants.Radius.default
    @State private var quickViewProduct: Product?

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                heroSection
                dealsSection
                mapSection
                statsSection
            }
        }
        .ignoresSafeArea(edges: .top)
        .background(Color.appBackground)
        .navigationTitle("")
        .navigationBarHidden(true)
        .sheet(item: $quickViewProduct) { product in
            QuickViewSheet(product: product)
                .presentationDetents([.large])
        }
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
                .font(.appTitle)
                .foregroundStyle(.white)
                .multilineTextAlignment(.center)

            Text("Find the best deals from major retailers near you")
                .font(.appCallout)
                .foregroundStyle(.white.opacity(0.9))
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
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                VStack(alignment: .leading, spacing: 6) {
                    Text(locationManager.isLocationSet ? "Deals Near You" : "Top Deals")
                        .font(.appTitle3)

                    if !locationManager.isLocationSet {
                        Text("Enable location for personalized results")
                            .font(.appCaption)
                            .foregroundStyle(.secondary)
                    }
                }

                Spacer()

                Button {
                    navigate(.explore(promoOnly: true))
                } label: {
                    HStack(spacing: 4) {
                        Text("View all")
                            .font(.appSansMedium(size: 14, relativeTo: .subheadline))
                        Image(systemName: "arrow.right")
                            .font(.system(size: 12))
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
                    HStack(alignment: .top, spacing: 12) {
                        ForEach(viewModel.deals) { product in
                            Button {
                                quickViewProduct = product
                            } label: {
                                DealCardView(product: product)
                            }
                            .buttonStyle(.pressableCard)
                        }
                    }
                    .padding(.horizontal, 4)
                    .padding(.vertical, 12)
                }
                .scrollClipDisabled()
            }
        }
        .padding(.horizontal)
        .padding(.vertical, 24)
    }

    // MARK: - Map

    private var mapSection: some View {
        VStack(spacing: 20) {
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
        .padding(.horizontal)
        .padding(.vertical, 24)
    }

    // MARK: - Stats

    private var statsSection: some View {
        VStack(spacing: 20) {
            Divider()
            StatsSection()
        }
        .padding(.horizontal)
        .padding(.vertical, 24)
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
