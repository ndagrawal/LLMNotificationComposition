// SharedComponents.swift
// NotifyCompose Sample App — Shared UI Components

import SwiftUI

// MARK: - Paper Context Banner

struct PaperContextBanner: View {
    let text: String
    let color: Color

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "doc.text.fill")
                .foregroundColor(color)
                .font(.caption)
            Text(text)
                .font(.caption)
                .foregroundColor(.secondary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(color.opacity(0.08))
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(color.opacity(0.25), lineWidth: 1)
        )
    }
}

// MARK: - Scenario Card

struct ScenarioCard: View {
    let title: String
    let subtitle: String
    let items: [(String, String, String)]  // (icon, label, value)
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.headline)
                Text(subtitle)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Divider()

            ForEach(Array(items.enumerated()), id: \.offset) { _, item in
                HStack(alignment: .top, spacing: 10) {
                    Image(systemName: item.0)
                        .foregroundColor(color)
                        .frame(width: 20)
                    VStack(alignment: .leading, spacing: 1) {
                        Text(item.1)
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(color)
                        Text(item.2)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

// MARK: - Context Control Panel

struct ContextControlPanel: View {
    @Binding var localHour: Double
    @Binding var weatherCondition: String

    let color: Color

    private let weatherOptions = ["sunny", "cloudy", "rainy", "snowy"]

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Contextual Signals")
                .font(.headline)

            // Hour slider
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Label("Local Hour", systemImage: "clock.fill")
                        .font(.subheadline)
                    Spacer()
                    Text(hourLabel)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .foregroundColor(color)
                }
                Slider(value: $localHour, in: 0...23, step: 1)
                    .accentColor(color)
            }

            // Weather picker
            VStack(alignment: .leading, spacing: 4) {
                Label("Weather", systemImage: "cloud.sun.fill")
                    .font(.subheadline)
                HStack(spacing: 8) {
                    ForEach(weatherOptions, id: \.self) { option in
                        Button(action: { weatherCondition = option }) {
                            Text(option.capitalized)
                                .font(.caption)
                                .fontWeight(weatherCondition == option ? .semibold : .regular)
                                .padding(.horizontal, 10)
                                .padding(.vertical, 6)
                                .background(weatherCondition == option ? color : Color(.systemGray5))
                                .foregroundColor(weatherCondition == option ? .white : .primary)
                                .cornerRadius(8)
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }

    private var hourLabel: String {
        let h = Int(localHour)
        let suffix = h < 12 ? "AM" : "PM"
        let display = h == 0 ? 12 : (h > 12 ? h - 12 : h)
        return "\(display):00 \(suffix)"
    }
}

// MARK: - Compose Button

struct ComposeButton: View {
    let isLoading: Bool
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 10) {
                if isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(0.9)
                    Text("Composing via Pipeline...")
                } else {
                    Image(systemName: "sparkles")
                    Text("Compose Notification")
                }
            }
            .font(.headline)
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(isLoading ? color.opacity(0.6) : color)
            .cornerRadius(12)
        }
        .disabled(isLoading)
    }
}

// MARK: - Notification Result Card

struct NotificationResultCard: View {
    let notification: ComposedNotification
    let color: Color

    @State private var showTrace = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {

            HStack {
                Label("Composed Notification", systemImage: "bell.badge.fill")
                    .font(.headline)
                Spacer()
                PathBadge(path: notification.compositionPath, color: color)
            }

            // Notification preview
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 8) {
                    RoundedRectangle(cornerRadius: 6)
                        .fill(color)
                        .frame(width: 32, height: 32)
                        .overlay(
                            Image(systemName: "bell.fill")
                                .foregroundColor(.white)
                                .font(.system(size: 14))
                        )
                    VStack(alignment: .leading, spacing: 2) {
                        Text(notification.title)
                            .font(.subheadline)
                            .fontWeight(.semibold)
                            .lineLimit(2)
                        Text(notification.body)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .lineLimit(3)
                    }
                }
            }
            .padding(12)
            .background(Color(.systemBackground))
            .cornerRadius(10)
            .shadow(color: .black.opacity(0.06), radius: 4, x: 0, y: 2)

            // Score bar
            HStack {
                Text("Reward Score")
                    .font(.caption)
                    .foregroundColor(.secondary)
                Spacer()
                Text(String(format: "%.2f", notification.rewardScore))
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(color)
            }
            ProgressView(value: notification.rewardScore)
                .accentColor(color)

            // Trace toggle
            Button(action: { showTrace.toggle() }) {
                HStack {
                    Text(showTrace ? "Hide Pipeline Trace" : "Show Pipeline Trace")
                        .font(.caption)
                        .foregroundColor(color)
                    Image(systemName: showTrace ? "chevron.up" : "chevron.down")
                        .font(.caption)
                        .foregroundColor(color)
                }
            }

            if showTrace {
                let trace = notification.pipelineTrace
                VStack(alignment: .leading, spacing: 6) {
                    TraceRow(label: "Budget Decision", value: trace.budgetDecision)
                    TraceRow(label: "Context Keys", value: trace.retrievedContextKeys.joined(separator: ", "))
                    TraceRow(label: "Candidates", value: "\(trace.candidatesGenerated) generated, \(trace.candidatesFiltered) filtered")
                    TraceRow(label: "Winner Rank", value: "#\(trace.winningCandidateRank)")
                    TraceRow(label: "STO Applied", value: trace.sendTimeOptimized ? "Yes" : "No")
                    TraceRow(label: "Latency", value: String(format: "%.0f ms", trace.latencyMs))
                }
                .padding(10)
                .background(Color(.systemGray5))
                .cornerRadius(8)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

// MARK: - Supporting Components

struct PathBadge: View {
    let path: CompositionPath
    let color: Color

    var body: some View {
        Text(path.rawValue)
            .font(.caption2)
            .fontWeight(.semibold)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(color.opacity(0.15))
            .foregroundColor(color)
            .cornerRadius(6)
    }
}

struct TraceRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack(alignment: .top) {
            Text(label + ":")
                .font(.caption2)
                .foregroundColor(.secondary)
                .frame(width: 100, alignment: .leading)
            Text(value.isEmpty ? "—" : value)
                .font(.caption2)
                .fontWeight(.medium)
        }
    }
}

struct ErrorCard: View {
    let message: String

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundColor(.red)
            VStack(alignment: .leading, spacing: 2) {
                Text("Pipeline Error")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                Text(message)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.red.opacity(0.08))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.red.opacity(0.25), lineWidth: 1)
        )
    }
}
