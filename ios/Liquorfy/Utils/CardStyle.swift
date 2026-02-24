import SwiftUI

// MARK: - Card Shadow Modifier
// Double shadow mimics Tailwind shadow-md from the web app

struct CardStyleModifier: ViewModifier {
    var cornerRadius: CGFloat = 12

    func body(content: Content) -> some View {
        content
            .background(.white)
            .clipShape(RoundedRectangle(cornerRadius: cornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius)
                    .stroke(Color.black.opacity(0.08), lineWidth: 1)
            )
            .shadow(color: .black.opacity(0.10), radius: 6, x: 0, y: 4)
            .shadow(color: .black.opacity(0.06), radius: 3, x: 0, y: 2)
    }
}

extension View {
    func cardStyle(cornerRadius: CGFloat = 12) -> some View {
        modifier(CardStyleModifier(cornerRadius: cornerRadius))
    }
}
