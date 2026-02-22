import SwiftUI

struct RadiusSliderView: View {
    @Binding var radius: Double
    let storeCount: Int
    var onChanged: ((Double) -> Void)?

    var body: some View {
        VStack(spacing: 8) {
            HStack {
                Text("Search radius")
                    .font(.subheadline)
                    .fontWeight(.medium)
                Spacer()
                Text("\(Int(radius)) km")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundStyle(.tint)
            }

            Slider(
                value: $radius,
                in: Constants.Radius.min...Constants.Radius.max,
                step: 1
            )
            .onChange(of: radius) { _, newValue in
                onChanged?(newValue)
            }

            HStack {
                Text("\(Int(Constants.Radius.min)) km")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Spacer()
                Text("\(storeCount) stores")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Spacer()
                Text("\(Int(Constants.Radius.max)) km")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(Color.appCardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

#Preview {
    RadiusSliderView(radius: .constant(20), storeCount: 12)
        .padding()
}
