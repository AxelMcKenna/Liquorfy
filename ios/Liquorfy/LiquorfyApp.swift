import SwiftUI

enum AppDestination: Hashable {
    case explore(query: String? = nil, promoOnly: Bool = false)
    case productDetail(id: UUID)
}

@main
struct LiquorfyApp: App {
    @State private var locationManager = LocationManager()
    @State private var navigationPath = NavigationPath()

    var body: some Scene {
        WindowGroup {
            NavigationStack(path: $navigationPath) {
                LandingView()
                    .navigationDestination(for: AppDestination.self) { destination in
                        switch destination {
                        case .explore(let query, let promoOnly):
                            ExploreView(initialQuery: query, initialPromoOnly: promoOnly)
                        case .productDetail(let id):
                            ProductDetailView(productId: id)
                        }
                    }
            }
            .environment(locationManager)
            .environment(\.navigate, NavigateAction { destination in
                navigationPath.append(destination)
            })
            .tint(.appPrimary)
        }
    }
}

// MARK: - Navigation Environment Key

struct NavigateAction {
    let action: (AppDestination) -> Void

    func callAsFunction(_ destination: AppDestination) {
        action(destination)
    }
}

private struct NavigateKey: EnvironmentKey {
    static let defaultValue = NavigateAction { _ in }
}

extension EnvironmentValues {
    var navigate: NavigateAction {
        get { self[NavigateKey.self] }
        set { self[NavigateKey.self] = newValue }
    }
}
