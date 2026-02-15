import SwiftUI

struct PaginationView: View {
    let currentPage: Int
    let totalPages: Int
    var onPageChange: (Int) -> Void

    var body: some View {
        HStack(spacing: 8) {
            // Previous
            Button {
                onPageChange(currentPage - 1)
            } label: {
                Image(systemName: "chevron.left")
                    .font(.caption)
                    .fontWeight(.semibold)
            }
            .disabled(currentPage <= 1)

            // Page numbers
            ForEach(visiblePages, id: \.self) { item in
                switch item {
                case .page(let num):
                    Button {
                        onPageChange(num)
                    } label: {
                        Text("\(num)")
                            .font(.caption)
                            .fontWeight(num == currentPage ? .bold : .regular)
                            .frame(minWidth: 28, minHeight: 28)
                            .background(num == currentPage ? Color.accentColor : Color.clear)
                            .foregroundStyle(num == currentPage ? .white : .primary)
                            .clipShape(RoundedRectangle(cornerRadius: 6))
                    }
                case .ellipsis:
                    Text("...")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            // Next
            Button {
                onPageChange(currentPage + 1)
            } label: {
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .fontWeight(.semibold)
            }
            .disabled(currentPage >= totalPages)
        }
        .padding(.vertical, 8)
    }

    private enum PageItem: Hashable {
        case page(Int)
        case ellipsis
    }

    private var visiblePages: [PageItem] {
        var items: [PageItem] = []
        let maxVisible = 7

        if totalPages <= maxVisible {
            return (1...totalPages).map { .page($0) }
        }

        items.append(.page(1))

        if currentPage > 3 {
            items.append(.ellipsis)
        }

        let start = max(2, currentPage - 1)
        let end = min(totalPages - 1, currentPage + 1)

        for i in start...end {
            items.append(.page(i))
        }

        if currentPage < totalPages - 2 {
            items.append(.ellipsis)
        }

        items.append(.page(totalPages))

        return items
    }
}

#Preview {
    PaginationView(currentPage: 3, totalPages: 10, onPageChange: { _ in })
}
