// Models.swift
// NotifyCompose SDK
//
// Core data models implementing the paper's conceptual entities:
// UserProfile, NotificationRequest, ComposedNotification, and supporting types.

import Foundation

// MARK: - User Profile

/// Represents a user's behavioural and preference profile.
/// Maps to the "User Profile" input node in the unified pipeline (Figure 2).
public struct UserProfile: Sendable {
    public let userId: String
    public let clvTier: CLVTier
    public let preferences: [String: Double]       // category → affinity score [0,1]
    public let recentInteractions: [Interaction]
    public let notificationHistory: [NotificationRecord]
    public let demographics: Demographics

    public init(
        userId: String,
        clvTier: CLVTier,
        preferences: [String: Double] = [:],
        recentInteractions: [Interaction] = [],
        notificationHistory: [NotificationRecord] = [],
        demographics: Demographics = Demographics()
    ) {
        self.userId = userId
        self.clvTier = clvTier
        self.preferences = preferences
        self.recentInteractions = recentInteractions
        self.notificationHistory = notificationHistory
        self.demographics = demographics
    }
}

/// Customer Lifetime Value tier — drives the Budget Router decision.
/// High-value users receive full LLM composition; low-value users receive templates.
public enum CLVTier: String, Sendable, CaseIterable {
    case platinum   // Top 5%  — full LLM pipeline, max personalisation
    case gold       // Top 20% — LLM pipeline with moderate context
    case silver     // Top 50% — hybrid: LLM title, template body
    case bronze     // Bottom 50% — template path only
}

public struct Interaction: Sendable {
    public let itemId: String
    public let category: String
    public let action: InteractionType
    public let timestamp: Date
    public let durationSeconds: Double?

    public init(itemId: String, category: String, action: InteractionType,
                timestamp: Date = Date(), durationSeconds: Double? = nil) {
        self.itemId = itemId
        self.category = category
        self.action = action
        self.timestamp = timestamp
        self.durationSeconds = durationSeconds
    }
}

public enum InteractionType: String, Sendable {
    case view, click, purchase, share, save, dismiss, longPress
}

public struct NotificationRecord: Sendable {
    public let notificationId: String
    public let sentAt: Date
    public let opened: Bool
    public let converted: Bool
    public let domain: NotificationDomain

    public init(notificationId: String, sentAt: Date, opened: Bool,
                converted: Bool, domain: NotificationDomain) {
        self.notificationId = notificationId
        self.sentAt = sentAt
        self.opened = opened
        self.converted = converted
        self.domain = domain
    }
}

public struct Demographics: Sendable {
    public let timezone: TimeZone
    public let locale: Locale
    public let ageGroup: AgeGroup?

    public init(timezone: TimeZone = .current, locale: Locale = .current, ageGroup: AgeGroup? = nil) {
        self.timezone = timezone
        self.locale = locale
        self.ageGroup = ageGroup
    }
}

public enum AgeGroup: String, Sendable {
    case gen_z = "18-24"
    case millennial = "25-40"
    case gen_x = "41-56"
    case boomer = "57+"
}

// MARK: - Notification Request

/// Input to the NotificationPipeline. Encapsulates the WHO, WHEN, and WHAT.
/// The pipeline resolves the HOW — the composed message.
public struct NotificationRequest: Sendable {
    public let requestId: String
    public let user: UserProfile
    public let domain: NotificationDomain
    public let intent: NotificationIntent
    public let contentItem: ContentItem
    public let triggerContext: TriggerContext
    public let options: PipelineOptions

    public init(
        requestId: String = UUID().uuidString,
        user: UserProfile,
        domain: NotificationDomain,
        intent: NotificationIntent,
        contentItem: ContentItem,
        triggerContext: TriggerContext = TriggerContext(),
        options: PipelineOptions = PipelineOptions()
    ) {
        self.requestId = requestId
        self.user = user
        self.domain = domain
        self.intent = intent
        self.contentItem = contentItem
        self.triggerContext = triggerContext
        self.options = options
    }
}

public enum NotificationDomain: String, Sendable, CaseIterable {
    case socialMedia   = "Social Media"
    case foodDelivery  = "Food Delivery"
    case eCommerce     = "E-Commerce"
}

public enum NotificationIntent: String, Sendable {
    case reEngagement       = "Re-engagement"
    case newContent         = "New Content"
    case promotionalOffer   = "Promotional Offer"
    case abandonedCart      = "Abandoned Cart"
    case orderUpdate        = "Order Update"
    case socialActivity     = "Social Activity"
    case recommendation     = "Recommendation"
    case flashSale          = "Flash Sale"
}

public struct ContentItem: Sendable {
    public let itemId: String
    public let title: String
    public let category: String
    public let attributes: [String: String]   // e.g. ["price": "$12.99", "rating": "4.8"]
    public let imageURL: URL?

    public init(itemId: String, title: String, category: String,
                attributes: [String: String] = [:], imageURL: URL? = nil) {
        self.itemId = itemId
        self.title = title
        self.category = category
        self.attributes = attributes
        self.imageURL = imageURL
    }
}

