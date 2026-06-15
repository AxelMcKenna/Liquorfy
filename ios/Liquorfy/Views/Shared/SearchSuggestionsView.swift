import SwiftUI

/// Dropdown content for search: recent searches and popular products before typing,
/// autocomplete suggestions once the user has typed ≥2 characters. Mirrors the web
/// SearchAutocomplete dropdown.
struct SearchSuggestionsView: View {
    let query: String
    let viewModel: AutocompleteViewModel
    let onSelectSuggestion: (Suggestion) -> Void
    let onSelectPopular: (PopularProduct) -> Void
    let onRunSearch: (String) -> Void

    private let recent = RecentSearchesManager.shared

    private var trimmed: String {
        query.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var isTyping: Bool { trimmed.count >= 2 }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                if isTyping {
                    suggestionsState
                } else {
                    emptyState
                }
            }
        }
        .frame(maxHeight: 320)
        .background(.white)
        .clipShape(RoundedRectangle(cornerRadius: 10))
        .shadow(color: .black.opacity(0.12), radius: 12, y: 6)
    }

    // MARK: - Typing

    @ViewBuilder
    private var suggestionsState: some View {
        if viewModel.isLoading && viewModel.suggestions.isEmpty {
            row {
                ProgressView().controlSize(.small)
                Text("Searching…").font(.appCaption).foregroundStyle(.secondary)
            }
        } else if viewModel.suggestions.isEmpty {
            row {
                Text("No matches").font(.appCaption).foregroundStyle(.secondary)
            }
        } else {
            ForEach(viewModel.suggestions) { suggestion in
                Button {
                    onSelectSuggestion(suggestion)
                } label: {
                    productRow(
                        name: suggestion.name,
                        brand: suggestion.brand,
                        imageUrl: suggestion.imageUrl,
                        chain: suggestion.chain
                    )
                }
                .buttonStyle(.plain)
                Divider()
            }
        }
    }

    // MARK: - Empty (recent + popular)

    @ViewBuilder
    private var emptyState: some View {
        if !recent.searches.isEmpty {
            sectionLabel("Recent") {
                Button("Clear") { recent.clearAll() }
                    .font(.appCaption)
                    .foregroundStyle(Color.appPrimary)
            }
            ForEach(recent.searches, id: \.self) { term in
                Button {
                    onRunSearch(term)
                } label: {
                    HStack(spacing: 10) {
                        Image(systemName: "clock.arrow.circlepath")
                            .font(.system(size: 13))
                            .foregroundStyle(.secondary)
                        Text(term).font(.appCardBody).foregroundStyle(.primary)
                        Spacer()
                        Button {
                            recent.remove(term)
                        } label: {
                            Image(systemName: "xmark")
                                .font(.system(size: 11))
                                .foregroundStyle(.tertiary)
                        }
                        .buttonStyle(.plain)
                    }
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                Divider()
            }
        }

        if !viewModel.popular.isEmpty {
            sectionLabel("Popular") { EmptyView() }
            ForEach(viewModel.popular) { popular in
                Button {
                    onSelectPopular(popular)
                } label: {
                    productRow(
                        name: popular.name,
                        brand: popular.brand,
                        imageUrl: popular.imageUrl,
                        chain: popular.chain
                    )
                }
                .buttonStyle(.plain)
                Divider()
            }
        }
    }

    // MARK: - Building blocks

    private func productRow(name: String, brand: String?, imageUrl: String?, chain: String) -> some View {
        HStack(spacing: 10) {
            AsyncProductImageView(url: imageUrl, size: 32)
                .frame(width: 36, height: 36)
                .background(Color.appBackground)
                .clipShape(RoundedRectangle(cornerRadius: 6))
            VStack(alignment: .leading, spacing: 2) {
                Text(name)
                    .font(.appCardBody)
                    .foregroundStyle(.primary)
                    .lineLimit(1)
                Text(brand ?? ChainConstants.displayName(for: chain))
                    .font(.appCaption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
            Spacer()
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 8)
        .contentShape(Rectangle())
    }

    private func sectionLabel<Trailing: View>(_ title: String, @ViewBuilder trailing: () -> Trailing) -> some View {
        HStack {
            Text(title.uppercased())
                .font(.appSansSemiBold(size: 11, relativeTo: .caption2))
                .foregroundStyle(.secondary)
            Spacer()
            trailing()
        }
        .padding(.horizontal, 14)
        .padding(.top, 12)
        .padding(.bottom, 6)
    }

    private func row<Content: View>(@ViewBuilder _ content: () -> Content) -> some View {
        HStack(spacing: 8, content: content)
            .padding(.horizontal, 14)
            .padding(.vertical, 12)
    }
}
