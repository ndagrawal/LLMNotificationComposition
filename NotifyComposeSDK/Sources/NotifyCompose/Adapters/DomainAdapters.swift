// DomainAdapters.swift
// NotifyCompose SDK — Domain-Specific Request Builders
//
// Convenience builders for each supported domain.
// These encapsulate domain-specific attribute schemas and intent mappings.

import Foundation

// MARK: - Social Media Adapter

/// Builds NotificationRequests for Social Media apps.
///
/// ```swift
/// let request = SocialMediaAdapter.newContent(
///     userId: "user_123",
///     postId: "post_456",
///     postTitle: "10 Swift Tips You Need to Know",
///     creatorName: "SwiftDev",
///     viewCount: "12K",
///     category: "technology"
/// )
/// ```
public enum SocialMediaAdapter {

    public static func newContent(
        userId: String,
        postId: String,
        postTitle: String,
        creatorName: String,
        viewCount: String,
        category: String,
        triggerContext: TriggerContext = TriggerContext()
    ) -> NotificationRequest {
        NotificationRequest(
            user: UserProfile(userId: userId, clvTier: .gold),
            domain: .socialMedia,
            intent: .newContent,
            contentItem: ContentItem(
                itemId: postId,
                title: postTitle,
                category: category,
                attributes: [
                    "creator": creatorName,
                    "views": viewCount,
                    "type": "post"
                ]
            ),
            triggerContext: triggerContext
        )
    }

    public static func socialActivity(
        userId: String,
        activityId: String,
        activityDescription: String,
        friendName: String,
        contentTitle: String,
        category: String,
        triggerContext: TriggerContext = TriggerContext()
    ) -> NotificationRequest {
        NotificationRequest(
            user: UserProfile(userId: userId, clvTier: .gold),
            domain: .socialMedia,
            intent: .socialActivity,
            contentItem: ContentItem(
                itemId: activityId,
                title: contentTitle,
                category: category,
                attributes: [
                    "friend": friendName,
                    "activity": activityDescription
                ]
            ),
            triggerContext: triggerContext
        )
    }

    public static func reEngagement(
        userId: String,
        featuredContentId: String,
        featuredContentTitle: String,
        trendingTopic: String,
        category: String,
        triggerContext: TriggerContext = TriggerContext()
    ) -> NotificationRequest {
        NotificationRequest(
            user: UserProfile(userId: userId, clvTier: .silver),
            domain: .socialMedia,
            intent: .reEngagement,
            contentItem: ContentItem(
                itemId: featuredContentId,
                title: featuredContentTitle,
                category: category,
                attributes: ["trending": trendingTopic]
            ),
            triggerContext: triggerContext
        )
    }
}

// MARK: - Food Delivery Adapter

/// Builds NotificationRequests for Food Delivery apps.
///
/// ```swift
/// let request = FoodDeliveryAdapter.reEngagement(
///     userId: "user_123",
///     restaurantId: "rest_456",
///     restaurantName: "Tony's Pizza",
///     dishName: "Margherita Pizza",
///     price: "$12.99",
///     rating: "4.8",
///     deliveryTime: "25 min",
///     category: "food/italian",
///     weatherCondition: "rainy"
/// )
/// ```
public enum FoodDeliveryAdapter {

    public static func reEngagement(
        userId: String,
        restaurantId: String,
        restaurantName: String,
        dishName: String,
        price: String,
        rating: String,
        deliveryTime: String,
        category: String,
        weatherCondition: String? = nil,
        triggerContext: TriggerContext? = nil
    ) -> NotificationRequest {
        let context = triggerContext ?? TriggerContext(weatherCondition: weatherCondition)
        return NotificationRequest(
            user: UserProfile(userId: userId, clvTier: .gold),
            domain: .foodDelivery,
            intent: .reEngagement,
            contentItem: ContentItem(
                itemId: restaurantId,
                title: dishName,
                category: category,
                attributes: [
                    "restaurant": restaurantName,
                    "price": price,
                    "rating": rating,
                    "deliveryTime": deliveryTime
                ]
            ),
            triggerContext: context
        )
    }

