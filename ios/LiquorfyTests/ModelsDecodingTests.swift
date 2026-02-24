import XCTest
@testable import Liquorfy

final class ModelsDecodingTests: XCTestCase {

    private var decoder: JSONDecoder!

    override func setUp() {
        decoder = JSONDecoder()
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        let fallbackFormatter = ISO8601DateFormatter()
        fallbackFormatter.formatOptions = [.withInternetDateTime]

        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let string = try container.decode(String.self)
            if let date = formatter.date(from: string) { return date }
            if let date = fallbackFormatter.date(from: string) { return date }
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Cannot decode date: \(string)")
        }
    }

    func testDecodePriceSchema() throws {
        let json = """
        {
            "store_id": "550e8400-e29b-41d4-a716-446655440000",
            "store_name": "Super Liquor Newtown",
            "chain": "super_liquor",
            "price_nzd": 24.99,
            "promo_price_nzd": 19.99,
            "promo_text": "20% off",
            "promo_ends_at": "2026-02-20T00:00:00Z",
            "price_per_100ml": 1.33,
            "standard_drinks": 10.0,
            "price_per_standard_drink": 2.00,
            "is_member_only": false,
            "is_stale": false,
            "distance_km": 1.2
        }
        """.data(using: .utf8)!

        let price = try decoder.decode(Price.self, from: json)
        XCTAssertEqual(price.storeName, "Super Liquor Newtown")
        XCTAssertEqual(price.priceNzd, 24.99)
        XCTAssertEqual(price.promoPriceNzd, 19.99)
        XCTAssertTrue(price.hasPromo)
        XCTAssertEqual(price.currentPrice, 19.99)
        XCTAssertEqual(price.savingsPercent, 20)
    }

    func testDecodePriceWithNulls() throws {
        let json = """
        {
            "store_id": "550e8400-e29b-41d4-a716-446655440000",
            "store_name": "Test Store",
            "chain": "liquorland",
            "price_nzd": 30.00,
            "promo_price_nzd": null,
            "promo_text": null,
            "promo_ends_at": null,
            "price_per_100ml": null,
            "standard_drinks": null,
            "price_per_standard_drink": null,
            "is_member_only": false,
            "is_stale": false,
            "distance_km": null
        }
        """.data(using: .utf8)!

        let price = try decoder.decode(Price.self, from: json)
        XCTAssertFalse(price.hasPromo)
        XCTAssertEqual(price.currentPrice, 30.00)
        XCTAssertEqual(price.savingsPercent, 0)
        XCTAssertNil(price.distanceKm)
    }

    func testDecodeProduct() throws {
        let json = """
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Speight's Gold Medal Ale 15pk",
            "brand": "Speight's",
            "category": "beer",
            "chain": "super_liquor",
            "abv_percent": 4.0,
            "total_volume_ml": 4950,
            "pack_count": 15,
            "unit_volume_ml": 330,
            "image_url": "https://example.com/image.jpg",
            "product_url": "https://example.com/product",
            "price": {
                "store_id": "550e8400-e29b-41d4-a716-446655440001",
                "store_name": "Super Liquor",
                "chain": "super_liquor",
                "price_nzd": 24.99,
                "promo_price_nzd": null,
                "promo_text": null,
                "promo_ends_at": null,
                "price_per_100ml": null,
                "standard_drinks": null,
                "price_per_standard_drink": null,
                "is_member_only": false,
                "is_stale": false,
                "distance_km": null
            },
            "last_updated": "2026-02-15T10:30:00Z"
        }
        """.data(using: .utf8)!

        let product = try decoder.decode(Product.self, from: json)
        XCTAssertEqual(product.name, "Speight's Gold Medal Ale 15pk")
        XCTAssertEqual(product.brand, "Speight's")
        XCTAssertEqual(product.category, "beer")
        XCTAssertEqual(product.abvPercent, 4.0)
        XCTAssertEqual(product.totalVolumeMl, 4950)
        XCTAssertEqual(product.packCount, 15)
    }

    func testDecodeStore() throws {
        let json = """
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Super Liquor Newtown",
            "chain": "super_liquor",
            "lat": -41.3101,
            "lon": 174.7791,
            "address": "200 Riddiford St",
            "region": "Wellington",
            "distance_km": 1.2
        }
        """.data(using: .utf8)!

        let store = try decoder.decode(Store.self, from: json)
        XCTAssertEqual(store.name, "Super Liquor Newtown")
        XCTAssertNotNil(store.coordinate)
        XCTAssertEqual(store.coordinate?.latitude, -41.3101, accuracy: 0.001)
    }

    func testDecodeProductListResponse() throws {
        let json = """
        {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 24
        }
        """.data(using: .utf8)!

        let response = try decoder.decode(ProductListResponse.self, from: json)
        XCTAssertTrue(response.items.isEmpty)
        XCTAssertEqual(response.total, 0)
        XCTAssertEqual(response.page, 1)
        XCTAssertEqual(response.pageSize, 24)
    }

    func testDecodeStoreListResponse() throws {
        let json = """
        {
            "items": []
        }
        """.data(using: .utf8)!

        let response = try decoder.decode(StoreListResponse.self, from: json)
        XCTAssertTrue(response.items.isEmpty)
    }

    func testChainTypeFromRawValue() {
        XCTAssertEqual(ChainType(rawValue: "super_liquor"), .superLiquor)
        XCTAssertEqual(ChainType(rawValue: "paknsave"), .paknsave)
        XCTAssertEqual(ChainType(rawValue: "bottle_o"), .bottleO)
        XCTAssertNil(ChainType(rawValue: "unknown_chain"))
    }

    func testChainTypeDisplayNames() {
        XCTAssertEqual(ChainType.superLiquor.displayName, "Super Liquor")
        XCTAssertEqual(ChainType.paknsave.displayName, "PAK'nSAVE")
        XCTAssertEqual(ChainType.bottleO.displayName, "Bottle-O")
    }

    func testSortOptionRawValues() {
        XCTAssertEqual(SortOption.discount.rawValue, "discount")
        XCTAssertEqual(SortOption.bestValue.rawValue, "price_per_100ml")
        XCTAssertEqual(SortOption.cheapest.rawValue, "total_price")
    }

    func testCategoryGroups() {
        XCTAssertEqual(Category.beer.group, .beer)
        XCTAssertEqual(Category.craftBeer.group, .beer)
        XCTAssertEqual(Category.redWine.group, .wine)
        XCTAssertEqual(Category.vodka.group, .spirits)
        XCTAssertEqual(Category.rtd.group, .readyToDrink)
        XCTAssertEqual(Category.nonAlcoholic.group, .other)
    }
}
