import SwiftUI

struct FilterSheetView: View {
    @Bindable var filterState: FilterState
    var onApply: () -> Void

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 0) {
                    // Header
                    VStack(spacing: 12) {
                        HStack {
                            HStack(spacing: 8) {
                                Text("Filters")
                                    .font(.appSansSemiBold(size: 18, relativeTo: .title3))

                                if filterState.activeFilterCount > 0 {
                                    Text("\(filterState.activeFilterCount)")
                                        .font(.appBadge)
                                        .foregroundStyle(.white)
                                        .padding(.horizontal, 7)
                                        .padding(.vertical, 2)
                                        .background(Color.appPrimary)
                                        .clipShape(RoundedRectangle(cornerRadius: 6))
                                }
                            }

                            Spacer()

                            if filterState.hasActiveFilters {
                                Button {
                                    filterState.reset()
                                } label: {
                                    Text("Clear all filters")
                                        .font(.appSans(size: 12, relativeTo: .caption))
                                        .foregroundStyle(.primary)
                                }
                            }
                        }
                    }
                    .padding(.horizontal, 24)
                    .padding(.vertical, 20)

                    Divider()

                    // Filter sections
                    VStack(spacing: 32) {
                        // Category
                        filterSection(icon: "square.grid.2x2", title: "Category") {
                            CategoryPickerView(selection: $filterState.category)
                        }

                        // Sort By
                        filterSection(icon: "arrow.up.arrow.down", title: "Sort By") {
                            SortPickerView(selection: $filterState.sort)
                        }

                        // Chains
                        filterSection(icon: "building.2", title: "Chains") {
                            ChainFilterView(selectedChains: $filterState.selectedChains)
                        }

                        // Price Range
                        filterSection(icon: "dollarsign.circle", title: "Price Range") {
                            PriceRangeView(
                                priceMin: $filterState.priceMin,
                                priceMax: $filterState.priceMax
                            )
                        }

                        // Options
                        filterSection(icon: "slider.horizontal.3", title: "Options") {
                            VStack(spacing: 12) {
                                checkboxRow(
                                    label: "Promo items only",
                                    isOn: $filterState.promoOnly
                                )
                                checkboxRow(
                                    label: "Unique products",
                                    isOn: $filterState.uniqueProducts
                                )
                            }
                        }
                    }
                    .padding(.horizontal, 24)
                    .padding(.vertical, 16)
                }
            }
            .background(.white)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "xmark")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundStyle(.secondary)
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        dismiss()
                        onApply()
                    } label: {
                        Text("Apply")
                            .font(.appSansSemiBold(size: 15, relativeTo: .body))
                            .foregroundStyle(.white)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 8)
                            .background(Color.appPrimary)
                            .clipShape(RoundedRectangle(cornerRadius: 6))
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    // MARK: - Section Builder

    private func filterSection<Content: View>(
        icon: String,
        title: String,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 13))
                    .foregroundStyle(.primary)
                Text(title)
                    .font(.appSansSemiBold(size: 13, relativeTo: .caption))
                    .foregroundStyle(.primary)
                    .textCase(.uppercase)
            }
            content()
        }
    }

    // MARK: - Checkbox Row

    private func checkboxRow(label: String, isOn: Binding<Bool>) -> some View {
        Button {
            isOn.wrappedValue.toggle()
        } label: {
            HStack(spacing: 10) {
                Image(systemName: isOn.wrappedValue ? "checkmark.square.fill" : "square")
                    .font(.system(size: 16))
                    .foregroundStyle(.primary)

                Text(label)
                    .font(.appSansMedium(size: 14, relativeTo: .subheadline))
                    .foregroundStyle(.primary)

                Spacer()
            }
        }
    }
}

#Preview {
    FilterSheetView(filterState: FilterState(), onApply: {})
}
