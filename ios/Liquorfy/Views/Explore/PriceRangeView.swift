import SwiftUI

struct PriceRangeView: View {
    @Binding var priceMin: Double?
    @Binding var priceMax: Double?

    @State private var minText: String = ""
    @State private var maxText: String = ""

    var body: some View {
        VStack(spacing: 8) {
            HStack(spacing: 12) {
                // Min field
                VStack(alignment: .leading, spacing: 4) {
                    Text("Min")
                        .font(.appSans(size: 12, relativeTo: .caption))
                        .foregroundStyle(.black)
                    HStack(spacing: 4) {
                        Text("$")
                            .font(.appCardBody)
                            .foregroundStyle(.black)
                        TextField("0", text: $minText)
                            .font(.appCardBody)
                            .keyboardType(.numberPad)
                            .onChange(of: minText) { _, newValue in
                                priceMin = Double(newValue)
                            }
                    }
                    .padding(.horizontal, 12)
                    .frame(height: 40)
                    .background(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                    )
                }

                Text("–")
                    .font(.appCardBody)
                    .foregroundStyle(.black)
                    .padding(.top, 20)

                // Max field
                VStack(alignment: .leading, spacing: 4) {
                    Text("Max")
                        .font(.appSans(size: 12, relativeTo: .caption))
                        .foregroundStyle(.black)
                    HStack(spacing: 4) {
                        Text("$")
                            .font(.appCardBody)
                            .foregroundStyle(.black)
                        TextField("200+", text: $maxText)
                            .font(.appCardBody)
                            .keyboardType(.numberPad)
                            .onChange(of: maxText) { _, newValue in
                                priceMax = Double(newValue)
                            }
                    }
                    .padding(.horizontal, 12)
                    .frame(height: 40)
                    .background(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                    )
                }
            }
        }
        .onAppear {
            if let priceMin { minText = String(format: "%.0f", priceMin) }
            if let priceMax { maxText = String(format: "%.0f", priceMax) }
        }
    }
}

#Preview {
    PriceRangeView(priceMin: .constant(nil), priceMax: .constant(nil))
        .padding()
}