public struct TriggerContext: Sendable {
    public let localHour: Int           // 0–23 in user's timezone
    public let dayOfWeek: Int           // 1=Sunday … 7=Saturday
    public let weatherCondition: String?
    public let recentAppOpen: Bool
    public let networkType: NetworkType

    public init(
        localHour: Int = Calendar.current.component(.hour, from: Date()),
        dayOfWeek: Int = Calendar.current.component(.weekday, from: Date()),
        weatherCondition: String? = nil,
        recentAppOpen: Bool = false,
        networkType: NetworkType = .wifi
    ) {
        self.localHour = localHour
        self.dayOfWeek = dayOfWeek
        self.weatherCondition = weatherCondition
        self.recentAppOpen = recentAppOpen
        self.networkType = networkType
    }
}

public enum NetworkType: String, Sendable {
    case wifi, cellular, offline
}

public struct PipelineOptions: Sendable {
    public let maxCandidates: Int
    public let maxTitleLength: Int
    public let maxBodyLength: Int
    public let enableGuardrails: Bool
    public let enableFrequencyCap: Bool
    public let enableSendTimeOptimization: Bool
    public let overrideCLVTier: CLVTier?

    public init(
        maxCandidates: Int = 5,
        maxTitleLength: Int = 50,
        maxBodyLength: Int = 120,
        enableGuardrails: Bool = true,
        enableFrequencyCap: Bool = true,
        enableSendTimeOptimization: Bool = true,
        overrideCLVTier: CLVTier? = nil
    ) {
        self.maxCandidates = maxCandidates
        self.maxTitleLength = maxTitleLength
        self.maxBodyLength = maxBodyLength
        self.enableGuardrails = enableGuardrails
        self.enableFrequencyCap = enableFrequencyCap
        self.enableSendTimeOptimization = enableSendTimeOptimization
        self.overrideCLVTier = overrideCLVTier
    }
}

// MARK: - Composed Notification (Output)

/// The final output of the NotificationPipeline.
/// Contains the composed message, pipeline trace, and delivery schedule.
public struct ComposedNotification: Sendable {
    public let notificationId: String
    public let title: String
    public let body: String
    public let scheduledAt: Date
    public let compositionPath: CompositionPath
    public let rewardScore: Double          // [0,1] from RewardRanker
    public let pipelineTrace: PipelineTrace
    public let metadata: [String: String]

    public init(
        notificationId: String = UUID().uuidString,
        title: String,
        body: String,
        scheduledAt: Date = Date(),
        compositionPath: CompositionPath,
        rewardScore: Double,
        pipelineTrace: PipelineTrace,
        metadata: [String: String] = [:]
    ) {
        self.notificationId = notificationId
        self.title = title
        self.body = body
        self.scheduledAt = scheduledAt
        self.compositionPath = compositionPath
        self.rewardScore = rewardScore
        self.pipelineTrace = pipelineTrace
        self.metadata = metadata
    }
}

/// Indicates which path through the pipeline was taken.
public enum CompositionPath: String, Sendable {
    case llmFull        = "LLM Full Pipeline"
    case llmHybrid      = "LLM Hybrid (Title only)"
    case template       = "Template Path"
    case blocked        = "Blocked by Guardrail"
    case frequencyCapped = "Frequency Capped"
}

/// Full audit trail of the pipeline execution.
public struct PipelineTrace: Sendable {
    public let budgetDecision: String
    public let retrievedContextKeys: [String]
    public let candidatesGenerated: Int
    public let guardrailsApplied: [String]
    public let candidatesFiltered: Int
    public let winningCandidateRank: Int
    public let sendTimeOptimized: Bool
    public let latencyMs: Double

    public init(
        budgetDecision: String,
        retrievedContextKeys: [String] = [],
        candidatesGenerated: Int = 0,
        guardrailsApplied: [String] = [],
        candidatesFiltered: Int = 0,
        winningCandidateRank: Int = 1,
        sendTimeOptimized: Bool = false,
        latencyMs: Double = 0
    ) {
        self.budgetDecision = budgetDecision
        self.retrievedContextKeys = retrievedContextKeys
        self.candidatesGenerated = candidatesGenerated
        self.guardrailsApplied = guardrailsApplied
        self.candidatesFiltered = candidatesFiltered
        self.winningCandidateRank = winningCandidateRank
        self.sendTimeOptimized = sendTimeOptimized
        self.latencyMs = latencyMs
    }
}

// MARK: - Candidate Message (internal)

/// An intermediate candidate message generated by the MessageComposer.
public struct CandidateMessage: Sendable {
    public let title: String
    public let body: String
    public var rewardScore: Double
    public let generationStrategy: String

    public init(title: String, body: String, rewardScore: Double = 0.0,
                generationStrategy: String = "llm") {
        self.title = title
        self.body = body
        self.rewardScore = rewardScore
        self.generationStrategy = generationStrategy
    }
}

// MARK: - Pipeline Result

public enum PipelineResult: Sendable {
    case success(ComposedNotification)
    case frequencyCapped(reason: String)
    case guardrailBlocked(reason: String)
    case error(Error)
}
