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
            ForEach(Array(products.enumerated()), id: \.element.id) { (index: Int, product: Product) in
                Button {
                    onTapProduct?(product)
                } label: {
                    ProductCardView(product: product)
                }
                .buttonStyle(.pressableCard)
                .opacity(appeared.contains(product.id) ? 1 : 0)
                .offset(y: appeared.contains(product.id) ? 0 : 12)
                .onAppear {
                    withAnimation(.easeOut(duration: 0.35).delay(Double(index) * 0.05)) {
                        _ = appeared.insert(product.id)
                    }
                }
            }
        }
        .padding(.horizontal)
        .padding(.vertical, 4)
    }

    @State private var appeared: Set<UUID> = []
}

#Preview {
    ScrollView {
        ProductGridView(products: PreviewData.products)
    }
}
