import SwiftUI

struct ExploreView: View {
    var initialQuery: String?
    var initialPromoOnly: Bool = false

    @Environment(LocationManager.self) private var locationManager
    @Environment(ComparisonManager.self) private var comparisonManager
    @Environment(\.navigate) private var navigate

    @State private var viewModel = ExploreViewModel()
    @State private var filterState = FilterState()
    @State private var showFilters = false

    var body: some View {
        Group {
            if !locationManager.isLocationSet {
                locationGate
            } else {
                content
            }
        }
        .navigationTitle("Explore")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    showFilters = true
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "line.3.horizontal.decrease")
                        if filterState.activeFilterCount > 0 {
                            Text("\(filterState.activeFilterCount)")
                                .font(.caption2)
                                .fontWeight(.bold)
                                .padding(.horizontal, 5)
                                .padding(.vertical, 1)
                                .background(.tint)
                                .foregroundStyle(.white)
                                .clipShape(Capsule())
                        }
                    }
                }
            }
        }
        .searchable(text: $filterState.query, prompt: "Search products")
        .onSubmit(of: .search) {
            filterState.currentPage = 1
            Task { await fetchProducts() }
        }
        .sheet(isPresented: $showFilters) {
            FilterSheetView(filterState: filterState) {
                filterState.currentPage = 1
                Task { await fetchProducts() }
            }
        }
        .onAppear {
            if let initialQuery, !initialQuery.isEmpty {
                filterState.query = initialQuery
            }
            if initialPromoOnly {
                filterState.promoOnly = true
            }
        }
        .task {
            if locationManager.isLocationSet {
                await fetchProducts()
            }
        }
        .onChange(of: locationManager.isLocationSet) {
            if locationManager.isLocationSet {
                Task { await fetchProducts() }
            }
        }
        .refreshable {
            await fetchProducts()
        }
        .safeAreaInset(edge: .bottom) {
            if !comparisonManager.isEmpty {
                ComparisonTrayView()
            }
        }
    }

    // MARK: - Location Gate

    private var locationGate: some View {
        VStack(spacing: 20) {
            Spacer()

            Image(systemName: "location.circle.fill")
                .font(.system(size: 50))
                .foregroundStyle(.tint)

            Text("Location Required")
                .font(.appTitle2)

            Text("Enable location to see products from stores in your area.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 40)

            if let error = locationManager.error {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.red)
                    .padding(.horizontal)
            }

            Button {
                locationManager.requestLocation()
            } label: {
                Label("Use My Location", systemImage: "location.fill")
            }
            .buttonStyle(.borderedProminent)
            .disabled(locationManager.isLoading)

            Spacer()
        }
    }

    // MARK: - Main Content

    private var content: some View {
        VStack(spacing: 0) {
            if viewModel.isLoading {
                LoadingView(message: "Searching...")
            } else if let error = viewModel.error {
                ErrorView(message: error) {
                    Task { await fetchProducts() }
                }
            } else if viewModel.products.isEmpty {
                VStack(spacing: 12) {
                    Spacer()
                    Image(systemName: "wineglass")
                        .font(.system(size: 40))
                        .foregroundStyle(.secondary)
                    Text("No products found")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    Text("Try adjusting your filters")
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                    Spacer()
                }
            } else {
                ScrollView {
                    VStack(spacing: 16) {
                        // Results info
                        HStack {
                            Text(viewModel.pageInfo)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Spacer()
                            Text("Page \(viewModel.currentPage) of \(viewModel.totalPages)")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        .padding(.horizontal)

                        ProductGridView(
                            products: viewModel.products,
                            onTapProduct: { product in
                                navigate(.productDetail(id: product.id))
                            }
                        )

                        if viewModel.totalPages > 1 {
                            PaginationView(
                                currentPage: viewModel.currentPage,
                                totalPages: viewModel.totalPages,
                                onPageChange: { page in
                                    filterState.currentPage = page
                                    Task { await fetchProducts() }
                                }
                            )
                        }
                    }
                    .padding(.vertical)
                }
            }
        }
    }

    // MARK: - Fetch

    private func fetchProducts() async {
        guard let location = locationManager.location else { return }
        let filters = filterState.buildFilters(
            lat: location.latitude,
            lon: location.longitude,
            radiusKm: locationManager.radiusKm
        )
        await viewModel.fetchProducts(filters: filters)
    }
}

#Preview {
    NavigationStack {
        ExploreView()
    }
    .environment(LocationManager())
    .environment(ComparisonManager())
}
