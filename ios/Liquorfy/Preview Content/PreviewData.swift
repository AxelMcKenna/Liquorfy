import Foundation

enum PreviewData {
    static let price = Price(
        storeId: UUID(),
        storeName: "Super Liquor Newtown",
        chain: "super_liquor",
        priceNzd: 24.99,
        promoPriceNzd: 19.99,
        promoText: "20% off",
        promoEndsAt: Date().addingTimeInterval(3 * 86400),
        pricePer100ml: 1.33,
        standardDrinks: 10.0,
        pricePerStandardDrink: 2.00,
        isMemberOnly: false,
        isStale: false,
        distanceKm: 1.2
    )

    static let priceNoPromo = Price(
        storeId: UUID(),
        storeName: "Liquorland Cuba",
        chain: "liquorland",
        priceNzd: 29.99,
        promoPriceNzd: nil,
        promoText: nil,
        promoEndsAt: nil,
        pricePer100ml: 2.00,
        standardDrinks: 7.9,
        pricePerStandardDrink: 3.80,
        isMemberOnly: false,
        isStale: false,
        distanceKm: 3.5
    )

    static let product = Product(
        id: UUID(),
        name: "Speight's Gold Medal Ale 15pk 330ml Bottles",
        brand: "Speight's",
        category: "beer",
        chain: "super_liquor",
        abvPercent: 4.0,
        totalVolumeMl: 4950,
        packCount: 15,
        unitVolumeMl: 330,
        imageUrl: nil,
        productUrl: "https://www.superliquor.co.nz",
        price: price,
        lastUpdated: Date()
    )

    static let productNoPromo = Product(
        id: UUID(),
        name: "Absolut Vodka 1L",
        brand: "Absolut",
        category: "vodka",
        chain: "liquorland",
        abvPercent: 40.0,
        totalVolumeMl: 1000,
        packCount: 1,
        unitVolumeMl: 1000,
        imageUrl: nil,
        productUrl: nil,
        price: priceNoPromo,
        lastUpdated: Date()
    )

    static let products = [product, productNoPromo]

    static let store = Store(
        id: UUID(),
        name: "Super Liquor Newtown",
        chain: "super_liquor",
        lat: -41.3101,
        lon: 174.7791,
        address: "200 Riddiford St, Newtown",
        region: "Wellington",
        distanceKm: 1.2
    )

    static let stores = [
        store,
        Store(
            id: UUID(),
            name: "Liquorland Cuba",
            chain: "liquorland",
            lat: -41.2925,
            lon: 174.7732,
            address: "240 Cuba St, Te Aro",
            region: "Wellington",
            distanceKm: 3.5
        ),
        Store(
            id: UUID(),
            name: "PAK'nSAVE Petone",
            chain: "paknsave",
            lat: -41.2270,
            lon: 174.8720,
            address: "2 Tawa St, Petone",
            region: "Lower Hutt",
            distanceKm: 8.2
        ),
    ]

    static let productListResponse = ProductListResponse(
        items: products,
        total: 2,
        page: 1,
        pageSize: 24
    )
}
