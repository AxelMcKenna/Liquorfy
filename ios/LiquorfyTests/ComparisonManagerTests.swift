import XCTest
@testable import Liquorfy

final class ComparisonManagerTests: XCTestCase {

    private var manager: ComparisonManager!

    override func setUp() {
        manager = ComparisonManager()
    }

    func testInitiallyEmpty() {
        XCTAssertTrue(manager.isEmpty)
        XCTAssertEqual(manager.count, 0)
        XCTAssertFalse(manager.isAtLimit)
    }

    func testToggleAddsProduct() {
        let product = PreviewData.product
        manager.toggle(product)
        XCTAssertEqual(manager.count, 1)
        XCTAssertTrue(manager.contains(product))
    }

    func testToggleRemovesProduct() {
        let product = PreviewData.product
        manager.toggle(product)
        manager.toggle(product)
        XCTAssertEqual(manager.count, 0)
        XCTAssertFalse(manager.contains(product))
    }

    func testMaxLimit() {
        // Add 4 products (the limit)
        for _ in 0..<4 {
            let product = makeProduct()
            manager.toggle(product)
        }

        XCTAssertEqual(manager.count, 4)
        XCTAssertTrue(manager.isAtLimit)

        // 5th product should not be added
        let extra = makeProduct()
        manager.toggle(extra)
        XCTAssertEqual(manager.count, 4)
        XCTAssertFalse(manager.contains(extra))
    }

    func testRemove() {
        let product = PreviewData.product
        manager.toggle(product)
        manager.remove(product)
        XCTAssertEqual(manager.count, 0)
    }

    func testClear() {
        manager.toggle(PreviewData.product)
        manager.toggle(PreviewData.productNoPromo)
        manager.clear()
        XCTAssertTrue(manager.isEmpty)
    }

    func testSortedByPrice() {
        let cheap = makeProduct(price: 10.0)
        let expensive = makeProduct(price: 50.0)

        manager.toggle(expensive)
        manager.toggle(cheap)

        let sorted = manager.sortedByPrice()
        XCTAssertEqual(sorted.first?.price.priceNzd, 10.0)
        XCTAssertEqual(sorted.last?.price.priceNzd, 50.0)
    }

    // MARK: - Helpers

    private func makeProduct(price: Double = 20.0) -> Product {
        Product(
            id: UUID(),
            name: "Test Product",
            brand: nil,
            category: nil,
            chain: "super_liquor",
            abvPercent: nil,
            totalVolumeMl: nil,
            packCount: nil,
            unitVolumeMl: nil,
            imageUrl: nil,
            productUrl: nil,
            price: Price(
                storeId: UUID(),
                storeName: "Store",
                chain: "super_liquor",
                priceNzd: price,
                promoPriceNzd: nil,
                promoText: nil,
                promoEndsAt: nil,
                pricePer100ml: nil,
                standardDrinks: nil,
                pricePerStandardDrink: nil,
                isMemberOnly: false,
                distanceKm: nil
            ),
            lastUpdated: Date()
        )
    }
}
