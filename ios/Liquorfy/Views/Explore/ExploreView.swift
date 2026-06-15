import SwiftUI

struct ExploreView: View {
    var initialQuery: String?
    var initialPromoOnly: Bool = false

    @Environment(LocationManager.self) private var locationManager
    @Environment(AuthManager.self) private var authManager
    @Environment(\.navigate) private var navigate
    @Environment(\.dismiss) private var dismiss

    @State private var viewModel = ExploreViewModel()
    @State private var filterState = FilterState()
    @State private var autocompleteVM = AutocompleteViewModel()
    @State private var showFilters = false
    @State private var showLocation = false
    @State private var quickViewProduct: Product?
    @State private var bannerDismissed = false
    @State private var didInit = false
    @FocusState private var isSearchFocused: Bool

    // Browsing is allowed without a location (matching web): locationless queries
    // are forced to promo-only when there's no search term and pinned to page 1.
    private var needsLocation: Bool { !locationManager.isLocationSet }
    private var needsSignIn: Bool { !authManager.isAuthenticated }
    private var showBanner: Bool { !bannerDismissed && (needsLocation || needsSignIn) }

    var body: some View {
        content
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
            .task {
                applyInitialState()
                await fetchProducts()
            }
            .onChange(of: locationManager.isLocationSet) {
                filterState.currentPage = 1
                Task { await fetchProducts() }
            }
            .onChange(of: locationManager.radiusKm) {
                Task { await fetchProducts() }
            }
            .onChange(of: filterState.sort) {
                filterState.currentPage = 1
                Task { await fetchProducts() }
            }
            .onChange(of: filterState.query) {
                autocompleteVM.updateQuery(filterState.query)
            }
            .onChange(of: isSearchFocused) {
                if isSearchFocused {
                    Task { await autocompleteVM.loadPopular() }
                }
            }
    }

    private func applyInitialState() {
        guard !didInit else { return }
        didInit = true
        if let initialQuery, !initialQuery.isEmpty {
            filterState.query = initialQuery
        }
        if initialPromoOnly {
            filterState.promoOnly = true
        }
        // Apply saved defaults only on a clean entry (no incoming query/promo).
        if (initialQuery?.isEmpty ?? true) && !initialPromoOnly {
            filterState.applySavedFilters()
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
                    .foregroundStyle(.primary.opacity(0.5))

                TextField("", text: $filterState.query, prompt: Text("Search products").foregroundStyle(.primary))
                    .font(.appCardBody)
                    .foregroundStyle(.primary)
                    .tint(.primary)
                    .focused($isSearchFocused)
                    .submitLabel(.search)
                    .onSubmit {
                        let trimmed = filterState.query.trimmingCharacters(in: .whitespacesAndNewlines)
                        if !trimmed.isEmpty {
                            RecentSearchesManager.shared.add(trimmed)
                        }
                        isSearchFocused = false
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

            if showBanner {
                promptBanner
            }

            ZStack(alignment: .top) {
                resultsView

                if isSearchFocused {
                    SearchSuggestionsView(
                        query: filterState.query,
                        viewModel: autocompleteVM,
                        onSelectSuggestion: { suggestion in
                            isSearchFocused = false
                            navigate(.productDetail(id: suggestion.id))
                        },
                        onSelectPopular: { popular in
                            isSearchFocused = false
                            navigate(.productDetail(id: popular.id))
                        },
                        onRunSearch: { term in
                            filterState.query = term
                            RecentSearchesManager.shared.add(term)
                            isSearchFocused = false
                            filterState.currentPage = 1
                            Task { await fetchProducts() }
                        }
                    )
                    .padding(.horizontal, 12)
                    .padding(.top, 8)
                    .zIndex(1)
                }
            }
        }
        .background(Color.appBackground)
    }

    @ViewBuilder
    private var resultsView: some View {
        VStack(spacing: 0) {
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
                        // Results info + sort
                        HStack {
                            Text(viewModel.pageInfo)
                                .font(.appCaption)
                                .foregroundStyle(.secondary)
                            Spacer()
                            SortPickerView(selection: $filterState.sort)
                                .frame(width: 190)
                        }
                        .padding(.horizontal)

                        ProductGridView(
                            products: viewModel.products,
                            sort: filterState.sort,
                            onTapProduct: { product in
                                quickViewProduct = product
                            }
                        )

                        // Pagination only when location is set (locationless queries are page-1 only).
                        if locationManager.isLocationSet && viewModel.totalPages > 1 {
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

    // MARK: - Prompt Banner

    private var promptBanner: some View {
        HStack(spacing: 12) {
            Image(systemName: "info.circle.fill")
                .foregroundStyle(Color.appPrimary)

            VStack(alignment: .leading, spacing: 2) {
                Text(needsLocation ? "See what's cheapest nearby" : "Save your watchlist")
                    .font(.appSansSemiBold(size: 14, relativeTo: .subheadline))
                Text(needsLocation
                     ? "Set your location for distances and local deals."
                     : "Sign in to track prices and favourites.")
                    .font(.appCaption)
                    .foregroundStyle(.secondary)
            }

            Spacer(minLength: 8)

            if needsLocation {
                Button("Enable") { showLocation = true }
                    .font(.appSansSemiBold(size: 13, relativeTo: .footnote))
                    .buttonStyle(.borderedProminent)
                    .controlSize(.small)
            } else if needsSignIn {
                Button("Sign in") { navigate(.login) }
                    .font(.appSansSemiBold(size: 13, relativeTo: .footnote))
                    .buttonStyle(.borderedProminent)
                    .controlSize(.small)
            }

            Button {
                bannerDismissed = true
            } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(Color.appPrimary.opacity(0.06))
    }

    // MARK: - Fetch

    private func fetchProducts() async {
        let hasLocation = locationManager.isLocationSet
        let location = locationManager.location

        var filters = filterState.buildFilters(
            lat: hasLocation ? location?.latitude : nil,
            lon: hasLocation ? location?.longitude : nil,
            radiusKm: hasLocation ? locationManager.radiusKm : nil
        )
        filters.uniqueProducts = true

        if !hasLocation {
            // Locationless queries are pinned to page 1, and the API requires either
            // promo_only or a search query — so force promo_only when there's no query.
            filters.page = 1
            if filters.query?.isEmpty ?? true {
                filters.promoOnly = true
            }
        }

        await viewModel.fetchProducts(filters: filters)
    }
}

#Preview {
    NavigationStack {
        ExploreView()
    }
    .environment(LocationManager())
    .environment(AuthManager())
}
