import XCTest
@testable import Liquorfy

final class APIClientTests: XCTestCase {

    func testProductsEndpointURL() {
        let url = APIEndpoint.products.url(queryItems: [
            URLQueryItem(name: "q", value: "beer"),
            URLQueryItem(name: "page", value: "1"),
        ])
        XCTAssertNotNil(url)
        XCTAssertTrue(url!.absoluteString.contains("/products"))
        XCTAssertTrue(url!.absoluteString.contains("q=beer"))
    }

    func testProductEndpointURL() {
        let id = UUID()
        let url = APIEndpoint.product(id).url()
        XCTAssertNotNil(url)
        XCTAssertTrue(url!.absoluteString.contains("/products/\(id)"))
    }

    func testStoresEndpointURL() {
        let url = APIEndpoint.stores.url(queryItems: [
            URLQueryItem(name: "lat", value: "-41.2865"),
            URLQueryItem(name: "lon", value: "174.7762"),
        ])
        XCTAssertNotNil(url)
        XCTAssertTrue(url!.absoluteString.contains("/stores"))
        XCTAssertTrue(url!.absoluteString.contains("lat=-41.2865"))
    }

    func testProductFiltersQueryItems() {
        var filters = ProductFilters()
        filters.query = "beer"
        filters.category = .beer
        filters.promoOnly = true
        filters.sort = .discount
        filters.page = 2

        let items = filters.queryItems
        XCTAssertTrue(items.contains(where: { $0.name == "q" && $0.value == "beer" }))
        XCTAssertTrue(items.contains(where: { $0.name == "category" && $0.value == "beer" }))
        XCTAssertTrue(items.contains(where: { $0.name == "promo_only" && $0.value == "true" }))
        XCTAssertTrue(items.contains(where: { $0.name == "sort" && $0.value == "discount" }))
        XCTAssertTrue(items.contains(where: { $0.name == "page" && $0.value == "2" }))
    }

    func testProductFiltersEmptyQuery() {
        let filters = ProductFilters()
        let items = filters.queryItems
        XCTAssertFalse(items.contains(where: { $0.name == "q" }))
        XCTAssertFalse(items.contains(where: { $0.name == "promo_only" }))
    }

    func testProductFiltersWithChains() {
        var filters = ProductFilters()
        filters.chains = [.superLiquor, .liquorland]

        let items = filters.queryItems
        let chainItems = items.filter { $0.name == "chain" }
        XCTAssertEqual(chainItems.count, 1)
        XCTAssertEqual(chainItems.first?.value, "liquorland,super_liquor")
    }
}
