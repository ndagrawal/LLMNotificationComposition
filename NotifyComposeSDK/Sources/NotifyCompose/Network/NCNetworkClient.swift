// NCNetworkClient.swift
// NotifyCompose SDK — HTTP Network Layer
//
// Handles all communication with the NotifyCompose FastAPI server.
// Uses URLSession with async/await.

import Foundation

// MARK: - Network Client

final class NCNetworkClient: Sendable {

    private let baseURL: URL
    private let session: URLSession
    private let encoder: JSONEncoder
    private let decoder: JSONDecoder

    init(baseURL: URL, timeout: TimeInterval = 15.0) {
        self.baseURL = baseURL

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = timeout
        config.timeoutIntervalForResource = timeout * 2
        self.session = URLSession(configuration: config)

        self.encoder = JSONEncoder()
        self.encoder.dateEncodingStrategy = .iso8601

        self.decoder = JSONDecoder()
        self.decoder.dateDecodingStrategy = .iso8601
    }

    // MARK: - Signal Ingestion

    func sendSignals(batch: APISignalBatch) async throws {
        let url = baseURL.appendingPathComponent("/api/v1/signals")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(batch)

        let (_, response) = try await session.data(for: request)
        try validateResponse(response)
    }

    // MARK: - Notification Composition

    func compose(request: APIComposeRequest) async throws -> APIComposeResponse {
        let url = baseURL.appendingPathComponent("/api/v1/compose")
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try encoder.encode(request)

        let (data, response) = try await session.data(for: urlRequest)
        try validateResponse(response)
        return try decoder.decode(APIComposeResponse.self, from: data)
    }

    // MARK: - Feedback

    func sendFeedback(payload: APIFeedbackPayload) async throws {
        let url = baseURL.appendingPathComponent("/api/v1/feedback")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(payload)

        let (_, response) = try await session.data(for: request)
        try validateResponse(response)
    }

    // MARK: - Debug: User Profile

    func fetchProfile(userId: String) async throws -> APIUserProfile {
        let url = baseURL.appendingPathComponent("/api/v1/debug/profile/\(userId)")
        let (data, response) = try await session.data(from: url)
        try validateResponse(response)
        return try decoder.decode(APIUserProfile.self, from: data)
    }

    // MARK: - Helpers

    private func validateResponse(_ response: URLResponse) throws {
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NCNetworkError.invalidResponse
        }
        guard (200...299).contains(httpResponse.statusCode) else {
            throw NCNetworkError.serverError(statusCode: httpResponse.statusCode)
        }
    }
}

// MARK: - Network Errors

enum NCNetworkError: LocalizedError {
    case invalidResponse
    case serverError(statusCode: Int)
    case decodingError(String)

    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "Invalid server response"
        case .serverError(let code):
            return "Server error: HTTP \(code)"
        case .decodingError(let detail):
            return "Decoding error: \(detail)"
        }
    }
}

// MARK: - API Payload Types (wire format matching the FastAPI server)

struct APISignal: Encodable {
    let type: String
    let itemId: String?
    let category: String?
    let durationSeconds: Double?
    let notificationId: String?
    let metadata: [String: String]
    let timestamp: String

    enum CodingKeys: String, CodingKey {
        case type
        case itemId = "item_id"
        case category
        case durationSeconds = "duration_seconds"
        case notificationId = "notification_id"
        case metadata, timestamp
    }
}

struct APIDeviceContext: Encodable {
    let timezone: String
    let locale: String
    let networkType: String?
    let appVersion: String?

    enum CodingKeys: String, CodingKey {
        case timezone, locale
        case networkType = "network_type"
        case appVersion = "app_version"
    }
}

struct APISignalBatch: Encodable {
    let userId: String
    let signals: [APISignal]
    let deviceContext: APIDeviceContext

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case signals
        case deviceContext = "device_context"
    }
}

struct APIContentItem: Encodable {
    let itemId: String
    let title: String
    let category: String
    let attributes: [String: String]

    enum CodingKeys: String, CodingKey {
        case itemId = "item_id"
        case title, category, attributes
    }
}

struct APITriggerContext: Encodable {
    let localHour: Int
    let dayOfWeek: Int?
    let weatherCondition: String?
    let recentAppOpen: Bool

    enum CodingKeys: String, CodingKey {
        case localHour = "local_hour"
        case dayOfWeek = "day_of_week"
        case weatherCondition = "weather_condition"
        case recentAppOpen = "recent_app_open"
    }
}

struct APIComposeOptions: Encodable {
    let enableFrequencyCap: Bool
    let enableGuardrails: Bool
    let enableSendTimeOptimization: Bool
    let maxCandidates: Int
    let maxTitleLength: Int
    let maxBodyLength: Int
    let overrideCLVTier: String?

    enum CodingKeys: String, CodingKey {
        case enableFrequencyCap = "enable_frequency_cap"
        case enableGuardrails = "enable_guardrails"
        case enableSendTimeOptimization = "enable_send_time_optimization"
        case maxCandidates = "max_candidates"
        case maxTitleLength = "max_title_length"
        case maxBodyLength = "max_body_length"
        case overrideCLVTier = "override_clv_tier"
    }
}

