import SwiftUI

struct FilterSheetView: View {
    @Bindable var filterState: FilterState
    var onApply: () -> Void

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                // Category
                Section("Category") {
                    CategoryPickerView(selection: $filterState.category)
                }

                // Chains
                Section("Chains") {
                    ChainFilterView(selectedChains: $filterState.selectedChains)
                }

                // Price Range
                Section("Price Range") {
                    PriceRangeView(
                        priceMin: $filterState.priceMin,
                        priceMax: $filterState.priceMax
                    )
                }

                // Sort
                Section("Sort By") {
                    SortPickerView(selection: $filterState.sort)
                }

                // Toggles
                Section {
                    Toggle("Promotions Only", isOn: $filterState.promoOnly)
                    Toggle("Unique Products", isOn: $filterState.uniqueProducts)
                }
            }
            .navigationTitle("Filters")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Reset") {
                        filterState.reset()
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Apply") {
                        dismiss()
                        onApply()
                    }
                    .fontWeight(.semibold)
                }
            }
        }
    }
}

#Preview {
    FilterSheetView(filterState: FilterState(), onApply: {})
}
