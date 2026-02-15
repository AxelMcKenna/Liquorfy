import SwiftUI

struct AsyncProductImageView: View {
    let url: String?
    var size: CGFloat = 100

    var body: some View {
        if let url, let imageURL = URL(string: url) {
            AsyncImage(url: imageURL) { phase in
                switch phase {
                case .empty:
                    placeholder
                case .success(let image):
                    image
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                case .failure:
                    placeholder
                @unknown default:
                    placeholder
                }
            }
            .frame(width: size, height: size)
        } else {
            placeholder
        }
    }

    private var placeholder: some View {
        Image(systemName: "wineglass")
            .font(.system(size: size * 0.35))
            .foregroundStyle(.tertiary)
            .frame(width: size, height: size)
            .background(Color(.systemGray6))
    }
}

#Preview {
    HStack {
        AsyncProductImageView(url: nil)
        AsyncProductImageView(url: "https://invalid.url/image.png")
    }
}