    public static func recommendation(
        userId: String,
        itemId: String,
        dishName: String,
        restaurantName: String,
        price: String,
        rating: String,
        deliveryTime: String,
        category: String,
        triggerContext: TriggerContext = TriggerContext()
    ) -> NotificationRequest {
        NotificationRequest(
            user: UserProfile(userId: userId, clvTier: .gold),
            domain: .foodDelivery,
            intent: .recommendation,
            contentItem: ContentItem(
                itemId: itemId,
                title: dishName,
                category: category,
                attributes: [
                    "restaurant": restaurantName,
                    "price": price,
                    "rating": rating,
                    "deliveryTime": deliveryTime
                ]
            ),
            triggerContext: triggerContext
        )
    }

    public static func orderUpdate(
        userId: String,
        orderId: String,
        orderStatus: String,
        estimatedArrival: String,
        restaurantName: String,
        triggerContext: TriggerContext = TriggerContext()
    ) -> NotificationRequest {
        NotificationRequest(
            user: UserProfile(userId: userId, clvTier: .bronze),
            domain: .foodDelivery,
            intent: .orderUpdate,
            contentItem: ContentItem(
                itemId: orderId,
                title: "Your order from \(restaurantName)",
                category: "order",
                attributes: [
                    "status": orderStatus,
                    "eta": estimatedArrival,
                    "restaurant": restaurantName
                ]
            ),
            triggerContext: triggerContext,
            options: PipelineOptions(
                enableGuardrails: true,
                enableFrequencyCap: false  // Order updates bypass frequency cap
            )
        )
    }
}

// MARK: - E-Commerce Adapter

/// Builds NotificationRequests for E-Commerce apps.
///
/// ```swift
/// let request = ECommerceAdapter.abandonedCart(
///     userId: "user_123",
///     productId: "prod_789",
///     productName: "Sony WH-1000XM5 Headphones",
///     price: "$349.99",
///     discount: nil,
///     category: "electronics/audio"
/// )
/// ```
public enum ECommerceAdapter {

    public static func abandonedCart(
        userId: String,
        productId: String,
        productName: String,
        price: String,
        discount: String? = nil,
        stockLevel: String? = nil,
        category: String,
        triggerContext: TriggerContext = TriggerContext()
    ) -> NotificationRequest {
        var attributes: [String: String] = ["price": price]
        if let discount = discount { attributes["discount"] = discount }
        if let stock = stockLevel { attributes["stockLevel"] = stock }

        return NotificationRequest(
            user: UserProfile(userId: userId, clvTier: .gold),
            domain: .eCommerce,
            intent: .abandonedCart,
            contentItem: ContentItem(
                itemId: productId,
                title: productName,
                category: category,
                attributes: attributes
            ),
            triggerContext: triggerContext
        )
    }

    public static func flashSale(
        userId: String,
        productId: String,
        productName: String,
        originalPrice: String,
        salePrice: String,
        discountPercent: String,
        saleEndsAt: String,
        category: String,
        triggerContext: TriggerContext = TriggerContext()
    ) -> NotificationRequest {
        NotificationRequest(
            user: UserProfile(userId: userId, clvTier: .platinum),
            domain: .eCommerce,
            intent: .flashSale,
            contentItem: ContentItem(
                itemId: productId,
                title: productName,
                category: category,
                attributes: [
                    "originalPrice": originalPrice,
                    "salePrice": salePrice,
                    "discount": "\(discountPercent)% off",
                    "saleEndsAt": saleEndsAt
                ]
            ),
            triggerContext: triggerContext
        )
    }

    public static func recommendation(
        userId: String,
        productId: String,
        productName: String,
        price: String,
        rating: String,
        reviewCount: String,
        category: String,
        triggerContext: TriggerContext = TriggerContext()
    ) -> NotificationRequest {
        NotificationRequest(
            user: UserProfile(userId: userId, clvTier: .gold),
            domain: .eCommerce,
            intent: .recommendation,
            contentItem: ContentItem(
                itemId: productId,
                title: productName,
                category: category,
                attributes: [
                    "price": price,
                    "rating": rating,
                    "reviews": reviewCount
                ]
            ),
            triggerContext: triggerContext
        )
    }
}
