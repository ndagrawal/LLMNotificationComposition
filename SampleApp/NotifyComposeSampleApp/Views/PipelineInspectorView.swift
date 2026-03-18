// PipelineInspectorView.swift
// NotifyCompose Sample App — Pipeline Inspector
//
// Shows the full pipeline trace for the last composed notification,
// mapping each step to the paper's architecture (Figure 2).

import SwiftUI

struct PipelineInspectorView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    if let notification = appState.client.lastComposedNotification {
                        PipelineTraceView(notification: notification)
                    } else {
                        EmptyInspectorView()
                    }
                }
                .padding()
            }
            .navigationTitle("Pipeline Inspector")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

// MARK: - Pipeline Trace View

struct PipelineTraceView: View {
    let notification: ComposedNotification

    var body: some View {
        VStack(spacing: 16) {

            // Header
            VStack(alignment: .leading, spacing: 4) {
                Text("Last Composed Notification")
                    .font(.headline)
                Text(notification.notificationId)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(12)

            // Composed message
            VStack(alignment: .leading, spacing: 8) {
                Label("Composed Message", systemImage: "bell.fill")
                    .font(.headline)
                Text(notification.title)
                    .font(.title3)
                    .fontWeight(.semibold)
                Text(notification.body)
                    .font(.body)
                    .foregroundColor(.secondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(12)

            // Pipeline steps
            Text("Pipeline Execution Trace")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)

            let trace = notification.pipelineTrace

            PipelineStepRow(
                step: "1",
                title: "Budget Router",
                value: trace.budgetDecision,
                icon: "arrow.triangle.branch",
                color: .orange,
                paperRef: "§4.1 Budget-Aware Router"
            )

            PipelineStepRow(
                step: "2",
                title: "Context Retrieval (RAG)",
                value: trace.retrievedContextKeys.joined(separator: ", "),
                icon: "doc.text.magnifyingglass",
                color: .blue,
                paperRef: "§4.2 RAG-Based Retrieval"
            )

            PipelineStepRow(
                step: "3",
                title: "Message Generation",
                value: "\(trace.candidatesGenerated) candidates generated",
                icon: "sparkles",
                color: .purple,
                paperRef: "§4.3 PEFT/LoRA Composer"
            )

            PipelineStepRow(
                step: "4",
                title: "Guardrail Filter",
                value: trace.guardrailsApplied.isEmpty
                    ? "All candidates passed"
                    : "\(trace.candidatesFiltered) filtered: \(trace.guardrailsApplied.joined(separator: ", "))",
                icon: "shield.fill",
                color: .red,
                paperRef: "§4.5 Factuality & Policy Guards"
            )

            PipelineStepRow(
                step: "5",
                title: "Reward Ranker",
                value: String(format: "Winner: Rank #%d, Score: %.2f", trace.winningCandidateRank, notification.rewardScore),
                icon: "star.fill",
                color: .yellow,
                paperRef: "§4.4 Pairwise Reward Model"
            )

            PipelineStepRow(
                step: "6",
                title: "Send-Time Optimization",
                value: trace.sendTimeOptimized
                    ? "Optimized via Thompson Sampling bandit"
                    : "Immediate delivery",
                icon: "clock.arrow.circlepath",
                color: .green,
                paperRef: "§4.6 STO Contextual Bandit"
            )

            // Metrics summary
            HStack(spacing: 12) {
                MetricPill(label: "Path", value: notification.compositionPath.rawValue, color: .blue)
                MetricPill(label: "Score", value: String(format: "%.2f", notification.rewardScore), color: .green)
                MetricPill(label: "Latency", value: String(format: "%.0fms", trace.latencyMs), color: .orange)
            }
        }
    }
}

// MARK: - Supporting Views

struct PipelineStepRow: View {
    let step: String
    let title: String
    let value: String
    let icon: String
    let color: Color
    let paperRef: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            ZStack {
                Circle()
                    .fill(color.opacity(0.15))
                    .frame(width: 36, height: 36)
                Image(systemName: icon)
                    .foregroundColor(color)
                    .font(.system(size: 14))
            }

            VStack(alignment: .leading, spacing: 2) {
                HStack {
                    Text("Step \(step): \(title)")
                        .font(.subheadline)
                        .fontWeight(.semibold)
                    Spacer()
                    Text(paperRef)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                }
                Text(value.isEmpty ? "—" : value)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
}

struct MetricPill: View {
    let label: String
    let value: String
    let color: Color

    var body: some View {
        VStack(spacing: 2) {
            Text(label)
                .font(.caption2)
                .foregroundColor(.secondary)
            Text(value)
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(color)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
        .background(color.opacity(0.1))
        .cornerRadius(8)
    }
}

struct EmptyInspectorView: View {
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "magnifyingglass.circle")
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            Text("No Notification Composed Yet")
                .font(.title3)
                .fontWeight(.semibold)
            Text("Compose a notification in any of the domain tabs to see the full pipeline trace here.")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding(40)
    }
}