struct APIComposeRequest: Encodable {
    let userId: String
    let domain: String
    let intent: String
    let contentItem: APIContentItem
    let triggerContext: APITriggerContext
    let options: APIComposeOptions

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case domain, intent
        case contentItem = "content_item"
        case triggerContext = "trigger_context"
        case options
    }

    init(from request: NotificationRequest, userId: String) {
        self.userId = userId
        self.domain = request.domain.rawValue.lowercased().replacingOccurrences(of: " ", with: "_")
        self.intent = request.intent.rawValue.lowercased().replacingOccurrences(of: " ", with: "_")
        self.contentItem = APIContentItem(
            itemId: request.contentItem.itemId,
            title: request.contentItem.title,
            category: request.contentItem.category,
            attributes: request.contentItem.attributes
        )
        self.triggerContext = APITriggerContext(
            localHour: request.triggerContext.localHour,
            dayOfWeek: request.triggerContext.dayOfWeek,
            weatherCondition: request.triggerContext.weatherCondition,
            recentAppOpen: request.triggerContext.recentAppOpen
        )
        self.options = APIComposeOptions(
            enableFrequencyCap: request.options.enableFrequencyCap,
            enableGuardrails: request.options.enableGuardrails,
            enableSendTimeOptimization: request.options.enableSendTimeOptimization,
            maxCandidates: request.options.maxCandidates,
            maxTitleLength: request.options.maxTitleLength,
            maxBodyLength: request.options.maxBodyLength,
            overrideCLVTier: request.options.overrideCLVTier?.rawValue
        )
    }
}

// MARK: - API Response Types

struct APIPipelineTrace: Decodable {
    let budgetDecision: String?
    let retrievedContextKeys: [String]?
    let candidatesGenerated: Int?
    let guardrailsApplied: [String]?
    let candidatesFiltered: Int?
    let winningCandidateRank: Int?
    let sendTimeOptimized: Bool?
    let latencyMs: Double?

    enum CodingKeys: String, CodingKey {
        case budgetDecision = "budget_decision"
        case retrievedContextKeys = "retrieved_context_keys"
        case candidatesGenerated = "candidates_generated"
        case guardrailsApplied = "guardrails_applied"
        case candidatesFiltered = "candidates_filtered"
        case winningCandidateRank = "winning_candidate_rank"
        case sendTimeOptimized = "send_time_optimized"
        case latencyMs = "latency_ms"
    }
}

struct APIComposeResponse: Decodable {
    let notificationId: String
    let title: String
    let body: String
    let scheduledAt: Date
    let compositionPath: String
    let rewardScore: Double
    let pipelineTrace: APIPipelineTrace?
    let metadata: [String: String]?

    enum CodingKeys: String, CodingKey {
        case notificationId = "notification_id"
        case title, body
        case scheduledAt = "scheduled_at"
        case compositionPath = "composition_path"
        case rewardScore = "reward_score"
        case pipelineTrace = "pipeline_trace"
        case metadata
    }

    func toComposedNotification() -> ComposedNotification {
        let path: CompositionPath
        switch compositionPath {
        case "LLM Full Pipeline": path = .llmFull
        case "LLM Hybrid": path = .llmHybrid
        case "Frequency Capped": path = .frequencyCapped
        default: path = .template
        }

        let trace = PipelineTrace(
            budgetDecision: pipelineTrace?.budgetDecision ?? "",
            retrievedContextKeys: pipelineTrace?.retrievedContextKeys ?? [],
            candidatesGenerated: pipelineTrace?.candidatesGenerated ?? 0,
            guardrailsApplied: pipelineTrace?.guardrailsApplied ?? [],
            candidatesFiltered: pipelineTrace?.candidatesFiltered ?? 0,
            winningCandidateRank: pipelineTrace?.winningCandidateRank ?? 1,
            sendTimeOptimized: pipelineTrace?.sendTimeOptimized ?? false,
            latencyMs: pipelineTrace?.latencyMs ?? 0
        )

        return ComposedNotification(
            notificationId: notificationId,
            title: title,
            body: body,
            scheduledAt: scheduledAt,
            compositionPath: path,
            rewardScore: rewardScore,
            pipelineTrace: trace,
            metadata: metadata ?? [:]
        )
    }
}

struct APIFeedbackPayload: Encodable {
    let notificationId: String
    let userId: String
    let outcome: FeedbackOutcome
    let openedAt: Date?
    let convertedAt: Date?

    enum CodingKeys: String, CodingKey {
        case notificationId = "notification_id"
        case userId = "user_id"
        case outcome
        case openedAt = "opened_at"
        case convertedAt = "converted_at"
    }
}

struct APIUserProfile: Decodable {
    let userId: String
    let clvTier: String
    let clvScore: Double
    let categoryAffinities: [String: Double]
    let notificationOpenRate: Double
    let totalPurchases: Int
    let preferredSendHours: [Int]

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case clvTier = "clv_tier"
        case clvScore = "clv_score"
        case categoryAffinities = "category_affinities"
        case notificationOpenRate = "notification_open_rate"
        case totalPurchases = "total_purchases"
        case preferredSendHours = "preferred_send_hours"
    }
}
