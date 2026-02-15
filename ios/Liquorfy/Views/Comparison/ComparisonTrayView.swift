import SwiftUI

struct ComparisonTrayView: View {
    @Environment(ComparisonManager.self) private var comparisonManager
    @State private var showShareSheet = false

    var body: some View {
        VStack(spacing: 8) {
            // Handle
            Capsule()
                .fill(Color(.systemGray4))
                .frame(width: 36, height: 4)
                .padding(.top, 6)

            HStack {
                Text("Compare (\(comparisonManager.count)/\(Constants.Comparison.maxProducts))")
                    .font(.subheadline)
                    .fontWeight(.semibold)

                Spacer()

                Button("Clear") {
                    comparisonManager.clear()
                }
                .font(.caption)
                .foregroundStyle(.red)
            }
            .padding(.horizontal)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 10) {
                    ForEach(comparisonManager.sortedByPrice()) { product in
                        ComparisonItemView(product: product)
                    }
                }
                .padding(.horizontal)
            }

            // Actions
            HStack(spacing: 12) {
                Button {
                    showShareSheet = true
                } label: {
                    Label("Share", systemImage: "square.and.arrow.up")
                        .font(.caption)
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
                .disabled(comparisonManager.isEmpty)
            }
            .padding(.horizontal)
            .padding(.bottom, 4)
        }
        .padding(.bottom, 4)
        .background(.ultraThinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .shadow(color: .black.opacity(0.1), radius: 10, y: -5)
        .padding(.horizontal, 8)
        .sheet(isPresented: $showShareSheet) {
            ShareSheet(items: [comparisonShareText])
        }
    }

    private var comparisonShareText: String {
        var text = "Liquorfy Price Comparison:\n\n"
        for product in comparisonManager.sortedByPrice() {
            text += "\(product.name) - \(Formatters.formatPrice(product.price.currentPrice)) at \(product.price.storeName)\n"
        }
        return text
    }
}

// UIKit share sheet wrapper
struct ShareSheet: UIViewControllerRepresentable {
    let items: [Any]

    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: items, applicationActivities: nil)
    }

    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}

#Preview {
    ComparisonTrayView()
        .environment(ComparisonManager())
}
