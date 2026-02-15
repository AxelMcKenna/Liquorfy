import SwiftUI

struct CategoryPickerView: View {
    @Binding var selection: Category?

    var body: some View {
        ForEach(CategoryGroup.allCases) { group in
            DisclosureGroup(group.rawValue) {
                ForEach(group.categories) { category in
                    Button {
                        if selection == category {
                            selection = nil
                        } else {
                            selection = category
                        }
                    } label: {
                        HStack {
                            Text(category.displayName)
                                .foregroundStyle(.primary)
                            Spacer()
                            if selection == category {
                                Image(systemName: "checkmark")
                                    .foregroundStyle(.tint)
                            }
                        }
                    }
                }
            }
        }
    }
}

#Preview {
    Form {
        CategoryPickerView(selection: .constant(.beer))
    }
}
