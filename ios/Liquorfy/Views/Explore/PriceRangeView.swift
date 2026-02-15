import SwiftUI

struct PriceRangeView: View {
    @Binding var priceMin: Double?
    @Binding var priceMax: Double?

    @State private var minText: String = ""
    @State private var maxText: String = ""

    var body: some View {
        HStack(spacing: 12) {
            HStack {
                Text("$")
                    .foregroundStyle(.secondary)
                TextField("Min", text: $minText)
                    .keyboardType(.decimalPad)
                    .onChange(of: minText) { _, newValue in
                        priceMin = Double(newValue)
                    }
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 8)
            .background(Color(.systemGray6))
            .clipShape(RoundedRectangle(cornerRadius: 8))

            Text("to")
                .foregroundStyle(.secondary)

            HStack {
                Text("$")
                    .foregroundStyle(.secondary)
                TextField("Max", text: $maxText)
                    .keyboardType(.decimalPad)
                    .onChange(of: maxText) { _, newValue in
                        priceMax = Double(newValue)
                    }
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 8)
            .background(Color(.systemGray6))
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
        .onAppear {
            if let priceMin { minText = String(format: "%.0f", priceMin) }
            if let priceMax { maxText = String(format: "%.0f", priceMax) }
        }
    }
}

#Preview {
    Form {
        PriceRangeView(priceMin: .constant(nil), priceMax: .constant(nil))
    }
}
