import SwiftUI

struct ExploreView: View {
    var initialQuery: String?
    var initialPromoOnly: Bool = false

    @Environment(LocationManager.self) private var locationManager
    @Environment(\.navigate) private var navigate
    @Environment(\.dismiss) private var dismiss

    @State private var viewModel = ExploreViewModel()
    @State private var filterState = FilterState()
    @State private var showFilters = false
    @State private var showLocation = false
    @State private var quickViewProduct: Product?
    @FocusState private var isSearchFocused: Bool

    var body: some View {
        Group {
            if !locationManager.isLocationSet {
                locationGate
            } else {
                content
            }
        }
        .navigationBarHidden(true)
        .sheet(isPresented: $showFilters) {
            FilterSheetView(filterState: filterState) {
                filterState.currentPage = 1
                Task { await fetchProducts() }
            }
        }
        .sheet(isPresented: $showLocation) {
            LocationSheetView {
                filterState.currentPage = 1
                Task { await fetchProducts() }
            }
        }
        .sheet(item: $quickViewProduct) { product in
            QuickViewSheet(product: product)
                .presentationDetents([.large])
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
    }

    // MARK: - Location Gate

    private var locationGate: some View {
        VStack {
            Spacer()
            LocationRequestView()
            Spacer()
        }
    }

    // MARK: - Custom Header

    private var headerBar: some View {
        VStack(spacing: 12) {
            HStack(spacing: 12) {
                Button {
                    dismiss()
                } label: {
                    Text("LIQUORFY")
                        .font(.appSansBold(size: 22, relativeTo: .title2))
                        .foregroundStyle(.white)
                }

                Spacer()

                // Location button
                Button {
                    showLocation = true
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "mappin.circle.fill")
                            .font(.system(size: 14, weight: .medium))
                        if locationManager.isLocationSet {
                            Text("\(Int(locationManager.radiusKm)) km")
                                .font(.appBadge)
                        }
                    }
                    .foregroundStyle(.white)
                }

                // Filter button
                Button {
                    showFilters = true
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "line.3.horizontal.decrease")
                            .font(.system(size: 14, weight: .medium))
                        if filterState.activeFilterCount > 0 {
                            Text("\(filterState.activeFilterCount)")
                                .font(.appBadge)
                                .padding(.horizontal, 5)
                                .padding(.vertical, 1)
                                .background(.white.opacity(0.3))
                                .clipShape(RoundedRectangle(cornerRadius: 4))
                        }
                    }
                    .foregroundStyle(.white)
                }
            }

            // Search bar
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 14))
                    .foregroundStyle(.secondary)

                TextField("Search products", text: $filterState.query)
                    .font(.appCardBody)
                    .focused($isSearchFocused)
                    .submitLabel(.search)
                    .onSubmit {
                        filterState.currentPage = 1
                        Task { await fetchProducts() }
                    }

                if !filterState.query.isEmpty {
                    Button {
                        filterState.query = ""
                        filterState.currentPage = 1
                        Task { await fetchProducts() }
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 14))
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .padding(.horizontal, 12)
            .frame(height: 36)
            .background(.white)
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 14)
        .padding(.top, 6)
        .background(Color.appPrimary)
    }

    // MARK: - Main Content

    private var content: some View {
        VStack(spacing: 0) {
            headerBar

            if viewModel.isLoading {
                ScrollView {
                    SkeletonGridView(count: 6)
                        .padding(.vertical)
                }
                .refreshable {
                    await fetchProducts()
                }
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
                        .font(.appCardBody)
                        .foregroundStyle(.secondary)
                    Text("Try adjusting your filters")
                        .font(.appCaption)
                        .foregroundStyle(.tertiary)
                    Spacer()
                }
            } else {
                ScrollView {
                    VStack(spacing: 16) {
                        // Results info
                        HStack {
                            Text(viewModel.pageInfo)
                                .font(.appCaption)
                                .foregroundStyle(.secondary)
                            Spacer()
                            Text("Page \(viewModel.currentPage) of \(viewModel.totalPages)")
                                .font(.appCaption)
                                .foregroundStyle(.secondary)
                        }
                        .padding(.horizontal)

                        ProductGridView(
                            products: viewModel.products,
                            onTapProduct: { product in
                                quickViewProduct = product
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
                .refreshable {
                    await fetchProducts()
                }
            }
        }
        .background(Color.appBackground)
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
}
