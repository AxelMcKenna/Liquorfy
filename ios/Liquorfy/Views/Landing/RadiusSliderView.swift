import SwiftUI

struct RadiusSliderView: View {
    @Binding var radius: Double
    let storeCount: Int
    var onChanged: ((Double) -> Void)?

    var body: some View {
        VStack(spacing: 8) {
            HStack {
                Text("Search radius")
                    .font(.appSansMedium(size: 14, relativeTo: .subheadline))
                Spacer()
                Text("\(Int(radius)) km")
                    .font(.appSansSemiBold(size: 14, relativeTo: .subheadline))
                    .foregroundStyle(.tint)
            }

            Slider(
                value: $radius,
                in: Constants.Radius.min...Constants.Radius.max,
                step: 1
            )
            .tint(Color.appPrimary)
            .onAppear {
                // Unfilled track: hsl(38, 12%, 83%) = #d8d5ce from web app
                UISlider.appearance().maximumTrackTintColor = UIColor(Color(hex: "#d8d5ce"))
                // Green-bordered circular thumb matching web app
                let size = CGSize(width: 22, height: 22)
                let renderer = UIGraphicsImageRenderer(size: size)
                let thumbImage = renderer.image { ctx in
                    let rect = CGRect(origin: .zero, size: size).insetBy(dx: 1, dy: 1)
                    ctx.cgContext.setFillColor(UIColor.white.cgColor)
                    ctx.cgContext.fillEllipse(in: rect)
                    ctx.cgContext.setStrokeColor(UIColor(Color.appPrimary).cgColor)
                    ctx.cgContext.setLineWidth(2)
                    ctx.cgContext.strokeEllipse(in: rect)
                }
                UISlider.appearance().setThumbImage(thumbImage, for: .normal)
                UISlider.appearance().setThumbImage(thumbImage, for: .highlighted)
            }
            .onChange(of: radius) { _, newValue in
                onChanged?(newValue)
            }

            HStack {
                Text("\(Int(Constants.Radius.min)) km")
                    .font(.appCaption)
                    .foregroundStyle(.secondary)
                Spacer()
                Text("\(storeCount) stores")
                    .font(.appCaption)
                    .foregroundStyle(.secondary)
                Spacer()
                Text("\(Int(Constants.Radius.max)) km")
                    .font(.appCaption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(Color.appTertiaryBackground)
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }
}

#Preview {
    RadiusSliderView(radius: .constant(20), storeCount: 12)
        .padding()
}
