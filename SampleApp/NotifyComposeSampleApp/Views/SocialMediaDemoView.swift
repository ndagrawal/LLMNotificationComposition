// SocialMediaDemoView.swift
// NotifyCompose Sample App — Social Media Domain Demo

import SwiftUI

struct SocialMediaDemoView: View {
    @EnvironmentObject var appState: AppState
    @StateObject private var viewModel = SocialMediaDemoViewModel()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {

                    PaperContextBanner(
                        text: "Paper Example: PushGen-style re-engagement with entity-aware composition",
                        color: DemoSection.socialMedia.color
                    )

                    ScenarioCard(
                        title: "New Content Scenario",
                        subtitle: "Creator-follower engagement with topic affinity",
                        items: [
                            ("person.fill", "WHO", "Active follower, high affinity for tech content"),
                            ("clock.fill", "WHEN", "Evening, 2 days since last app open"),
                            ("play.rectangle.fill", "WHAT", "New post from followed creator, 12K views"),
                            ("sparkles", "HOW", "LLM references creator name + topic interest")
                        ],
                        color: DemoSection.socialMedia.color
                    )

                    // Intent picker
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Notification Intent")
                            .font(.headline)
                        Picker("Intent", selection: $viewModel.selectedIntent) {
                            Text("New Content").tag("new_content")
                            Text("Social Activity").tag("social_activity")
                            Text("Re-engagement").tag("re_engagement")
                        }
                        .pickerStyle(.segmented)
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(12)

                    ComposeButton(
                        isLoading: viewModel.isComposing,
                        color: DemoSection.socialMedia.color,
                        action: {
                            Task {
                                await viewModel.compose(
                                    using: appState.client,
                                    intent: viewModel.selectedIntent
                                )
                            }
                        }
                    )

                    if let notification = viewModel.result {
                        NotificationResultCard(
                            notification: notification,
                            color: DemoSection.socialMedia.color
                        )
                    }

                    if let error = viewModel.errorMessage {
                        ErrorCard(message: error)
                    }

                    Spacer(minLength: 40)
                }
                .padding()
            }
            .navigationTitle("Social Media")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

// MARK: - ViewModel

@MainActor
final class SocialMediaDemoViewModel: ObservableObject {
    @Published var isComposing = false
    @Published var result: ComposedNotification?
    @Published var errorMessage: String?
    @Published var selectedIntent: String = "new_content"

    func compose(using client: NotifyComposeClient, intent: String) async {
        isComposing = true
        errorMessage = nil
        result = nil

        client.track(.screenView, itemId: "feed_home", category: "social/feed")

        let request: NotificationRequest
        switch intent {
        case "social_activity":
            request = SocialMediaAdapter.socialActivity(
                userId: "demo_user_001",
                activityId: "activity_001",
                activityDescription: "liked your post",
                friendName: "Alex Chen",
                contentTitle: "My Swift tips article",
                category: "technology"
            )
        case "re_engagement":
            request = SocialMediaAdapter.reEngagement(
                userId: "demo_user_001",
                featuredContentId: "post_trending_001",
                featuredContentTitle: "WWDC 2026 Highlights",
                trendingTopic: "Swift 6 Concurrency",
                category: "technology"
            )
        default:
            request = SocialMediaAdapter.newContent(
                userId: "demo_user_001",
                postId: "post_456",
                postTitle: "10 Swift Concurrency Tips You Need to Know",
                creatorName: "SwiftDev",
                viewCount: "12K",
                category: "technology"
            )
        }

        do {
            result = try await client.compose(request: request)
        } catch {
            errorMessage = error.localizedDescription
        }

        isComposing = false
    }
}
