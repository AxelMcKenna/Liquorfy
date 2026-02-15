import SwiftUI

struct ProductGridView: View {
    let products: [Product]
    var onTapProduct: ((Product) -> Void)?

    private let columns = [
        GridItem(.flexible(), spacing: 12),
        GridItem(.flexible(), spacing: 12),
    ]

    var body: some View {
        LazyVGrid(columns: columns, spacing: 12) {
            ForEach(products) { product in
                ProductCardView(product: product)
                    .onTapGesture {
                        onTapProduct?(product)
                    }
            }
        }
        .padding(.horizontal)
    }
}

#Preview {
    ScrollView {
        ProductGridView(products: PreviewData.products)
    }
    .environment(ComparisonManager())
}
