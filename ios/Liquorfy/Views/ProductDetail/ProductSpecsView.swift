import SwiftUI

struct ProductSpecsView: View {
    let product: Product

    var body: some View {
        let specs = buildSpecs()

        if !specs.isEmpty {
            VStack(alignment: .leading, spacing: 8) {
                Text("Product Details")
                    .font(.appSansSemiBold(size: 14, relativeTo: .subheadline))
                    .foregroundStyle(.primary)

                LazyVGrid(columns: [
                    GridItem(.flexible()),
                    GridItem(.flexible()),
                ], alignment: .leading, spacing: 8) {
                    ForEach(specs, id: \.label) { spec in
                        VStack(alignment: .leading, spacing: 2) {
                            Text(spec.label)
                                .font(.appCaption)
                                .foregroundStyle(.secondary)
                            Text(spec.value)
                                .font(.appCardTitle)
                        }
                    }
                }
            }
        }
    }

    private struct Spec {
        let label: String
        let value: String
    }

    private func buildSpecs() -> [Spec] {
        var specs: [Spec] = []

        if let category = product.category {
            specs.append(Spec(label: "Category", value: Formatters.formatCategory(category)))
        }
        if let abv = product.abvPercent {
            specs.append(Spec(label: "Alcohol", value: "\(abv)%"))
        }
        if let volume = product.totalVolumeMl {
            specs.append(Spec(label: "Volume", value: "\(Int(volume))ml"))
        }
        if let pack = product.packCount, pack > 1 {
            specs.append(Spec(label: "Pack Size", value: "\(pack) units"))
        }

        return specs
    }
}

#if DEBUG
#Preview {
    ProductSpecsView(product: PreviewData.product)
        .padding()
}
#endif
