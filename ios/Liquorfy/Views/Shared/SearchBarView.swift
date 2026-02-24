import SwiftUI

struct SearchBarView: View {
    @Binding var text: String
    var placeholder: String = "Search for beer, wine, or spirits"
    var onSubmit: () -> Void = {}

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(.secondary)

            TextField(placeholder, text: $text)
                .textFieldStyle(.plain)
                .submitLabel(.search)
                .onSubmit(onSubmit)
                .autocorrectionDisabled()

            if !text.isEmpty {
                Button {
                    text = ""
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(.secondary)
                }
                .accessibilityLabel("Clear search")
            }

            Button {
                onSubmit()
            } label: {
                Text("Search")
                    .font(.appSansSemiBold(size: 14, relativeTo: .subheadline))
                    .foregroundStyle(.white)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 8)
                    .background(Color.appPrimary)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
            }
            .buttonStyle(.plain)
        }
        .padding(.leading, 12)
        .padding(.vertical, 5)
        .padding(.trailing, 5)
        .background(.white)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

#Preview {
    SearchBarView(text: .constant(""))
        .padding()
        .background(Color.appPrimary)
}
