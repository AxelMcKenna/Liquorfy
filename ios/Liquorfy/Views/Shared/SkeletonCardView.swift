import SwiftUI

// MARK: - Shimmer Effect

struct ShimmerModifier: ViewModifier {
    @State private var phase: CGFloat = 0

    func body(content: Content) -> some View {
        content
            .overlay(
                LinearGradient(
                    colors: [.clear, .white.opacity(0.3), .clear],
                    startPoint: .leading,
                    endPoint: .trailing
                )
                .offset(x: phase)
                .mask(content)
            )
            .onAppear {
                withAnimation(.linear(duration: 1.5).repeatForever(autoreverses: false)) {
                    phase = 300
                }
            }
    }
}

// MARK: - Skeleton Product Card (matches ProductCardView shape)

struct SkeletonCardView: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Image placeholder
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.appTertiaryBackground)
                .aspectRatio(1, contentMode: .fit)

            // Text placeholders
            VStack(alignment: .leading, spacing: 6) {
                RoundedRectangle(cornerRadius: 4)
                    .fill(Color.appTertiaryBackground)
                    .frame(height: 14)

                RoundedRectangle(cornerRadius: 4)
                    .fill(Color.appTertiaryBackground)
                    .frame(width: 80, height: 10)

                RoundedRectangle(cornerRadius: 4)
                    .fill(Color.appTertiaryBackground)
                    .frame(width: 60, height: 16)
            }
        }
        .padding(12)
        .cardStyle()
        .modifier(ShimmerModifier())
    }
}

// MARK: - Skeleton Grid (for ExploreView)

struct SkeletonGridView: View {
    var count: Int = 6

    private let columns = [
        GridItem(.flexible(), spacing: 12),
        GridItem(.flexible(), spacing: 12),
    ]

    var body: some View {
        LazyVGrid(columns: columns, spacing: 12) {
            ForEach(0..<count, id: \.self) { _ in
                SkeletonCardView()
            }
        }
        .padding(.horizontal)
    }
}

// MARK: - Skeleton Deal Card (for LandingView horizontal scroll)

struct SkeletonDealCardView: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.appTertiaryBackground)
                .frame(height: 156)

            VStack(alignment: .leading, spacing: 6) {
                RoundedRectangle(cornerRadius: 4)
                    .fill(Color.appTertiaryBackground)
                    .frame(height: 12)

                RoundedRectangle(cornerRadius: 4)
                    .fill(Color.appTertiaryBackground)
                    .frame(width: 70, height: 10)

                RoundedRectangle(cornerRadius: 4)
                    .fill(Color.appTertiaryBackground)
                    .frame(width: 50, height: 14)
            }
        }
        .frame(width: 180)
        .padding(12)
        .cardStyle()
        .modifier(ShimmerModifier())
    }
}

struct SkeletonDealScrollView: View {
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            LazyHStack(spacing: 12) {
                ForEach(0..<4, id: \.self) { _ in
                    SkeletonDealCardView()
                }
            }
            .padding(.horizontal, 1)
        }
    }
}

#Preview("Grid") {
    ScrollView {
        SkeletonGridView()
    }
    .background(Color.appBackground)
}

#Preview("Deals") {
    SkeletonDealScrollView()
        .padding()
        .background(Color.appBackground)
}
